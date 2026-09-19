"""Local, source-attributed exact-version threat intelligence correlation."""

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.api import API
from app.models.threat import ThreatAdvisory, ThreatFinding
from app.schemas.threat import ThreatAdvisoryCreate

CORRELATION_METHOD = (
    "Exact component-name and version match against source-attributed advisories. "
    "Version ranges and unverified external claims are intentionally not inferred."
)


def create_advisory(db: Session, payload: ThreatAdvisoryCreate) -> ThreatAdvisory:
    data = payload.model_dump()
    data["source_url"] = str(data["source_url"])
    advisory = ThreatAdvisory(**data)
    db.add(advisory)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise
    db.refresh(advisory)
    return advisory


def list_advisories(db: Session) -> list[ThreatAdvisory]:
    return list(db.scalars(select(ThreatAdvisory).order_by(ThreatAdvisory.created_at.desc())))


def list_findings(db: Session, api_id: uuid.UUID | None = None) -> list[ThreatFinding]:
    statement = select(ThreatFinding).order_by(ThreatFinding.correlated_at.desc())
    if api_id is not None:
        statement = statement.where(ThreatFinding.api_id == api_id)
    return list(db.scalars(statement))


def correlate_api(db: Session, api: API, advisories: list[ThreatAdvisory] | None = None) -> tuple[list[ThreatFinding], int]:
    advisories = advisories if advisories is not None else list_advisories(db)
    by_component: dict[str, list[ThreatAdvisory]] = {}
    for advisory in advisories:
        by_component.setdefault(advisory.component_name.strip().lower(), []).append(advisory)

    created: list[ThreatFinding] = []
    for component in api.technology_components or []:
        name = str(component.get("name", "")).strip()
        version = str(component.get("version", "")).strip()
        if not name or not version:
            continue
        for advisory in by_component.get(name.lower(), []):
            if version not in set(advisory.affected_versions or []):
                continue
            existing = db.scalar(select(ThreatFinding).where(
                ThreatFinding.api_id == api.id,
                ThreatFinding.threat_advisory_id == advisory.id,
                ThreatFinding.component_version == version,
            ))
            if existing is not None:
                continue
            finding = ThreatFinding(
                api_id=api.id,
                threat_advisory_id=advisory.id,
                advisory_id=advisory.advisory_id,
                component_name=name,
                component_version=version,
                severity=advisory.severity,
                summary=advisory.summary,
                source_name=advisory.source_name,
                source_url=advisory.source_url,
            )
            db.add(finding)
            created.append(finding)

    db.flush()
    api.threat_finding_count = len(list_findings(db, api.id))
    return created, len(created)
