import uuid
from pathlib import Path

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.api import APICreate, APIRead
from app.schemas.discovery import DiscoveryResponse, GitDiscoveryRequest, OpenAPIDiscoveryRequest, RuntimeLogDiscoveryRequest
from app.schemas.classification import ClassificationResult, ClassificationRunResponse
from app.schemas.risk import RiskAssessmentResult, RiskAssessmentRunResponse
from app.schemas.threat import ThreatAdvisoryCreate, ThreatAdvisoryRead, ThreatCorrelationRunResponse, ThreatFindingRead
from app.schemas.simulation import SimulationResultRead, SimulationRunRequest, SimulationRunResponse
from app.models.api import LifecycleState, RiskLevel
from app.services import api_inventory
from app.core.config import get_settings
from app.services.discovery import DiscoveryError, GitDiscovery, OpenAPIDiscovery, RuntimeLogDiscovery, persist_discoveries
from app.services.lifecycle import LifecycleClassifier
from app.services.risk_assessment import RiskAssessmentService, persist_assessment
from app.services.risk_ml import TRAINING_DATA_DESCRIPTION
from app.services import threat_intelligence
from app.services import simulation
from app.services import decision
from app.schemas.decision import DecisionRead, DecisionRunResponse

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy"}


@router.post("/apis", response_model=APIRead, status_code=status.HTTP_201_CREATED)
def create_api(payload: APICreate, db: Session = Depends(get_db)) -> APIRead:
    try:
        return api_inventory.create_api(db, payload)
    except IntegrityError as exc:
        raise HTTPException(status_code=409, detail="API inventory record already exists") from exc


@router.get("/apis", response_model=list[APIRead])
def list_apis(lifecycle_state: LifecycleState | None = Query(default=None), db: Session = Depends(get_db)) -> list[APIRead]:
    records = api_inventory.list_apis(db)
    return [record for record in records if lifecycle_state is None or record.lifecycle_state == lifecycle_state]


@router.get("/apis/{api_id}", response_model=APIRead)
def get_api(api_id: uuid.UUID, db: Session = Depends(get_db)) -> APIRead:
    api = api_inventory.get_api(db, api_id)
    if api is None:
        raise HTTPException(status_code=404, detail="API inventory record not found")
    return api


def discovery_response(source: str, results, db: Session) -> DiscoveryResponse:
    records, added_count = persist_discoveries(db, results)
    return DiscoveryResponse(source=source, discovered_count=len(results), added_count=added_count, records=records)


@router.post("/discovery/openapi", response_model=DiscoveryResponse)
def discover_openapi(payload: OpenAPIDiscoveryRequest, db: Session = Depends(get_db)) -> DiscoveryResponse:
    try:
        results = OpenAPIDiscovery().discover(payload.document, organization=payload.organization, service_name=payload.service_name, host=payload.host, version=payload.version)
    except DiscoveryError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return discovery_response("openapi", results, db)


@router.post("/discovery/git", response_model=DiscoveryResponse)
def discover_git(payload: GitDiscoveryRequest, db: Session = Depends(get_db)) -> DiscoveryResponse:
    root = Path(get_settings().discovery_git_root).resolve()
    repository = (root / payload.repository_path).resolve()
    if not repository.is_relative_to(root):
        raise HTTPException(status_code=400, detail="Repository path must stay within the configured discovery root")
    try:
        results = GitDiscovery().discover(repository, organization=payload.organization, service_name=payload.service_name, host=payload.host, version=payload.version)
    except DiscoveryError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return discovery_response("git", results, db)


@router.post("/discovery/runtime-log", response_model=DiscoveryResponse)
def discover_runtime_log(payload: RuntimeLogDiscoveryRequest, db: Session = Depends(get_db)) -> DiscoveryResponse:
    try:
        results = RuntimeLogDiscovery().discover(payload.log_content, organization=payload.organization, service_name=payload.service_name, host=payload.host, version=payload.version)
    except DiscoveryError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return discovery_response("runtime_log", results, db)


