from app.services.model_evaluation import evaluate_models


def test_model_evaluation_compares_baseline_and_ensemble_models():
    result = evaluate_models()

    assert result["dataset_type"] == "reproducible synthetic risk scenarios"
    assert result["train_scenarios"] + result["test_scenarios"] == result["total_scenarios"]
    assert [metric["name"] for metric in result["metrics"]] == [
        "Logistic Regression (Baseline)", "Random Forest", "Gradient Boosting"
    ]
    assert {sample["risk_label"] for sample in result["sample_scenarios"]} == {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
    assert any(metric["selected_for_live_scoring"] for metric in result["metrics"])
    assert all(0 <= metric["f1_macro"] <= 1 for metric in result["metrics"])


def test_model_evaluation_endpoint(client):
    response = client.get("/risk/models/evaluate")

    assert response.status_code == 200
    payload = response.json()
    assert payload["random_state"] == 42
    assert len(payload["metrics"]) == 3
    assert "do not represent production security accuracy" in payload["dataset_notice"]
