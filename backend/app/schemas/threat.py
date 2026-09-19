import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


ThreatSeverity = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]


class ThreatAdvisoryCreate(BaseModel):
    """An advisory must identify its source; ZombieShield does not invent it."""

    advisory_id: str = Field(min_length=1, max_length=100)
    component_name: str = Field(min_length=1, max_length=255)
    affected_versions: list[str] = Field(min_length=1)
    severity: ThreatSeverity
    summary: str = Field(min_length=1, max_length=2000)
    source_name: str = Field(min_length=1, max_length=255)
    source_url: HttpUrl
    published_at: datetime | None = None


class ThreatAdvisoryRead(ThreatAdvisoryCreate):
    id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ThreatFindingRead(BaseModel):
    id: uuid.UUID
    api_id: uuid.UUID
    advisory_id: str
    component_name: str
    component_version: str
    severity: ThreatSeverity
    summary: str
    source_name: str
    source_url: str
    correlated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ThreatCorrelationRunResponse(BaseModel):
    total_apis_evaluated: int
    findings_created: int
    findings: list[ThreatFindingRead]
    correlation_method: str
