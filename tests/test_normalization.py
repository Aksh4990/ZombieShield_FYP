from datetime import datetime, timedelta, timezone


def _openapi(path: str, version: str = "v1") -> str:
    return '{"openapi":"3.0.3","info":{"title":"API","version":"' + version + '"},"paths":{"' + path + '":{"get":{}}}}'


def test_cross_source_reconciliation_normalizes_trailing_slash_and_tracks_sources(client):
    base = {"organization": "canonical", "host": "api.example", "service_name": "service"}
    first = client.post("/discovery/openapi", json={**base, "document": _openapi("/users/")})
    second = client.post("/discovery/runtime-log", json={**base, "version": "v1", "log_content": "2026-09-06T18:31:00Z GET /users 200"})
    assert first.json()["added_count"] == 1
    assert second.json()["added_count"] == 0
    records = client.get("/apis").json()
    assert len(records) == 1
    assert records[0]["endpoint_path"] == "/users"
    assert set(records[0]["sources"]) == {"openapi", "runtime_log"}


def test_versions_and_distinct_routes_remain_separate(client):
    base = {"organization": "canonical", "host": "api.example", "service_name": "service"}
    client.post("/discovery/openapi", json={**base, "document": _openapi("/users", "v1")})
    client.post("/discovery/openapi", json={**base, "document": _openapi("/users", "v2")})
    client.post("/discovery/openapi", json={**base, "document": _openapi("/orders", "v1")})
    assert len(client.get("/apis").json()) == 3
