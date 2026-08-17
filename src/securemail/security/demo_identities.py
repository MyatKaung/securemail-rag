"""Trusted synthetic demo identities for the browser/API boundary."""

from __future__ import annotations

from dataclasses import dataclass

from .authorization import PrincipalContext


class UnknownDemoIdentityError(ValueError):
    """Raised when a request names an identity outside the demo allowlist."""


@dataclass(frozen=True)
class DemoIdentity:
    """A display label and server-owned principal for one demo email identity."""

    email: str
    label: str
    principal: PrincipalContext


DEMO_IDENTITIES: dict[str, DemoIdentity] = {
    "finance@securemail.demo": DemoIdentity(
        email="finance@securemail.demo",
        label="Finance employee",
        principal=PrincipalContext(
            role="employee",
            department="finance",
            access_level="department",
            resource_scope="finance",
        ),
    ),
    "legal@securemail.demo": DemoIdentity(
        email="legal@securemail.demo",
        label="Legal employee",
        principal=PrincipalContext(
            role="employee",
            department="legal",
            access_level="department",
            resource_scope="legal",
        ),
    ),
    "employee@securemail.demo": DemoIdentity(
        email="employee@securemail.demo",
        label="Shared/general employee",
        principal=PrincipalContext(
            role="employee",
            department="general",
            access_level="standard",
            resource_scope="shared",
        ),
    ),
    "admin@securemail.demo": DemoIdentity(
        email="admin@securemail.demo",
        label="Admin",
        principal=PrincipalContext(
            role="admin",
            department="global",
            access_level="global",
            resource_scope="global",
        ),
    ),
}


def resolve_demo_identity(email: str) -> PrincipalContext:
    """Resolve only allowlisted demo email identities to trusted principals."""

    normalized_email = email.strip().casefold()
    try:
        return DEMO_IDENTITIES[normalized_email].principal
    except KeyError as exc:
        raise UnknownDemoIdentityError("unknown synthetic demo identity") from exc
