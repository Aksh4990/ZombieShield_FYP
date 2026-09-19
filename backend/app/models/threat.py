import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, JSON, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.api import utc_now


class ThreatAdvisory(Base):
    """Source-attributed advisory supplied to ZombieShield for correlation."""

    __tablename__ = "threat_advisories"
    __table_args__ = (Index("ix_threat_advisories_component", "component_name"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    advisory_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    component_name: Mapped[str] = mapped_column(String(255), nullable=False)
    affected_versions: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    summary: Mapped[str] = mapped_column(String(2000), nullable=False)
    source_name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


class ThreatFinding(Base):
    """A persisted exact-version correlation between an API and an advisory."""

    __tablename__ = "threat_findings"
    __table_args__ = (
        UniqueConstraint("api_id", "threat_advisory_id", "component_version", name="uq_threat_finding_match"),
        Index("ix_threat_findings_api_id", "api_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    api_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("apis.id", ondelete="CASCADE"), nullable=False)
    threat_advisory_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("threat_advisories.id", ondelete="CASCADE"), nullable=False)
    advisory_id: Mapped[str] = mapped_column(String(100), nullable=False)
    component_name: Mapped[str] = mapped_column(String(255), nullable=False)
    component_version: Mapped[str] = mapped_column(String(255), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    summary: Mapped[str] = mapped_column(String(2000), nullable=False)
    source_name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    correlated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