@router.post("/classification/run", response_model=ClassificationRunResponse)
def run_classification(db: Session = Depends(get_db)) -> ClassificationRunResponse:
    now = datetime.now(timezone.utc)
    classifier = LifecycleClassifier(get_settings().lifecycle_activity_window_days)
    results = []
    counts = {state: 0 for state in LifecycleState}
    for api in api_inventory.list_apis(db):
        outcome = classifier.classify(api, now)
        api.lifecycle_state, api.classification_reason, api.classified_at = outcome.state, outcome.reason, now
        counts[outcome.state] += 1
        results.append(ClassificationResult(api=api, lifecycle_state=outcome.state, classification_reason=outcome.reason, classified_at=now))
    db.commit()
    return ClassificationRunResponse(total_evaluated=len(results), active=counts[LifecycleState.ACTIVE], deprecated=counts[LifecycleState.DEPRECATED], zombie=counts[LifecycleState.ZOMBIE], decommissioned=counts[LifecycleState.DECOMMISSIONED], results=results)


@router.post("/apis/{api_id}/risk-assessment", response_model=RiskAssessmentResult)
def assess_api_risk(api_id: uuid.UUID, db: Session = Depends(get_db)) -> RiskAssessmentResult:
    api = api_inventory.get_api(db, api_id)
    if api is None:
        raise HTTPException(status_code=404, detail="API inventory record not found")
    assessment = RiskAssessmentService().assess(api)
    persist_assessment(api, assessment)
    db.commit()
    db.refresh(api)
    return RiskAssessmentResult(api=api, assessed_at=assessment.assessed_at)


@router.post("/risk/assessments/run", response_model=RiskAssessmentRunResponse)
def run_risk_assessments(db: Session = Depends(get_db)) -> RiskAssessmentRunResponse:
    service = RiskAssessmentService()
    results: list[RiskAssessmentResult] = []
    counts = {level: 0 for level in RiskLevel}
    for api in api_inventory.list_apis(db):
        assessment = service.assess(api)
        persist_assessment(api, assessment)
        counts[assessment.level] += 1
        results.append(RiskAssessmentResult(api=api, assessed_at=assessment.assessed_at))
    db.commit()
    return RiskAssessmentRunResponse(
        total_assessed=len(results),
        low=counts[RiskLevel.LOW],
        medium=counts[RiskLevel.MEDIUM],
        high=counts[RiskLevel.HIGH],
        critical=counts[RiskLevel.CRITICAL],
        model_training_data=TRAINING_DATA_DESCRIPTION,
        results=results,
    )


@router.post("/threat-intelligence/advisories", response_model=ThreatAdvisoryRead, status_code=status.HTTP_201_CREATED)
def create_threat_advisory(payload: ThreatAdvisoryCreate, db: Session = Depends(get_db)) -> ThreatAdvisoryRead:
    try:
        return threat_intelligence.create_advisory(db, payload)
    except IntegrityError as exc:
        raise HTTPException(status_code=409, detail="Threat advisory already exists") from exc


@router.get("/threat-intelligence/advisories", response_model=list[ThreatAdvisoryRead])
def list_threat_advisories(db: Session = Depends(get_db)) -> list[ThreatAdvisoryRead]:
    return threat_intelligence.list_advisories(db)


@router.get("/threat-intelligence/findings", response_model=list[ThreatFindingRead])
def list_threat_findings(db: Session = Depends(get_db)) -> list[ThreatFindingRead]:
    return threat_intelligence.list_findings(db)


@router.get("/apis/{api_id}/threat-findings", response_model=list[ThreatFindingRead])
def list_api_threat_findings(api_id: uuid.UUID, db: Session = Depends(get_db)) -> list[ThreatFindingRead]:
    if api_inventory.get_api(db, api_id) is None:
        raise HTTPException(status_code=404, detail="API inventory record not found")
    return threat_intelligence.list_findings(db, api_id)


