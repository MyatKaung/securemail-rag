# Phase 05 — Permission-Aware Retrieval

## Critical
Authorization must pre-filter candidate retrieval.

- [x] Implement principal/role model.
- [x] Implement synthetic RBAC policy.
- [x] Apply authorization before BM25 and dense retrieval.
- [x] Run permission test suite.
- [x] Run adversarial tests.
- [x] Measure Unauthorized Retrieval Rate.

Evidence: `PrincipalContext` defines role, department, access level, and
resource scope. `AuthorizationFilter` is applied before dense/BM25 scoring and
propagated through hybrid and reranking. The 24-case dataset produces no-filter
URR `1.0000`, filtered URR `0.0000`, decision accuracy `1.0000`, authorized
HitRate@5 `1.0000`, and authorized MRR@5 `0.9167`.
