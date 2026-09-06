import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import yaml
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.api import LifecycleState
from app.schemas.api import APICreate
from app.services import api_inventory
from app.services.normalization import normalize_path

HTTP_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}
OPENAPI_METHODS = {method.lower() for method in HTTP_METHODS}
LOG_PATTERN = re.compile(
    r"^\s*(?P<timestamp>\S+)?\s*(?P<method>GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+"
    r"(?P<path>/\S+)(?:\s+(?P<status>\d{3}))?\s*$"
)
FASTAPI_PATTERN = re.compile(
    r"@\s*\w+\.(?P<method>get|post|put|patch|delete|head|options)\s*\(\s*['\"](?P<path>/[^'\"]*)['\"]",
    re.IGNORECASE,
)
FLASK_PATTERN = re.compile(
    r"@\s*\w+\.route\s*\(\s*['\"](?P<path>/[^'\"]*)['\"](?P<arguments>[^)]*)\)",
    re.IGNORECASE,
)
FLASK_METHODS_PATTERN = re.compile(r"methods\s*=\s*\[\s*(?P<methods>[^\]]+)\]", re.IGNORECASE)
QUOTED_METHOD_PATTERN = re.compile(r"['\"](?P<method>GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)['\"]", re.IGNORECASE)


class DiscoveryError(ValueError):
    pass


@dataclass(frozen=True)
class DiscoveryResult:
    organization: str
    service_name: str
    host: str
    version: str
    http_method: str
    endpoint_path: str
    source: str
    is_documented: bool
    first_seen: datetime | None = None
    last_seen: datetime | None = None

    @property
    def identity(self) -> tuple[str, str, str, str, str, str]:
        return (
            self.organization,
            self.service_name,
            self.host,
            self.version,
            self.http_method,
            self.endpoint_path,
        )


class OpenAPIDiscovery:
    def discover(self, document: str, *, organization: str, service_name: str | None, host: str, version: str) -> list[DiscoveryResult]:
        parsed = self._parse_document(document)
        if not isinstance(parsed, dict) or not str(parsed.get("openapi", "")).startswith("3."):
            raise DiscoveryError("Document must be an OpenAPI 3.x JSON or YAML specification")
        paths = parsed.get("paths")
        if not isinstance(paths, dict):
            raise DiscoveryError("OpenAPI document must contain a paths object")

        info = parsed.get("info") if isinstance(parsed.get("info"), dict) else {}
        resolved_service = service_name or str(info.get("title") or "openapi-service")
        resolved_version = version if version != "unversioned" else str(info.get("version") or version)
        resolved_host = self._server_host(parsed) or host
        results: list[DiscoveryResult] = []
        for path, operations in paths.items():
            if not isinstance(path, str) or not path.startswith("/") or not isinstance(operations, dict):
                continue
            for method in operations:
                if method.lower() in OPENAPI_METHODS:
                    results.append(DiscoveryResult(
                        organization=organization, service_name=resolved_service, host=resolved_host,
                        version=resolved_version, http_method=method.upper(), endpoint_path=path,
                        source="openapi", is_documented=True,
                    ))
        return unique_results(results)

    @staticmethod
    def _parse_document(document: str) -> dict:
        try:
            parsed = json.loads(document)
        except json.JSONDecodeError:
            try:
                parsed = yaml.safe_load(document)
            except yaml.YAMLError as exc:
                raise DiscoveryError("OpenAPI document is not valid JSON or YAML") from exc
        if not isinstance(parsed, dict):
            raise DiscoveryError("OpenAPI document must be an object")
        return parsed

    @staticmethod
    def _server_host(document: dict) -> str | None:
        servers = document.get("servers")
        if not isinstance(servers, list) or not servers or not isinstance(servers[0], dict):
            return None
        url = servers[0].get("url")
        if not isinstance(url, str):
            return None
        return urlparse(url).netloc or None


