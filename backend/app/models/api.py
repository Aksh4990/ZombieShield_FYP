import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, Float, Index, Integer, JSON, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class LifecycleState(str, enum.Enum):
    ACTIVE = "ACTIVE"
    DEPRECATED = "DEPRECATED"
    ZOMBIE = "ZOMBIE"
    DECOMMISSIONED = "DECOMMISSIONED"


class RiskLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class API(Base):
    __tablename__ = "apis"
    __table_args__ = (
        UniqueConstraint(
            "organization", "service_name", "host", "http_method", "endpoint_path", "version",
            name="uq_api_inventory_identity",
        ),
        Index("ix_apis_organization_service", "organization", "service_name"),
        Index("ix_apis_lifecycle_state", "lifecycle_state"),
        Index("ix_apis_last_seen", "last_seen"),
        Index("ix_apis_canonical_key", "canonical_key", unique=True),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization: Mapped[str] = mapped_column(String(255), nullable=False)
    service_name: Mapped[str] = mapped_column(String(255), nullable=False)
    http_method: Mapped[str] = mapped_column(String(10), nullable=False)
    endpoint_path: Mapped[str] = mapped_column(String(2048), nullable=False)
    host: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str] = mapped_column(String(100), nullable=False, default="unversioned")
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    sources: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    canonical_key: Mapped[str | None] = mapped_column(String(64), nullable=True)
    owner: Mapped[str | None] = mapped_column(String(255))
    is_registered: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_documented: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_deprecated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_removed_from_supported_surface: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    lifecycle_state: Mapped[LifecycleState] = mapped_column(
        Enum(LifecycleState, name="lifecycle_state"), nullable=False, default=LifecycleState.ACTIVE
    )
    classification_reason: Mapped[str | None] = mapped_column(String(1000))
    classified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    risk_score: Mapped[float | None] = mapped_column(Float)
    risk_level: Mapped[str | None] = mapped_column(String(20))
    risk_features: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    risk_findings: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    risk_explanation: Mapped[str | None] = mapped_column(String(2000))
    risk_assessed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    technology_components: Mapped[list[dict]] = mapped_column(JSON, nullable=False, default=list)
    threat_finding_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    simulation_finding_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )
