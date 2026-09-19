import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class DecisionRead(BaseModel):
    id: uuid.UUID
    api_id: uuid.UUID
    action: str
    status: str
    reason: str
    decided_at: datetime
    model_config = ConfigDict(from_attributes=True)

class DecisionRunResponse(BaseModel):
    total_evaluated: int
    monitor: int
    remediate: int
    escalate: int
    decisions: list[DecisionRead]
