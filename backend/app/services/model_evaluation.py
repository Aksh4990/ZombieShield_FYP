"""Controlled comparison of risk-model candidates on synthetic scenarios only."""

from time import perf_counter

from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, precision_recall_fscore_support
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from app.services.risk_ml import FEATURE_COLUMNS, _synthetic_training_data

DATASET_NOTICE = (
    "Metrics are measured on a held-out split of reproducible synthetic risk scenarios. "
    "They compare model behavior in this controlled demonstration and do not represent production security accuracy."
)


def evaluate_models() -> dict:
    rows, labels = _synthetic_training_data()
    x_train, x_test, y_train, y_test = train_test_split(
        rows, labels, test_size=0.20, random_state=42, stratify=labels
    )
    candidates = {
        "Logistic Regression (Baseline)": make_pipeline(
            StandardScaler(), LogisticRegression(max_iter=1000, random_state=42, solver="liblinear")
        ),
        "Random Forest": RandomForestClassifier(n_estimators=100, random_state=42),
        "Gradient Boosting": GradientBoostingClassifier(random_state=42, n_estimators=60, max_depth=2),
    }
    metrics = []
    for name, model in candidates.items():
        started = perf_counter()
        model.fit(x_train, y_train)
        training_time_ms = round((perf_counter() - started) * 1000, 3)
        prediction = model.predict(x_test)
        precision, recall, f1, _ = precision_recall_fscore_support(
            y_test, prediction, average="macro", zero_division=0
        )
        metrics.append({
            "name": name,
            "accuracy": round(float(accuracy_score(y_test, prediction)), 4),
            "precision_macro": round(float(precision), 4),
            "recall_macro": round(float(recall), 4),
            "f1_macro": round(float(f1), 4),
            "training_time_ms": training_time_ms,
            "selected_for_live_scoring": name == "Gradient Boosting",
            "confusion_matrix": confusion_matrix(y_test, prediction, labels=[0, 1, 2, 3]).astype(int).tolist(),
        })
    labels_by_tier = {0: "LOW", 1: "MEDIUM", 2: "HIGH", 3: "CRITICAL"}
    samples = []
    seen_labels: set[int] = set()
    for row, label in zip(rows, labels):
        if label not in seen_labels:
            samples.append({
                "risk_label": labels_by_tier[label],
                "features": {name: float(value) for name, value in zip(FEATURE_COLUMNS, row)},
            })
            seen_labels.add(label)
        if len(seen_labels) == len(labels_by_tier):
            break
    return {
        "dataset_type": "reproducible synthetic risk scenarios",
        "dataset_notice": DATASET_NOTICE,
        "total_scenarios": len(rows),
        "train_scenarios": len(x_train),
        "test_scenarios": len(x_test),
        "random_state": 42,
        "metrics": metrics,
        "sample_scenarios": samples,
    }
