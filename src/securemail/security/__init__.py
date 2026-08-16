"""Permission-aware retrieval security boundaries."""

from .authorization import (
    AuthorizationError,
    AuthorizationFilter,
    AuthorizationPolicy,
    PrincipalContext,
    SyntheticRBACPolicy,
)

__all__ = [
    "AuthorizationError",
    "AuthorizationFilter",
    "AuthorizationPolicy",
    "PrincipalContext",
    "SyntheticRBACPolicy",
]
