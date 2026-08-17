# Phase 07 — Application Interface

SecureMail RAG exposes a FastAPI endpoint and a small dependency-free browser
UI. The production path keeps the Phase 06 defaults: permission-aware hybrid
retrieval, cross-encoder reranking, and `basic_grounded_v1` generation through
OpenRouter/Qwen.

## Run locally

```bash
PYTHONPATH=src uv run uvicorn securemail.api.app:app --reload
```

Open <http://127.0.0.1:8000/login> for the browser UI. The page labels the
login accounts as synthetic demo identities created for this experiment; they
are not Enron historical accounts or permissions. The credentials are
intentionally non-secret demo values stored in `config/demo_users.yaml`:

| Email | Demo password |
| --- | --- |
| `finance@securemail.demo` | `finance-demo` |
| `legal@securemail.demo` | `legal-demo` |
| `employee@securemail.demo` | `employee-demo` |
| `admin@securemail.demo` | `admin-demo` |

The login creates a short-lived signed HttpOnly cookie. This is a local demo
authentication layer, not OAuth, SSO, JWT infrastructure, or real identity
management.

## API

`GET /health` returns `{"status": "ok"}` without loading models or requiring
OpenRouter credentials.

`POST /login` accepts an allowlisted synthetic email and demo password. On
success it sets the signed session cookie and returns display-only email,
department, and role information. `GET /logout` clears the cookie and returns
to `/login`.

`POST /query` requires the session cookie and accepts only:

```json
{
  "question": "What was discussed about the finance plan?"
}
```

The response contains the request ID, grounded answer, source email IDs,
retrieval method, evidence count, refusal/insufficient-evidence flags, and
uncertainty text. It never returns email bodies or retrieval candidates. The
authenticated session email is resolved to `PrincipalContext` before constructing the
authorization filter. Role, department, access level, and resource scope are
not accepted from the client, and query text cannot grant access. If no
authorized evidence is retrieved, the service returns a safe no-evidence
response without calling the LLM.

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
open `/login`, use one synthetic demo credential, and click **Query securely**. Verify
that the answer shows source IDs only and that a cross-department question does
not expose restricted email content. This is a manual path and is intentionally
not part of the default test suite.
