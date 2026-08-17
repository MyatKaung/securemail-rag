"""Demo-only credentials and signed browser sessions.

This module is intentionally lightweight. It is not a replacement for OAuth,
SSO, JWT infrastructure, or a production identity provider.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from securemail.config import PROJECT_ROOT, ConfigurationError, load_yaml_config

from .demo_identities import DEMO_IDENTITIES, DemoIdentity

DEMO_USERS_PATH = PROJECT_ROOT / "config/demo_users.yaml"
SESSION_COOKIE_NAME = "securemail_demo_session"
DEFAULT_SESSION_MAX_AGE = 8 * 60 * 60
DEFAULT_DEMO_SESSION_SECRET = "securemail-local-demo-session-secret"


class InvalidDemoCredentialsError(ValueError):
    """Raised for any unknown email or incorrect synthetic demo password."""


@dataclass(frozen=True)
class DemoAuthenticator:
    """Validate the allowlisted synthetic credentials without exposing them."""

    passwords: dict[str, str]

    @classmethod
    def from_config(cls, path: str | Path = DEMO_USERS_PATH) -> DemoAuthenticator:
        loaded = load_yaml_config(path)
        users = loaded.get("users")
        if not isinstance(users, dict):
            raise ConfigurationError("demo users config must contain a users mapping")
        passwords: dict[str, str] = {}
        for raw_email, raw_record in users.items():
            email = str(raw_email).strip().casefold()
            if email not in DEMO_IDENTITIES:
                raise ConfigurationError(f"demo users config contains unknown identity: {email}")
            if not isinstance(raw_record, dict) or not isinstance(raw_record.get("password"), str):
                raise ConfigurationError(f"demo password is missing for identity: {email}")
            password = raw_record["password"].strip()
            if not password:
                raise ConfigurationError(f"demo password is empty for identity: {email}")
            passwords[email] = password
        missing = sorted(set(DEMO_IDENTITIES) - set(passwords))
        if missing:
            raise ConfigurationError("demo users config is missing identities: " + ", ".join(missing))
        return cls(passwords=passwords)

    def authenticate(self, email: str, password: str) -> DemoIdentity:
        normalized_email = email.strip().casefold()
        expected = self.passwords.get(normalized_email)
        if expected is None or not hmac.compare_digest(expected, password):
            raise InvalidDemoCredentialsError("invalid synthetic demo credentials")
        return DEMO_IDENTITIES[normalized_email]


class DemoSessionManager:
    """Sign and validate a short-lived, HttpOnly demo session cookie."""

    def __init__(
        self,
        secret: str | None = None,
        *,
        max_age: int = DEFAULT_SESSION_MAX_AGE,
    ) -> None:
        configured_secret = secret or os.getenv(
            "SECUREMAIL_SESSION_SECRET", DEFAULT_DEMO_SESSION_SECRET
        )
        if not configured_secret:
            raise ConfigurationError("SECUREMAIL_SESSION_SECRET must not be empty")
        if max_age <= 0:
            raise ValueError("session max_age must be greater than zero")
        self._secret = configured_secret.encode("utf-8")
        self.max_age = max_age

    def issue(self, email: str, *, now: int | None = None) -> str:
        normalized_email = email.strip().casefold()
        if normalized_email not in DEMO_IDENTITIES:
            raise InvalidDemoCredentialsError("invalid synthetic demo identity")
        payload = {"email": normalized_email, "exp": (now or int(time.time())) + self.max_age}
        encoded_payload = self._encode(payload)
        signature = self._signature(encoded_payload)
        return f"{encoded_payload}.{signature}"

    def resolve_email(self, token: str | None, *, now: int | None = None) -> str | None:
        if not token:
            return None
        try:
            encoded_payload, encoded_signature = token.split(".", maxsplit=1)
            expected_signature = self._signature(encoded_payload)
            if not hmac.compare_digest(encoded_signature, expected_signature):
                return None
            payload = self._decode(encoded_payload)
            email = payload["email"]
            expires_at = int(payload["exp"])
            if not isinstance(email, str) or email not in DEMO_IDENTITIES:
                return None
            if expires_at <= (now or int(time.time())):
                return None
            return email
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            return None

    def set_cookie(self, response: Any, email: str) -> None:
        response.set_cookie(
            SESSION_COOKIE_NAME,
            self.issue(email),
            max_age=self.max_age,
            httponly=True,
            samesite="lax",
            path="/",
        )

    @staticmethod
    def clear_cookie(response: Any) -> None:
        response.delete_cookie(SESSION_COOKIE_NAME, path="/")

    def _signature(self, encoded_payload: str) -> str:
        digest = hmac.new(
            self._secret,
            encoded_payload.encode("ascii"),
            hashlib.sha256,
        ).digest()
        return self._b64encode(digest)

    @staticmethod
    def _encode(payload: dict[str, object]) -> str:
        raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
        return DemoSessionManager._b64encode(raw)

    @staticmethod
    def _decode(value: str) -> dict[str, object]:
        raw = base64.urlsafe_b64decode(value.encode("ascii") + b"===")
        decoded = json.loads(raw.decode("utf-8"))
        if not isinstance(decoded, dict):
            raise TypeError("session payload must be a mapping")
        return decoded

    @staticmethod
    def _b64encode(value: bytes) -> str:
        return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")
