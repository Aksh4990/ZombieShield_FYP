def test_decision_engine_recommends_monitor_and_remediation(client):
    low = client.post("/apis", json={"organization":"decision","service_name":"low","http_method":"GET","endpoint_path":"/ok","host":"api.test","version":"v1","source":"manual","is_registered":True,"is_documented":True}).json()
    high = client.post("/apis", json={"organization":"decision","service_name":"high","http_method":"GET","endpoint_path":"/debug","host":"api2.test","version":"v1","source":"runtime_log","is_registered":False,"is_documented":False}).json()
    client.post(f"/apis/{high['id']}/risk-assessment")
    result = client.post("/decisions/run")
    assert result.status_code == 200
    assert result.json()["total_evaluated"] == 2
    assert {item["action"] for item in result.json()["decisions"]} >= {"MONITOR", "REMEDIATE"}
    assert all(item["status"] == "RECOMMENDED" for item in result.json()["decisions"])
