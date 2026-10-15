import json
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Literal, NamedTuple

Level = Literal["debug", "info", "warn", "error"]
_LEVELS = {"debug", "info", "warn", "error"}


class IngestResult(NamedTuple):
    inserted: int
    ids: list[str]


class IngestError(Exception):
    """The ingest API rejected the request or could not be reached."""

    def __init__(self, url: str, status: int | None, body: str):
        self.url = url
        self.status = status
        self.body = body
        super().__init__(f"Ingest failed for {url}: status {status}; body {body}")


class Client:
    """Posts logs and metrics for one service.

    The service name, base URL, and timeout are fixed here so each call only
    passes the event itself. The ingest routes accept a list, so every call
    sends a one-item batch.
    """

    def __init__(self, base_url: str, service: str, timeout_seconds: float):
        if base_url.strip() == "":
            raise ValueError("base_url is required")
        if service.strip() == "":
            raise ValueError("service is required")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be greater than 0")
        self.base_url = base_url.rstrip("/")
        self.service = service
        self.timeout_seconds = timeout_seconds

    def log(
        self,
        level: Level,
        message: str,
        request_id: str,
        label: dict[str, str],
    ) -> IngestResult:
        if level not in _LEVELS:
            raise ValueError(f"level must be one of {sorted(_LEVELS)}; got {level}")
        _require_text(message, "message")
        _require_text(request_id, "request_id")
        _require_string_map(label, "label")
        body = [
            {
                "timestamp": _utc_now(),
                "service": self.service,
                "level": level,
                "message": message,
                "request_id": request_id,
                "label": label,
            }
        ]
        return _post_json(f"{self.base_url}/v1/ingest/logs", body, self.timeout_seconds)

    def metric(self, name: str, value: float, tags: dict[str, str]) -> IngestResult:
        _require_text(name, "name")
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("value must be a number")
        _require_string_map(tags, "tags")
        body = [
            {
                "timestamp": _utc_now(),
                "service": self.service,
                "metric_name": name,
                "value": float(value),
                "tags": tags,
            }
        ]
        return _post_json(f"{self.base_url}/v1/ingest/metrics", body, self.timeout_seconds)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _require_text(value: str, field: str) -> None:
    if value.strip() == "":
        raise ValueError(f"{field} is required")


def _require_string_map(value: dict[str, str], field: str) -> None:
    for key, item in value.items():
        if not isinstance(key, str) or not isinstance(item, str):
            raise ValueError(f"{field} must be a map of strings")


def _post_json(url: str, body: list[dict[str, object]], timeout_seconds: float) -> IngestResult:
    """Send one ingest batch and surface the status and body on failure.

    Callers share this path so a URL or field-name change stays in the SDK.
    """
    payload = json.dumps(body).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            raw = response.read().decode("utf-8")
            status = response.status
    except urllib.error.HTTPError as error:
        raw = error.read().decode("utf-8")
        raise IngestError(url, error.code, raw) from error
    except urllib.error.URLError as error:
        raise IngestError(url, None, str(error.reason)) from error
    return _parse_result(url, status, raw)


def _parse_result(url: str, status: int, raw: str) -> IngestResult:
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as error:
        raise IngestError(url, status, raw) from error
    if not isinstance(parsed, dict):
        raise IngestError(url, status, raw)
    inserted = parsed.get("inserted")
    ids = parsed.get("ids")
    if not isinstance(inserted, int) or not isinstance(ids, list):
        raise IngestError(url, status, raw)
    if not all(isinstance(item, str) for item in ids):
        raise IngestError(url, status, raw)
    return IngestResult(inserted=inserted, ids=ids)
