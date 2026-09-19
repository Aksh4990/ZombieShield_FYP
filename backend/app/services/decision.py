"""Explainable, recommendation-only decision engine; no external action occurs."""
from sqlalchemy.orm import Session
from app.models.api import API
from app.models.decision import Decision

def decide(api: API) -> tuple[str, str]:
    score = api.risk_score or 0
    if score >= 75:
        return "ESCALATE", f"Risk score {score:.2f} is CRITICAL; escalate for urgent security review. No blocking action was executed."
    if score >= 50 or (api.threat_finding_count or 0) or (api.simulation_finding_count or 0):
        return "REMEDIATE", f"Risk score {score:.2f}, threat findings {api.threat_finding_count or 0}, simulation findings {api.simulation_finding_count or 0}; recommend remediation and continued monitoring."
    return "MONITOR", f"Risk score {score:.2f} has no elevated threat or simulation evidence; continue monitoring."

def persist(db: Session, api: API) -> Decision:
    action, reason = decide(api)
    decision = Decision(api_id=api.id, action=action, status="RECOMMENDED", reason=reason)
    db.add(decision)
    return decision
