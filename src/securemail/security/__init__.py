"""Permission-aware retrieval security boundaries."""

from .authorization import (
    AuthorizationError,
    AuthorizationFilter,
    AuthorizationPolicy,
    PrincipalContext,
    SyntheticRBACPolicy,
)
from .demo_auth import (
    DEMO_USERS_PATH,
    SESSION_COOKIE_NAME,
    DemoAuthenticator,
    DemoSessionManager,
    InvalidDemoCredentialsError,
)
from .demo_identities import (
    DEMO_IDENTITIES,
    DemoIdentity,
    UnknownDemoIdentityError,
    resolve_demo_identity,
)

__all__ = [
    "DEMO_IDENTITIES",
    "DEMO_USERS_PATH",
    "SESSION_COOKIE_NAME",
    "AuthorizationError",
    "AuthorizationFilter",
    "AuthorizationPolicy",
    "DemoAuthenticator",
    "DemoIdentity",
    "DemoSessionManager",
    "InvalidDemoCredentialsError",
    "PrincipalContext",
    "SyntheticRBACPolicy",
    "UnknownDemoIdentityError",
    "resolve_demo_identity",
]
