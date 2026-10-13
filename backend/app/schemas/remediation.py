import uuid
from typing import Literal

from pydantic import BaseModel, Field


RecommendationPriority = Literal["IMMEDIATE", "HIGH", "MEDIUM", "LOW"]


class RemediationRecommendation(BaseModel):
    """An evidence-led action recommendation; it does not execute a change."""

    key: str
    priority: RecommendationPriority
    title: str
    action: str
    rationale: str
    evidence: list[str] = Field(default_factory=list)
    validation: str
    reference_url: str | None = None


class RemediationResponse(BaseModel):
    api_id: uuid.UUID
    recommendations: list[RemediationRecommendation]
    limitations: list[str]
