# Phase 08 — Monitoring + Feedback

- [x] Capture thumbs up/down or equivalent feedback.
- [x] Track >=5 useful metrics/charts.
- [x] Include retrieval, reranking, end-to-end, and LLM latency.
- [x] Include permission denials/security metric.
- [x] Add request/correlation IDs and safe structured logging.
- [x] Persist telemetry and feedback behind a storage interface.

## Evidence

`POST /feedback`, `/monitoring`, and `/monitoring/metrics` are implemented in
the FastAPI application. `SQLiteMonitoringStore` stores request telemetry and
feedback without raw prompts or email content. The dashboard exposes request
volume, average/p95 end-to-end latency, retrieval latency, reranking latency,
LLM latency, permission denials, refusal rate, and feedback counts.

`tests/integration/test_phase08_monitoring.py` uses
`tests/fixtures/monitoring_events.json` and verifies telemetry creation,
request-ID propagation, feedback persistence, invalid IDs, permission-denial
aggregation, dashboard metrics, and secret-safe structured logs. Ruff passes
and the full suite passes 69 tests. No live UI feedback flow was manually run.
