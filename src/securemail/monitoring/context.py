"""Correlation-ID context shared across one API request."""

from __future__ import annotations

import re
from contextvars import ContextVar, Token
from uuid import uuid4

REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")
_request_id: ContextVar[str | None] = ContextVar("securemail_request_id", default=None)


def new_request_id() -> str:
    return str(uuid4())


def valid_request_id(value: str) -> bool:
    return bool(REQUEST_ID_PATTERN.fullmatch(value))


def set_request_id(value: str) -> Token[str | None]:
    if not valid_request_id(value):
        raise ValueError("invalid request ID")
    return _request_id.set(value)


def reset_request_id(token: Token[str | None]) -> None:
    _request_id.reset(token)


def get_request_id() -> str | None:
    return _request_id.get()


def ensure_request_id() -> str:
    current = get_request_id()
    if current is not None:
        return current
    value = new_request_id()
    _request_id.set(value)
    return value
