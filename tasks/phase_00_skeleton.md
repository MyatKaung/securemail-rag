# Phase 00 — Skeleton + Evals First

## Goal
Create a runnable project skeleton and evaluation contracts without implementing advanced RAG.

## Tasks
- [x] Create Python package structure.
- [x] Load configuration from `.env` and YAML without exposing secrets.
- [x] Add config validation for OpenRouter settings.
- [x] Add test framework and linting.
- [x] Define evaluation dataset schemas.
- [x] Create placeholder/sample retrieval and permission test records.
- [x] Add FastAPI health endpoint only.
- [x] Add CI-friendly test command.
- [x] Update rubric evidence only for items actually satisfied.

## Phase 00 verification

- `uv run --extra dev ruff check src tests` passes.
- `uv run --extra dev pytest -q --disable-warnings --maxfail=1` passes: 10 tests.
- Retrieval, hybrid search, reranking, generation, authorization enforcement, and other future-phase features were not implemented.

## Do Not Implement
Hybrid, reranking, HyDE, CRAG, Self-RAG, Text2SQL, caching, cloud, Rust.
