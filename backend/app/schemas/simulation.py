import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

SimulationScenario = Literal["ZOMBIE_EXPOSURE_REVIEW", "AUTHENTICATION_EVIDENCE_REVIEW", "RATE_LIMIT_EVIDENCE_REVIEW", "THREAT_FINDING_REVIEW"]


class SimulationRunRequest(BaseModel):
    api_ids: list[uuid.UUID] | None = None
    scenarios: list[SimulationScenario] = Field(default_factory=lambda: ["ZOMBIE_EXPOSURE_REVIEW", "AUTHENTICATION_EVIDENCE_REVIEW", "RATE_LIMIT_EVIDENCE_REVIEW", "THREAT_FINDING_REVIEW"])


class SimulationResultRead(BaseModel):
    id: uuid.UUID
    api_id: uuid.UUID
    scenario: SimulationScenario
    status: str
    severity: str
    finding: str
    evidence_summary: str
    simulated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SimulationRunResponse(BaseModel):
    total_apis_evaluated: int
    results_created_or_updated: int
    observed_risks: int
    safety_notice: str
    results: list[SimulationResultRead]
