from datetime import datetime
from pydantic import BaseModel
from app.models.api import LifecycleState
from app.schemas.api import APIRead

class ClassificationResult(BaseModel):
    api: APIRead
    lifecycle_state: LifecycleState
    classification_reason: str
    classified_at: datetime

class ClassificationRunResponse(BaseModel):
    total_evaluated: int
    active: int
    deprecated: int
    zombie: int
    decommissioned: int
    results: list[ClassificationResult]
