# Phase 07 — Interface

- [x] FastAPI `/query` endpoint.
- [x] Principal/role passed explicitly for demo.
- [x] Minimal dependency-free browser UI served by FastAPI.
- [x] Show sources and authorization-safe evidence only.
- [x] Offline tests for health, successful query, validation, authorization,
  restricted-content exclusion, and missing OpenRouter configuration.
- [x] Optional manual/live UI smoke-test path documented in `docs/interface.md`.

## Evidence

`tests/integration/test_phase07_interface.py` exercises the endpoint with a
mocked generator and fake retrieval components. The production service wires
the existing permission-aware hybrid + cross-encoder reranker to
`basic_grounded_v1`. `uv run pytest -q` passes 64 tests and Ruff passes.
No manual/live UI query was run; the documented smoke path remains optional.
