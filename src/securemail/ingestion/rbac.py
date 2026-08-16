"""Deterministic synthetic authorization metadata for controlled experiments."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

SYNTHETIC_POLICY_VERSION = "synthetic-enron-overlay-v1"
SYNTHETIC_ROLES = ("general", "finance", "legal", "executive", "admin")
_KEYWORD_ROLES = {
    "admin": "admin",
    "executive": "executive",
    "legal": "legal",
    "finance": "finance",
}


@dataclass(frozen=True)
class SyntheticRBACMetadata:
    """The synthetic role and access fields attached to a normalized email."""

    synthetic_role: str
    department: str
    access_level: str
    resource_scope: str


def _role_for_mailbox(mailbox: str) -> str:
    normalized_mailbox = mailbox.strip().casefold()
    for keyword, role in _KEYWORD_ROLES.items():
        if keyword in normalized_mailbox:
            return role

    digest = hashlib.sha256(normalized_mailbox.encode("utf-8")).digest()
    return SYNTHETIC_ROLES[digest[0] % len(SYNTHETIC_ROLES)]


def assign_synthetic_rbac(mailbox: str) -> SyntheticRBACMetadata:
    """Assign repeatable synthetic access metadata from a mailbox name.

    This is an experiment-only overlay. It does not reconstruct Enron's
    historical authorization model or infer real employee permissions.
    """

    role = _role_for_mailbox(mailbox)
    if role == "admin":
        return SyntheticRBACMetadata(role, "global", "global", "global")
    if role == "general":
        return SyntheticRBACMetadata(role, "general", "standard", "shared")
    return SyntheticRBACMetadata(role, role, "department", role)
