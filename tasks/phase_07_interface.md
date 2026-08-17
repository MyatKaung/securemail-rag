# Phase 07 — Interface

- [x] FastAPI `/query` endpoint.
- [x] Synthetic demo login/session resolves server-side to the trusted principal.
- [x] Minimal dependency-free browser UI served by FastAPI.
- [x] Show sources and authorization-safe evidence only.
- [x] Offline tests for health, successful query, validation, authorization,
  restricted-content exclusion, and missing OpenRouter configuration.
- [x] Optional manual/live UI smoke-test path documented in `docs/interface.md`.

## Evidence

`tests/integration/test_phase07_interface.py` and
`tests/unit/test_demo_identities.py` exercise the endpoint with a mocked
generator, fake retrieval components, login/logout, trusted session identity
resolution, client override rejection, authorization boundaries, and the
zero-evidence LLM short-circuit. The production service wires the existing
permission-aware hybrid + cross-encoder reranker to `basic_grounded_v1`.
`uv run pytest -q` passes 88 tests and Ruff passes. No manual/live UI query was
run; the documented smoke path remains optional.