class GitDiscovery:
    supported_suffixes = {".py"}

    def discover(self, repository: Path, *, organization: str, service_name: str | None, host: str, version: str) -> list[DiscoveryResult]:
        if not repository.is_dir():
            raise DiscoveryError("Repository path does not exist or is not a directory")
        resolved_service = service_name or repository.name
        documented = self._has_documentation(repository)
        results: list[DiscoveryResult] = []
        for path in repository.rglob("*"):
            if path.suffix.lower() not in self.supported_suffixes or not path.is_file():
                continue
            try:
                content = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            results.extend(self._extract_routes(content, organization, resolved_service, host, version, documented))
        return unique_results(results)

    @staticmethod
    def _has_documentation(repository: Path) -> bool:
        return any(path.is_file() and path.name.lower().startswith(("readme", "openapi", "swagger")) for path in repository.rglob("*"))

    @staticmethod
    def _extract_routes(content: str, organization: str, service_name: str, host: str, version: str, documented: bool) -> list[DiscoveryResult]:
        results: list[DiscoveryResult] = []
        for match in FASTAPI_PATTERN.finditer(content):
            results.append(DiscoveryResult(organization, service_name, host, version, match["method"].upper(), match["path"], "git", documented))
        for match in FLASK_PATTERN.finditer(content):
            methods_match = FLASK_METHODS_PATTERN.search(match["arguments"])
            methods = [item["method"].upper() for item in QUOTED_METHOD_PATTERN.finditer(methods_match["methods"])] if methods_match else ["GET"]
            for method in methods:
                results.append(DiscoveryResult(organization, service_name, host, version, method, normalize_flask_path(match["path"]), "git", documented))
        return results


class RuntimeLogDiscovery:
    def discover(self, content: str, *, organization: str, service_name: str | None, host: str, version: str) -> list[DiscoveryResult]:
        if not content.strip():
            raise DiscoveryError("Runtime log content is empty")
        resolved_service = service_name or "runtime-service"
        results: list[DiscoveryResult] = []
        for line in content.splitlines():
            match = LOG_PATTERN.match(line)
            if not match:
                continue
            timestamp = parse_timestamp(match["timestamp"])
            results.append(DiscoveryResult(
                organization, resolved_service, host, version, match["method"], normalize_log_path(match["path"]),
                "runtime_log", False, first_seen=timestamp, last_seen=timestamp,
            ))
        return unique_results(results)


def persist_discoveries(db: Session, results: list[DiscoveryResult]):
    records = []
    added_count = 0
    for result in unique_results(results):
        payload = APICreate(
            organization=result.organization, service_name=result.service_name, host=result.host, version=result.version,
            http_method=result.http_method, endpoint_path=result.endpoint_path, source=result.source,
            is_documented=result.is_documented, first_seen=result.first_seen, last_seen=result.last_seen,
            lifecycle_state=LifecycleState.ACTIVE,
        )
        record, added, _ = api_inventory.observe_api(db, payload)
        records.append(record)
        added_count += int(added)
    return records, added_count


def unique_results(results: list[DiscoveryResult]) -> list[DiscoveryResult]:
    unique: dict[tuple[str, str, str, str, str, str], DiscoveryResult] = {}
    for result in results:
        normalized = DiscoveryResult(**{**result.__dict__, "endpoint_path": normalize_path(result.endpoint_path)})
        unique.setdefault(normalized.identity, normalized)
    return list(unique.values())


def normalize_flask_path(path: str) -> str:
    return re.sub(r"<[^>]+>", "{id}", path)


def normalize_log_path(path: str) -> str:
    path = path.split("?", 1)[0]
    segments = ["{id}" if segment.isdigit() or re.fullmatch(r"[0-9a-fA-F]{8}-[0-9a-fA-F-]{27,35}", segment) else segment for segment in path.split("/")]
    return "/".join(segments) or "/"


def parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
