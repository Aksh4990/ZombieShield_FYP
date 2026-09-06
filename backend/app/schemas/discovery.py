from pydantic import BaseModel, Field

from app.schemas.api import APIRead


class DiscoveryRequestBase(BaseModel):
    organization: str = Field(min_length=1, max_length=255)
    service_name: str | None = Field(default=None, min_length=1, max_length=255)
    host: str = Field(min_length=1, max_length=255)
    version: str = Field(default="unversioned", min_length=1, max_length=100)


class OpenAPIDiscoveryRequest(DiscoveryRequestBase):
    document: str = Field(min_length=1)


class GitDiscoveryRequest(DiscoveryRequestBase):
    repository_path: str = Field(min_length=1, max_length=1024)


class RuntimeLogDiscoveryRequest(DiscoveryRequestBase):
    log_content: str = Field(min_length=1)


class DiscoveryResponse(BaseModel):
    source: str
    discovered_count: int
    added_count: int
    records: list[APIRead]
