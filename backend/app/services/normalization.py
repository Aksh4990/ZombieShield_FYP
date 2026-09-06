import hashlib


def normalize_path(path: str) -> str:
    """Remove only a non-root trailing slash; preserve all other route semantics."""
    return path.rstrip("/") or "/"


def canonical_key(organization: str, host: str, method: str, path: str, version: str) -> str:
    identity = "\x1f".join((organization.strip().lower(), host.strip().lower(), method.upper(), normalize_path(path), version.strip() or "unversioned"))
    return hashlib.sha256(identity.encode()).hexdigest()
