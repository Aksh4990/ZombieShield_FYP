from datetime import datetime

from pydantic import BaseModel

from app.schemas.api import APIRead


class RiskAssessmentResult(BaseModel):
    api: APIRead
    assessed_at: datetime


class RiskAssessmentRunResponse(BaseModel):
    """Results from a bulk risk assessment using synthetic-model output."""

    total_assessed: int
    low: int
    medium: int
    high: int
    critical: int
    model_training_data: str
    results: list[RiskAssessmentResult]
