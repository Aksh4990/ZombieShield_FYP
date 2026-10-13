from pydantic import BaseModel, Field


class ModelMetric(BaseModel):
    name: str
    accuracy: float = Field(ge=0, le=1)
    precision_macro: float = Field(ge=0, le=1)
    recall_macro: float = Field(ge=0, le=1)
    f1_macro: float = Field(ge=0, le=1)
    training_time_ms: float = Field(ge=0)
    selected_for_live_scoring: bool = False
    confusion_matrix: list[list[int]]


class SyntheticScenarioSample(BaseModel):
    risk_label: str
    features: dict[str, float]


class ModelEvaluationResponse(BaseModel):
    dataset_type: str
    dataset_notice: str
    total_scenarios: int
    train_scenarios: int
    test_scenarios: int
    random_state: int
    metrics: list[ModelMetric]
    sample_scenarios: list[SyntheticScenarioSample]
