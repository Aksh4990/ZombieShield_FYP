def api_payload() -> dict[str, object]:
    return {
        "organization": "threat-org",
        "service_name": "catalog",
        "http_method": "GET",
        "endpoint_path": "/v1/catalog",
        "host": "api.example.test",
        "version": "v1",
        "source": "manual",
        "is_registered": True,
        "is_documented": True,
        "technology_components": [
            {"name": "example-library", "version": "1.2.3", "evidence_source": "deployment-manifest"}
        ],
    }


def advisory_payload() -> dict[str, object]:
    return {
        "advisory_id": "TEST-ADVISORY-001",
        "component_name": "example-library",
        "affected_versions": ["1.2.3"],
        "severity": "HIGH",
        "summary": "Controlled test advisory used only for correlation verification.",
        "source_name": "controlled-test-feed",
        "source_url": "https://security.example.test/advisories/TEST-ADVISORY-001",
    }


def test_source_attributed_advisory_correlates_exact_component_version(client):
    created_api = client.post("/apis", json=api_payload())
    assert created_api.status_code == 201
    api_id = created_api.json()["id"]

    advisory = client.post("/threat-intelligence/advisories", json=advisory_payload())
    assert advisory.status_code == 201
    assert advisory.json()["source_name"] == "controlled-test-feed"

    correlation = client.post("/threat-intelligence/correlate/run")
    assert correlation.status_code == 200
    assert correlation.json()["total_apis_evaluated"] == 1
    assert correlation.json()["findings_created"] == 1
    assert "Exact component-name and version match" in correlation.json()["correlation_method"]

    findings = client.get(f"/apis/{api_id}/threat-findings")
    assert findings.status_code == 200
    assert findings.json()[0]["advisory_id"] == "TEST-ADVISORY-001"
    assert findings.json()[0]["component_version"] == "1.2.3"

    stored_api = client.get(f"/apis/{api_id}")
    assert stored_api.json()["threat_finding_count"] == 1

    risk = client.post(f"/apis/{api_id}/risk-assessment")
    assert risk.status_code == 200
    assert risk.json()["api"]["risk_features"]["known_threat_finding_count"] == 1
    assert "threat intelligence finding" in " ".join(risk.json()["api"]["risk_findings"])


def test_unmatched_version_does_not_create_a_threat_finding(client):
    payload = api_payload()
    payload["technology_components"] = [{"name": "example-library", "version": "9.9.9", "evidence_source": "deployment-manifest"}]
    assert client.post("/apis", json=payload).status_code == 201
    assert client.post("/threat-intelligence/advisories", json=advisory_payload()).status_code == 201

    correlation = client.post("/threat-intelligence/correlate/run")
    assert correlation.status_code == 200
    assert correlation.json()["findings_created"] == 0
    assert client.get("/threat-intelligence/findings").json() == []


def test_duplicate_advisory_and_unknown_api_findings_are_rejected(client):
    assert client.post("/threat-intelligence/advisories", json=advisory_payload()).status_code == 201
    assert client.post("/threat-intelligence/advisories", json=advisory_payload()).status_code == 409
    assert client.get("/apis/00000000-0000-0000-0000-000000000000/threat-findings").status_code == 404
