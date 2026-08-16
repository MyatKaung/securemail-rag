"""Structured logging with an intentionally small, safe event surface."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

from .context import get_request_id

LOGGER = logging.getLogger("securemail")


class JsonFormatter(logging.Formatter):
    """Render log records as JSON without including arbitrary message fields."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "event": getattr(record, "event", record.getMessage()),
            "request_id": get_request_id(),
        }
        fields = getattr(record, "fields", {})
        if isinstance(fields, dict):
            payload.update(fields)
        return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def configure_structured_logging(level: int = logging.INFO) -> None:
    """Install one JSON handler if the application has not configured logging."""

    LOGGER.setLevel(level)
    if not LOGGER.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        LOGGER.addHandler(handler)


def log_event(event: str, **fields: Any) -> None:
    """Log only caller-provided aggregate/safe fields, never prompts or bodies."""

    safe_fields = {
        key: value
        for key, value in fields.items()
        if key not in {"api_key", "prompt", "question", "body", "email_body", "comment"}
    }
    LOGGER.info("monitoring_event", extra={"event": event, "fields": safe_fields})
