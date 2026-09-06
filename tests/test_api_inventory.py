def api_payload() -> dict[str, object]:
    return {
        "organization": "example-org",
        "service_name": "accounts",
        "http_method": "get",
        "endpoint_path": "/v1/accounts",
        "host": "api.example.test",
        "version": "v1",
        "source": "manual",
        "owner": "platform@example.test",
        "is_registered": True,
        "is_documented": False,
    }


def test_create_list_and_get_api_inventory_record(client):
    created = client.post("/apis", json=api_payload())

    assert created.status_code == 201
    record = created.json()
    assert record["http_method"] == "GET"
    assert record["lifecycle_state"] == "ACTIVE"
    assert record["id"]

    listed = client.get("/apis")
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()] == [record["id"]]

    fetched = client.get(f"/apis/{record['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["endpoint_path"] == "/v1/accounts"


def test_duplicate_api_inventory_record_is_rejected(client):
    assert client.post("/apis", json=api_payload()).status_code == 201

    response = client.post("/apis", json=api_payload())
    assert response.status_code == 409


def test_unknown_api_inventory_record_returns_not_found(client):
    response = client.get("/apis/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
