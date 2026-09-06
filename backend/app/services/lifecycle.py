from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from app.models.api import API, LifecycleState

@dataclass(frozen=True)
class Classification:
    state: LifecycleState
    reason: str

class LifecycleClassifier:
    def __init__(self, activity_window_days: int = 30): self.window = timedelta(days=activity_window_days)
    def classify(self, api: API, now: datetime) -> Classification:
        sources = set(api.sources or [api.source])
        recent = api.last_seen.replace(tzinfo=timezone.utc) >= now - self.window if api.last_seen.tzinfo is None else api.last_seen >= now - self.window
        supported = "openapi" in sources or "git" in sources
        runtime = "runtime_log" in sources
        if api.is_deprecated: return Classification(LifecycleState.DEPRECATED, "Explicitly marked deprecated in inventory evidence.")
        if api.is_removed_from_supported_surface and not recent: return Classification(LifecycleState.DECOMMISSIONED, "Explicit removal from supported surface and no recent runtime activity.")
        if runtime and not supported and recent: return Classification(LifecycleState.ZOMBIE, "Recent runtime activity exists without corresponding documented or source evidence.")
        if supported and runtime and recent: return Classification(LifecycleState.ACTIVE, "Supported by documentation/source with recent runtime activity.")
        return Classification(LifecycleState.ACTIVE, "No explicit deprecation or removal evidence; retained as active to avoid a false-positive lifecycle change.")
