import uuid
from datetime import timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.api import API
from app.schemas.api import APICreate
from app.services.normalization import canonical_key, normalize_path


def create_api(db: Session, payload: APICreate) -> API:
    data = payload.model_dump(exclude_none=True)
    data["endpoint_path"] = normalize_path(data["endpoint_path"])
    data["sources"] = list(dict.fromkeys(data.get("sources") or [data["source"]]))
    data["canonical_key"] = canonical_key(data["organization"], data["host"], data["http_method"], data["endpoint_path"], data["version"])
    api = API(**data)
    db.add(api)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise
    db.refresh(api)
    return api


def list_apis(db: Session) -> list[API]:
    return list(db.scalars(select(API).order_by(API.created_at.desc())))


def get_api(db: Session, api_id: uuid.UUID) -> API | None:
    return db.get(API, api_id)


def get_api_by_identity(
    db: Session,
    *,
    organization: str,
    service_name: str,
    host: str,
    http_method: str,
    endpoint_path: str,
    version: str,
) -> API | None:
    statement = select(API).where(
        API.organization == organization,
        API.service_name == service_name,
        API.host == host,
        API.http_method == http_method,
        API.endpoint_path == endpoint_path,
        API.version == version,
    )
    return db.scalar(statement)


def observe_api(db: Session, payload: APICreate) -> tuple[API, bool, bool]:
    """Create once or update a canonical record without erasing prior metadata."""
    normalized_path = normalize_path(payload.endpoint_path)
    key = canonical_key(payload.organization, payload.host, payload.http_method, normalized_path, payload.version)
    existing = db.scalar(select(API).where(API.canonical_key == key))
    if existing is None:
        record = create_api(db, payload.model_copy(update={"endpoint_path": normalized_path, "sources": [payload.source]}))
        return record, True, False
    prior_sources = list(existing.sources or [existing.source])
    sources = list(dict.fromkeys([*prior_sources, payload.source]))
    changed = sources != prior_sources
    existing.sources = sources
    if payload.last_seen:
        prior_seen = existing.last_seen if existing.last_seen.tzinfo else existing.last_seen.replace(tzinfo=timezone.utc)
        incoming_seen = payload.last_seen if payload.last_seen.tzinfo else payload.last_seen.replace(tzinfo=timezone.utc)
        if incoming_seen > prior_seen:
            existing.last_seen = payload.last_seen
    db.commit()
    db.refresh(existing)
    return existing, False, True
