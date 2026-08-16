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
principal as synthetic RBAC metadata created for this experiment; it does not
represent Enron's historical permissions.

## API

`GET /health` returns `{"status": "ok"}` without loading models or requiring
OpenRouter credentials.

`POST /query` accepts:

```json
{
  "question": "What was discussed about the finance plan?",
  "principal": {
    "role": "employee",
    "department": "finance",
    "access_level": "department",
    "resource_scope": "finance"
  }
}
```

The response contains the grounded answer, source email IDs, retrieval method,
evidence count, refusal/insufficient-evidence flags, and uncertainty text. It
never returns email bodies or retrieval candidates. The principal is converted
to `PrincipalContext` before constructing the authorization filter; the query
text cannot grant access.

Useful errors are returned without stack traces: `422` for malformed input,
`403` for authorization failures, `502` for retrieval/generation failures, and
`503` when OpenRouter configuration is unavailable.

## Optional live UI smoke test

With a valid local `.env` and the development corpus present, start Uvicorn,
choose a demo principal, enter a question, and click **Query securely**. Verify
that the answer shows source IDs only and that a cross-department question does
not expose restricted email content. This is a manual path and is intentionally
not part of the default test suite.
