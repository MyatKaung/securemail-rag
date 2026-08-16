# Phase 09 — Docker + Reproducibility

- [x] Dockerfile and `.dockerignore`.
- [x] Docker Compose defines the complete required local app and health check.
- [x] Fresh-clone and data-acquisition instructions.
- [x] Direct dependencies pinned with `uv.lock`.
- [x] Verify no secrets are copied or committed.
- [x] Persist monitoring SQLite and model cache with named volumes.

## Evidence

The app image copies only source code, non-secret config, and the normalized
500-email sample. The index is generated from that processed file at first
query; raw Enron acquisition is explicit through `make ingest`. Compose has one
`app` service and omits unused PostgreSQL. The Dockerfile and Compose health
check are present. `uv lock --check`, Ruff, and the full offline test suite pass
(73 tests).

Verified on 2026-08-16 with `docker compose up --build -d`: the image built with
the Linux CPU-only `torch==2.13.0+cpu` lock entry, `/health` returned
`{"status":"ok"}`, and the container reached Docker health status `healthy`.
A live `/query` was intentionally not run because it would download model
weights and make a paid OpenRouter call.
