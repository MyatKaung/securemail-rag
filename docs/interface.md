# Phase 07 — Application Interface

SecureMail RAG exposes a FastAPI endpoint and a small dependency-free browser
UI. The production path keeps the Phase 06 defaults: permission-aware hybrid
retrieval, cross-encoder reranking, and `basic_grounded_v1` generation through
OpenRouter/Qwen.

## Run locally

```bash
PYTHONPATH=src uv run uvicorn securemail.api.app:app --reload
```

Open <http://127.0.0.1:8000/> for the browser UI. The page labels the active
email as a synthetic demo identity created for this experiment; it is not an
Enron historical account or permission.

## API

`GET /health` returns `{"status": "ok"}` without loading models or requiring
OpenRouter credentials.

`POST /query` accepts:

```json
{
  "question": "What was discussed about the finance plan?",
  "email": "finance@securemail.demo"
}
```

The response contains the request ID, grounded answer, source email IDs,
retrieval method, evidence count, refusal/insufficient-evidence flags, and
uncertainty text. It never returns email bodies or retrieval candidates. The
email must be one of the four server-side synthetic demo identities; the
backend resolves it to `PrincipalContext` before constructing the authorization
filter. Role, department, access level, and resource scope are not accepted
from the client, and query text cannot grant access.

`POST /feedback` accepts `request_id`, `positive`, and an optional short
`comment`. The request ID must refer to a recorded query. The browser UI submits
this ID from its in-memory response state; it does not store credentials.

`/monitoring` is an aggregated dashboard for request volume, end-to-end/retrieval/
reranking/LLM latency, permission denials, refusal rate, and feedback counts.

Useful errors are returned without stack traces: `422` for malformed input,
`403` for authorization failures, `502` for retrieval/generation failures, and
`503` when OpenRouter configuration is unavailable.

## Optional live UI smoke test

With a valid local `.env` and the development corpus present, start Uvicorn,
choose a synthetic demo email identity, enter a question, and click **Query securely**. Verify
that the answer shows source IDs only and that a cross-department question does
not expose restricted email content. This is a manual path and is intentionally
not part of the default test suite.
