def test_safe_simulation_records_evidence_without_network_activity(client):
    created = client.post("/apis", json={
        "organization": "simulation-org", "service_name": "runtime", "http_method": "GET",
        "endpoint_path": "/debug", "host": "api.example.test", "version": "v1",
        "source": "runtime_log", "sources": ["runtime_log"],
    })
    api_id = created.json()["id"]
    client.post("/classification/run")

    response = client.post(f"/apis/{api_id}/simulation/run", json={"scenarios": ["ZOMBIE_EXPOSURE_REVIEW", "AUTHENTICATION_EVIDENCE_REVIEW"]})
    assert response.status_code == 200
    body = response.json()
    assert body["observed_risks"] == 1
    assert "no HTTP requests" in body["safety_notice"]
    assert {result["status"] for result in body["results"]} == {"OBSERVED_RISK", "INSUFFICIENT_EVIDENCE"}

    stored = client.get(f"/apis/{api_id}")
    assert stored.json()["simulation_finding_count"] == 1
    assert len(client.get(f"/apis/{api_id}/simulation-results").json()) == 2
