"""Pre-retrieval authorization for the deterministic synthetic RBAC overlay."""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass
from typing import Protocol

from securemail.retrieval.documents import RetrievalDocument

ACCESS_LEVELS = {"standard": 1, "department": 2, "global": 3}
GLOBAL_SCOPE = "global"


class AuthorizationError(PermissionError):
    """Raised when protected evidence is supplied to a downstream component."""


@dataclass(frozen=True)
class PrincipalContext:
    """Explicit user context used by the synthetic authorization policy."""

    role: str
    department: str
    access_level: str
    resource_scope: str

    def __post_init__(self) -> None:
        for field_name in ("role", "department", "access_level", "resource_scope"):
            value = getattr(self, field_name).strip().casefold()
            if not value:
                raise ValueError(f"{field_name} must not be empty")
            object.__setattr__(self, field_name, value)
        if self.access_level not in ACCESS_LEVELS:
            raise ValueError(f"unsupported access_level: {self.access_level}")


class AuthorizationPolicy(Protocol):
    """Policy interface independent of any retrieval implementation."""

    def is_allowed(self, principal: PrincipalContext, metadata: Mapping[str, str | None]) -> bool:
        """Return whether this principal may retrieve the resource."""


class SyntheticRBACPolicy:
    """Experiment-only policy for the Phase 01 synthetic metadata overlay.

    Rules, in order:
    * ``admin`` principals may retrieve every synthetic resource.
    * Global resources require global access and global scope.
    * Shared resources require at least standard access and shared/global scope.
    * Department resources require matching department, at least department
      access, and department/global scope.

    This policy is deliberately not historical Enron authorization data.
    """

    def is_allowed(self, principal: PrincipalContext, metadata: Mapping[str, str | None]) -> bool:
        resource_scope = (metadata.get("resource_scope") or "").strip().casefold()
        department = (metadata.get("department") or "").strip().casefold()
        access_level = (metadata.get("access_level") or "").strip().casefold()
        if not resource_scope or access_level not in ACCESS_LEVELS:
            return False
        if principal.role == "admin":
            return True
        if resource_scope == GLOBAL_SCOPE:
            return principal.access_level == "global" and principal.resource_scope == GLOBAL_SCOPE
        if resource_scope == "shared":
            return ACCESS_LEVELS[principal.access_level] >= ACCESS_LEVELS[
                access_level
            ] and principal.resource_scope in {"shared", GLOBAL_SCOPE}
        return (
            principal.department == department
            and ACCESS_LEVELS[principal.access_level] >= ACCESS_LEVELS[access_level]
            and principal.resource_scope in {department, GLOBAL_SCOPE}
        )


class AuthorizationFilter:
    """Bind a principal and policy into a reusable pre-retrieval document filter."""

    def __init__(self, principal: PrincipalContext, policy: AuthorizationPolicy):
        self.principal = principal
        self.policy = policy

    def is_allowed(self, document: RetrievalDocument) -> bool:
        return self.policy.is_allowed(self.principal, document.metadata)

    def allowed_email_ids(self, documents: Sequence[RetrievalDocument]) -> set[str]:
        return {document.email_id for document in documents if self.is_allowed(document)}

    def filter_documents(
        self, documents: Sequence[RetrievalDocument]
    ) -> tuple[RetrievalDocument, ...]:
        return tuple(document for document in documents if self.is_allowed(document))

    def assert_allowed(self, documents: Collection[RetrievalDocument]) -> None:
        unauthorized = [
            document.email_id for document in documents if not self.is_allowed(document)
        ]
        if unauthorized:
            raise AuthorizationError(
                f"unauthorized evidence cannot cross the security boundary: {unauthorized}"
            )
