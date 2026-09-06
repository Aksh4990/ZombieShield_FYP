import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.api import LifecycleState


class APIBase(BaseModel):
    organization: str = Field(min_length=1, max_length=255)
    service_name: str = Field(min_length=1, max_length=255)
    http_method: str = Field(min_length=1, max_length=10)
    endpoint_path: str = Field(min_length=1, max_length=2048, pattern=r"^/")
    host: str = Field(min_length=1, max_length=255)
    version: str = Field(default="unversioned", min_length=1, max_length=100)
    source: str = Field(min_length=1, max_length=100)
    sources: list[str] = Field(default_factory=list)
    owner: str | None = Field(default=None, max_length=255)
    is_registered: bool = False
    is_documented: bool = False
    is_deprecated: bool = False
    is_removed_from_supported_surface: bool = False
    first_seen: datetime | None = None
    last_seen: datetime | None = None
    lifecycle_state: LifecycleState = LifecycleState.ACTIVE

    @field_validator("http_method")
    @classmethod
    def normalize_method(cls, value: str) -> str:
        return value.upper()


class APICreate(APIBase):
    pass


class APIRead(APIBase):
    id: uuid.UUID
    first_seen: datetime
    last_seen: datetime
    created_at: datetime
    updated_at: datetime
    classification_reason: str | None = None
    classified_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
