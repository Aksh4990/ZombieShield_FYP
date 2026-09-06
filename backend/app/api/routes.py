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
from app.models.api import LifecycleState
from app.services import api_inventory
from app.core.config import get_settings
from app.services.discovery import DiscoveryError, GitDiscovery, OpenAPIDiscovery, RuntimeLogDiscovery, persist_discoveries
from app.services.lifecycle import LifecycleClassifier

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