@router.post("/apis/{api_id}/threat-intelligence/correlate", response_model=ThreatCorrelationRunResponse)
def correlate_api_threat_intelligence(api_id: uuid.UUID, db: Session = Depends(get_db)) -> ThreatCorrelationRunResponse:
    api = api_inventory.get_api(db, api_id)
    if api is None:
        raise HTTPException(status_code=404, detail="API inventory record not found")
    findings, created = threat_intelligence.correlate_api(db, api)
    db.commit()
    return ThreatCorrelationRunResponse(total_apis_evaluated=1, findings_created=created, findings=findings, correlation_method=threat_intelligence.CORRELATION_METHOD)


@router.post("/threat-intelligence/correlate/run", response_model=ThreatCorrelationRunResponse)
def run_threat_intelligence_correlation(db: Session = Depends(get_db)) -> ThreatCorrelationRunResponse:
    advisories = threat_intelligence.list_advisories(db)
    findings = []
    created = 0
    apis = api_inventory.list_apis(db)
    for api in apis:
        api_findings, api_created = threat_intelligence.correlate_api(db, api, advisories)
        findings.extend(api_findings)
        created += api_created
    db.commit()
    return ThreatCorrelationRunResponse(total_apis_evaluated=len(apis), findings_created=created, findings=findings, correlation_method=threat_intelligence.CORRELATION_METHOD)


@router.get("/simulation/results", response_model=list[SimulationResultRead])
def list_simulation_results(db: Session = Depends(get_db)) -> list[SimulationResultRead]:
    return simulation.list_results(db)


@router.get("/apis/{api_id}/simulation-results", response_model=list[SimulationResultRead])
def list_api_simulation_results(api_id: uuid.UUID, db: Session = Depends(get_db)) -> list[SimulationResultRead]:
    if api_inventory.get_api(db, api_id) is None:
        raise HTTPException(status_code=404, detail="API inventory record not found")
    return simulation.list_results(db, api_id)


@router.post("/apis/{api_id}/simulation/run", response_model=SimulationRunResponse)
def run_api_simulation(api_id: uuid.UUID, payload: SimulationRunRequest, db: Session = Depends(get_db)) -> SimulationRunResponse:
    api = api_inventory.get_api(db, api_id)
    if api is None:
        raise HTTPException(status_code=404, detail="API inventory record not found")
    results = simulation.run_for_api(db, api, payload.scenarios)
    db.commit()
    observed = sum(result.status == "OBSERVED_RISK" for result in results)
    return SimulationRunResponse(total_apis_evaluated=1, results_created_or_updated=len(results), observed_risks=observed, safety_notice=simulation.SAFETY_NOTICE, results=results)


@router.post("/simulation/run", response_model=SimulationRunResponse)
def run_simulations(payload: SimulationRunRequest, db: Session = Depends(get_db)) -> SimulationRunResponse:
    apis = api_inventory.list_apis(db)
    if payload.api_ids is not None:
        requested = set(payload.api_ids)
        apis = [api for api in apis if api.id in requested]
    results = []
    for api in apis:
        results.extend(simulation.run_for_api(db, api, payload.scenarios))
    db.commit()
    observed = sum(result.status == "OBSERVED_RISK" for result in results)
    return SimulationRunResponse(total_apis_evaluated=len(apis), results_created_or_updated=len(results), observed_risks=observed, safety_notice=simulation.SAFETY_NOTICE, results=results)

@router.post("/decisions/run", response_model=DecisionRunResponse)
def run_decisions(db: Session = Depends(get_db)) -> DecisionRunResponse:
    decisions = [decision.persist(db, api) for api in api_inventory.list_apis(db)]
    db.commit()
    counts = {"MONITOR": 0, "REMEDIATE": 0, "ESCALATE": 0}
    for item in decisions: counts[item.action] += 1
    return DecisionRunResponse(total_evaluated=len(decisions), monitor=counts["MONITOR"], remediate=counts["REMEDIATE"], escalate=counts["ESCALATE"], decisions=decisions)
