import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.api import utc_now


class SimulationResult(Base):
    """Safe local evaluation result; no request is ever sent to a target API."""

    __tablename__ = "simulation_results"
    __table_args__ = (
        UniqueConstraint("api_id", "scenario", name="uq_simulation_result_scenario"),
        Index("ix_simulation_results_api_id", "api_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    api_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("apis.id", ondelete="CASCADE"), nullable=False)
    scenario: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    finding: Mapped[str] = mapped_column(String(2000), nullable=False)
    evidence_summary: Mapped[str] = mapped_column(String(2000), nullable=False)
    simulated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
