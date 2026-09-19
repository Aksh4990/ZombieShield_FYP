"""Evidence-aware risk feature extraction for inventory records."""

from dataclasses import dataclass
from datetime import datetime, timezone

from app.models.api import API, LifecycleState


UNKNOWN_SECURITY_EVIDENCE = {
    "authentication_requirement": "unknown",
    "tls_enabled": "unknown",
    "rate_limiting_enabled": "unknown",
    "pii_exposure": "unknown",
}


@dataclass(frozen=True)
class RiskFeatureSet:
    values: dict[str, int | float | str | dict[str, str]]


class RiskFeatureExtractor:
    """Extract only signals present in the current inventory model.

    The platform currently has no reliable authentication, TLS, rate-limit, or
    PII telemetry. Those controls are deliberately emitted as ``unknown`` and
    are not treated as evidence that a control is missing.
    """

    def extract(self, api: API, now: datetime) -> RiskFeatureSet:
        sources = set(api.sources or [api.source])
        first_seen = api.first_seen
        if first_seen.tzinfo is None:
            first_seen = first_seen.replace(tzinfo=timezone.utc)
        age_days = max(0, (now - first_seen).days)
        runtime_only = "runtime_log" in sources and not ({"openapi", "git"} & sources)
        return RiskFeatureSet(
            values={
                "registration_confirmed": int(bool(api.is_registered)),
                "documentation_confirmed": int(bool(api.is_documented)),
                "deprecated": int(bool(api.is_deprecated)),
                "removed_from_supported_surface": int(bool(api.is_removed_from_supported_surface)),
                "zombie_lifecycle": int(api.lifecycle_state == LifecycleState.ZOMBIE),
                "runtime_only_evidence": int(runtime_only),
                "source_count": len(sources),
                "endpoint_age_days": age_days,
                "known_threat_finding_count": int(api.threat_finding_count or 0),
                "simulation_finding_count": int(api.simulation_finding_count or 0),
                "security_control_evidence": UNKNOWN_SECURITY_EVIDENCE.copy(),
            }
        )
