def test_recommendations_explain_inventory_remediation_without_assuming_missing_controls(client):
    created = client.post("/apis", json={
        "organization": "remediation-org",
        "service_name": "legacy-service",
        "http_method": "GET",
        "endpoint_path": "/debug",
        "host": "api.example.test",
        "version": "v1",
        "source": "runtime_log",
        "sources": ["runtime_log"],
        "is_registered": False,
        "is_documented": False,
    })
    assert created.status_code == 201
    api_id = created.json()["id"]

    simulation = client.post(f"/apis/{api_id}/simulation/run", json={
        "scenarios": ["AUTHENTICATION_EVIDENCE_REVIEW", "RATE_LIMIT_EVIDENCE_REVIEW"],
    })
    assert simulation.status_code == 200

    response = client.get(f"/apis/{api_id}/recommendations")
    assert response.status_code == 200
    payload = response.json()
    recommendations = {item["key"]: item for item in payload["recommendations"]}

    assert "register-api-owner" in recommendations
    assert "document-api-contract" in recommendations
    assert "reconcile-runtime-only-route" in recommendations
    assert "verify-authentication-evidence" in recommendations
    assert "verify-rate-limit-evidence" in recommendations
    assert recommendations["verify-authentication-evidence"]["action"].startswith("Confirm whether")
    assert "unknown" in payload["limitations"][0]


def test_recommendations_include_source_attributed_threat_remediation(client):
    created = client.post("/apis", json={
        "organization": "remediation-org",
        "service_name": "component-service",
        "http_method": "GET",
        "endpoint_path": "/health",
        "host": "api.example.test",
        "version": "v1",
        "source": "manual",
        "is_registered": True,
        "is_documented": True,
        "technology_components": [{"name": "demo-lib", "version": "1.0.0", "evidence_source": "manual"}],
    })
    api_id = created.json()["id"]
    advisory = client.post("/threat-intelligence/advisories", json={
        "advisory_id": "DEMO-2026-1",
        "component_name": "demo-lib",
        "affected_versions": ["1.0.0"],
        "severity": "HIGH",
        "summary": "Demonstration advisory.",
        "source_name": "ZombieShield test source",
        "source_url": "https://example.test/advisories/DEMO-2026-1",
    })
    assert advisory.status_code == 201
    correlated = client.post(f"/apis/{api_id}/threat-intelligence/correlate")
    assert correlated.status_code == 200

    response = client.get(f"/apis/{api_id}/recommendations")
    recommendations = response.json()["recommendations"]
    threat_recommendation = next(item for item in recommendations if item["key"].startswith("threat-"))
    assert threat_recommendation["title"] == "Remediate DEMO-2026-1 in demo-lib"
    assert threat_recommendation["reference_url"] == "https://example.test/advisories/DEMO-2026-1"


def test_recommendations_return_not_found_for_unknown_api(client):
    response = client.get("/apis/00000000-0000-0000-0000-000000000000/recommendations")
    assert response.status_code == 404
