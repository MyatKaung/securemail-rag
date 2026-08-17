"""Permission-aware retrieval security boundaries."""

from .authorization import (
    AuthorizationError,
    AuthorizationFilter,
    AuthorizationPolicy,
    PrincipalContext,
    SyntheticRBACPolicy,
)
from .demo_identities import (
    DEMO_IDENTITIES,
    DemoIdentity,
    UnknownDemoIdentityError,
    resolve_demo_identity,
)

__all__ = [
    "DEMO_IDENTITIES",
    "AuthorizationError",
    "AuthorizationFilter",
    "AuthorizationPolicy",
    "DemoIdentity",
    "PrincipalContext",
    "SyntheticRBACPolicy",
    "UnknownDemoIdentityError",
    "resolve_demo_identity",
]
