# Deployment Strategy

## Decision
Local Docker Compose is mandatory.
Public cloud deployment is optional P3 bonus.

Phase 09 implements one local `app` container. It serves FastAPI, the browser
UI, the existing hybrid/reranker/RBAC/generation path, and monitoring/feedback.
PostgreSQL is intentionally omitted because the current implementation uses
SQLite. Monitoring is persisted through the `monitoring_data` named volume.

## Sequence
1. Core RAG passes.
2. Retrieval and LLM evals pass.
3. Permission tests pass.
4. Docker Compose works from a fresh clone.
5. README/setup is complete.
6. Only then attempt public cloud deployment.

## Reproducible local container

The Docker image uses Python 3.12, exact direct dependency pins in
`pyproject.toml`, and the committed `uv.lock`. The image copies the normalized
500-email sample and non-secret configuration only. The runtime index is built
from `data/sample/enron_dev_500.jsonl` on the first query; the Enron archive is
never downloaded by container startup. Sentence-transformer and cross-encoder
weights are downloaded only when first needed and persist in the
`huggingface_cache` named volume.

Fresh start:

```bash
cp .env.example .env
# Set OPENROUTER_API_KEY in .env; do not commit .env.
docker compose up --build
```

The Compose interpolation fails before startup if the API key is absent. The
container health check calls `/health`. Runtime data and model/config files are
validated during FastAPI startup, with a clear `make ingest` message if the
normalized sample or required config is missing.

Verification on 2026-08-16: `docker compose up --build -d` completed, the
container reached Docker health status `healthy`, and `GET /health` returned
`{"status":"ok"}`. No live `/query` was run during the container test because
that would incur an OpenRouter call and trigger model downloads.

## Cloud Constraint
Do not require a cloud GPU.
Generation uses OpenRouter.
Prefer a low-cost CPU/container deployment if cloud deployment is attempted.
