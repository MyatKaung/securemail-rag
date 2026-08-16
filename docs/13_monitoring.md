# Phase 08 — Monitoring + User Feedback

Monitoring is implemented with a replaceable `MonitoringStore` interface and a
local SQLite implementation at `data/monitoring/securemail.sqlite3`. The store
contains request IDs, timestamps, timing values, status flags, and feedback
records. It deliberately has no question, prompt, email-body, or API-key
columns.

## Request telemetry

Each RAG request records:

- correlation/request ID and UTC start time
- total end-to-end latency
- retrieval latency
- reranking latency
- OpenRouter/LLM latency
- HTTP status
- permission-denied flag
- refusal and insufficient-evidence flags

`X-Request-ID` is accepted only when it matches the safe request-ID pattern;
otherwise the API creates a UUID. The same ID is placed in the response header,
query response, structured logs, telemetry row, and feedback reference.

Structured logs are JSON events containing only event names, request IDs,
status, flags, and timing values. Questions, prompts, email content, comments,
and credentials are excluded.

## Feedback and dashboard

`POST /feedback` accepts `request_id`, `positive`, and an optional short
`comment`. Feedback is stored only when the request ID exists. The browser UI
shows thumbs-up/down buttons after a response and submits the original request
ID.

The aggregated dashboard is available at `/monitoring`, with JSON metrics at
`/monitoring/metrics`. It shows total requests and requests over time, average
and p95 end-to-end latency, average retrieval latency, average reranking
latency, average LLM latency, permission denials, refusal/insufficient rate,
and positive versus negative feedback. Individual comments and request content
are not displayed.

The default suite uses temporary SQLite files and synthetic monitoring fixtures;
it makes no OpenRouter calls. A live UI feedback click-through is optional and
has not been run as part of Phase 08.
