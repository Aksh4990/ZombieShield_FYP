from pathlib import Path

from app.services.discovery import GitDiscovery, OpenAPIDiscovery, RuntimeLogDiscovery

FIXTURES = Path(__file__).parent / "fixtures"
CONTEXT = {"organization": "test-org", "service_name": "test-service", "host": "test.example", "version": "v1"}


def test_openapi_json_and_yaml_discovery():
    discovery = OpenAPIDiscovery()
    json_results = discovery.discover((FIXTURES / "openapi.json").read_text(), **CONTEXT)
    yaml_results = discovery.discover((FIXTURES / "openapi.yaml").read_text(), **CONTEXT)

    assert {(item.http_method, item.endpoint_path) for item in json_results} == {
        ("GET", "/users"), ("POST", "/users"), ("GET", "/users/{id}"), ("DELETE", "/users/{id}"), ("PATCH", "/orders")
    }
    assert all(item.source == "openapi" and item.is_documented for item in yaml_results)


def test_git_discovery_extracts_fastapi_and_flask_routes():
    results = GitDiscovery().discover(FIXTURES / "git_source", **CONTEXT)

    assert {(item.http_method, item.endpoint_path) for item in results} == {
        ("GET", "/users"), ("POST", "/users"), ("PUT", "/users/{id}"), ("GET", "/orders/{id}"), ("POST", "/orders/{id}")
    }
    assert all(item.source == "git" and item.is_documented for item in results)


def test_runtime_log_discovery_normalizes_dynamic_paths_and_skips_malformed_lines():
    results = RuntimeLogDiscovery().discover((FIXTURES / "runtime.log").read_text(), **CONTEXT)

    assert {(item.http_method, item.endpoint_path) for item in results} == {
        ("GET", "/api/users"), ("POST", "/api/orders"), ("GET", "/api/users/{id}")
    }
    assert results[0].last_seen is not None


def test_discovery_endpoints_persist_and_deduplicate_within_run(client):
    openapi_response = client.post("/discovery/openapi", json={**CONTEXT, "document": (FIXTURES / "openapi.json").read_text()})
    assert openapi_response.status_code == 200
    assert openapi_response.json()["discovered_count"] == 5
    assert openapi_response.json()["added_count"] == 5

    git_response = client.post("/discovery/git", json={**CONTEXT, "service_name": "git-service", "repository_path": "git_source"})
    assert git_response.status_code == 200
    assert git_response.json()["added_count"] == 5

    log_response = client.post("/discovery/runtime-log", json={**CONTEXT, "service_name": "log-service", "log_content": (FIXTURES / "runtime.log").read_text()})
    assert log_response.status_code == 200
    assert log_response.json()["discovered_count"] == 3

    inventory = client.get("/apis")
    assert inventory.status_code == 200
    assert len(inventory.json()) == 13


def test_discovery_rejects_invalid_openapi_and_unsafe_git_path(client):
    invalid = client.post("/discovery/openapi", json={**CONTEXT, "document": "not valid: ["})
    assert invalid.status_code == 422

    unsafe = client.post("/discovery/git", json={**CONTEXT, "repository_path": "../outside"})
    assert unsafe.status_code == 400
