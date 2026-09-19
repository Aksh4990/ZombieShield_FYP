"""Controlled, evidence-only threat simulation. It performs no network I/O."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.api import API, LifecycleState
from app.models.simulation import SimulationResult

SAFETY_NOTICE = "Simulations evaluate stored inventory evidence only; no HTTP requests, exploitation, scanning, or traffic generation occurs."


def _evaluate(api: API, scenario: str) -> tuple[str, str, str, str]:
    if scenario == "ZOMBIE_EXPOSURE_REVIEW":
        if api.lifecycle_state == LifecycleState.ZOMBIE:
            return "OBSERVED_RISK", "HIGH", "Zombie exposure scenario observed.", "Lifecycle classifier recorded ZOMBIE from inventory/runtime evidence."
        return "NO_ELEVATED_RISK", "LOW", "No zombie lifecycle exposure observed.", f"Current lifecycle state is {api.lifecycle_state.value}."
    if scenario == "THREAT_FINDING_REVIEW":
        count = api.threat_finding_count or 0
        if count:
            return "OBSERVED_RISK", "HIGH", "Threat-intelligence exposure scenario observed.", f"{count} source-attributed threat finding(s) are persisted for this API."
        return "NO_ELEVATED_RISK", "LOW", "No correlated threat-intelligence finding observed.", "No source-attributed finding is currently stored."
    if scenario == "AUTHENTICATION_EVIDENCE_REVIEW":
        return "INSUFFICIENT_EVIDENCE", "LOW", "Authentication exposure cannot be simulated from current evidence.", "Authentication requirement is explicitly unknown; no request was sent."
    return "INSUFFICIENT_EVIDENCE", "LOW", "Rate-limit exposure cannot be simulated from current evidence.", "Rate-limiting evidence is explicitly unknown; no request was sent."


def run_for_api(db: Session, api: API, scenarios: list[str]) -> list[SimulationResult]:
    now = datetime.now(timezone.utc)
    results = []
    for scenario in dict.fromkeys(scenarios):
        status, severity, finding, evidence = _evaluate(api, scenario)
        result = db.scalar(select(SimulationResult).where(SimulationResult.api_id == api.id, SimulationResult.scenario == scenario))
        if result is None:
            result = SimulationResult(api_id=api.id, scenario=scenario, status=status, severity=severity, finding=finding, evidence_summary=evidence, simulated_at=now)
            db.add(result)
        else:
            result.status, result.severity, result.finding, result.evidence_summary, result.simulated_at = status, severity, finding, evidence, now
        results.append(result)
    db.flush()
    api.simulation_finding_count = len(list(db.scalars(select(SimulationResult).where(SimulationResult.api_id == api.id, SimulationResult.status == "OBSERVED_RISK"))))
    return results


def list_results(db: Session, api_id: uuid.UUID | None = None) -> list[SimulationResult]:
    statement = select(SimulationResult).order_by(SimulationResult.simulated_at.desc())
    if api_id is not None:
        statement = statement.where(SimulationResult.api_id == api_id)
    return list(db.scalars(statement))
