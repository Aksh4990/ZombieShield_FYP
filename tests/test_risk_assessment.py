from datetime import datetime, timedelta, timezone

from app.models.api import API, LifecycleState
from app.services.risk_assessment import RiskAssessmentService
from app.services.risk_features import RiskFeatureExtractor
from app.services.risk_ml import TRAINING_DATA_DESCRIPTION


def api_payload() -> dict[str, object]:
    return {
        "organization": "risk-org",
        "service_name": "payments",
        "http_method": "GET",
        "endpoint_path": "/v1/payments",
        "host": "api.example.test",
        "version": "v1",
        "source": "manual",
        "is_registered": True,
        "is_documented": True,
    }


def test_feature_extraction_marks_unavailable_controls_unknown():
    api = API(**api_payload(), first_seen=datetime.now(timezone.utc))

    features = RiskFeatureExtractor().extract(api, datetime.now(timezone.utc)).values

    assert features["security_control_evidence"] == {
        "authentication_requirement": "unknown",
        "tls_enabled": "unknown",
        "rate_limiting_enabled": "unknown",
        "pii_exposure": "unknown",
    }


def test_zombie_runtime_only_api_scores_higher_than_supported_api():
    now = datetime.now(timezone.utc)
    supported = API(**api_payload(), sources=["openapi", "runtime_log"], first_seen=now - timedelta(days=5))
    exposed = API(
        **{**api_payload(), "endpoint_path": "/debug", "is_registered": False, "is_documented": False, "source": "runtime_log"},
        sources=["runtime_log"],
        lifecycle_state=LifecycleState.ZOMBIE,
        first_seen=now - timedelta(days=400),
    )

    service = RiskAssessmentService()
    supported_assessment = service.assess(supported, now)
    exposed_assessment = service.assess(exposed, now)

    assert exposed_assessment.score > supported_assessment.score
    assert "unknown; no missing control has been inferred" in exposed_assessment.findings[-1]
    assert exposed_assessment.level.value in {"HIGH", "CRITICAL"}


def test_risk_endpoints_persist_individual_and_bulk_results(client):
    created = client.post("/apis", json=api_payload())
    assert created.status_code == 201
    api_id = created.json()["id"]

    individual = client.post(f"/apis/{api_id}/risk-assessment")
    assert individual.status_code == 200
    individual_record = individual.json()["api"]
    assert 0 <= individual_record["risk_score"] <= 100
    assert individual_record["risk_level"] in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
    assert individual_record["risk_assessed_at"] is not None
    assert individual_record["risk_features"]["security_control_evidence"]["tls_enabled"] == "unknown"

    bulk = client.post("/risk/assessments/run")
    assert bulk.status_code == 200
    assert bulk.json()["total_assessed"] == 1
    assert bulk.json()["model_training_data"] == TRAINING_DATA_DESCRIPTION

    persisted = client.get(f"/apis/{api_id}")
    assert persisted.status_code == 200
    assert persisted.json()["risk_score"] is not None


def test_unknown_api_risk_assessment_returns_not_found(client):
    response = client.post("/apis/00000000-0000-0000-0000-000000000000/risk-assessment")
    assert response.status_code == 404
