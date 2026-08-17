# SecureMail RAG

SecureMail RAG is a permission-aware enterprise email RAG system over a
manageable development subset of the public Enron Email Dataset. The business
problem is that ordinary search optimizes relevance but can retrieve information
the requester is not authorized to see. SecureMail RAG applies a synthetic RBAC
policy before retrieval, then answers from authorized evidence with source IDs.

Status: Phases 00–09 implemented. Optional advanced RAG, cloud deployment, and
Rust work are intentionally not started.

## Architecture

```text
login session -> server-resolved synthetic email identity -> pre-retrieval RBAC filter
      -> dense + BM25 -> RRF hybrid -> cross-encoder reranker
      -> authorized evidence -> basic_grounded_v1 -> Qwen via OpenRouter
      -> answer/source IDs + SQLite telemetry/feedback
```

The production path uses hybrid retrieval, `cross-encoder/ms-marco-MiniLM-L-6-v2`,
pre-retrieval authorization, `basic_grounded_v1`, and
`qwen/qwen3.6-27b`. Dense, BM25, hybrid, and hybrid+reranker baselines remain
independently runnable.

## Dataset and authorization limitation

The exact Enron source is the CMU May 7, 2015 archive:
`https://www.cs.cmu.edu/~enron/enron_mail_20150507.tar.gz`.

The repository includes a normalized 500-email development sample at
`data/sample/enron_dev_500.jsonl`, so normal startup does not download the full
corpus. To reproduce it from the public source:

```bash
make ingest
```

The roles, departments, access levels, and resource scopes are a deterministic
synthetic overlay created for this experiment. They are not Enron's historical
permissions. See [docs/data_design.md](docs/data_design.md) and
[docs/12_permission_aware_rag.md](docs/12_permission_aware_rag.md).

The browser/API demo identities are `finance@securemail.demo`,
`legal@securemail.demo`, `employee@securemail.demo`, and
`admin@securemail.demo`. The server resolves these emails to trusted
`PrincipalContext` values; clients cannot submit or override the role,
department, access level, or resource scope. This is a synthetic identity
selector for evaluation/demo use, not authentication for real Enron accounts.

The local demo login uses intentionally non-secret credentials from
`config/demo_users.yaml`:

| Email | Demo password |
| --- | --- |
| `finance@securemail.demo` | `finance-demo` |
| `legal@securemail.demo` | `legal-demo` |
| `employee@securemail.demo` | `employee-demo` |
| `admin@securemail.demo` | `admin-demo` |

This is a lightweight signed-cookie demo layer, not OAuth, SSO, JWT, or a real
identity provider. OpenRouter credentials are separate and are never used as
login credentials.

## Measured results

Retrieval evaluation uses the same 500-email corpus and 20-question ground
truth set:

| Retriever | HitRate@5 | MRR@5 |
| --- | ---: | ---: |
| Dense | 0.9500 | 0.7267 |
| BM25 | 1.0000 | 0.8017 |
| Hybrid | 0.9500 | 0.8667 |
| Hybrid + reranker | 1.0000 | 0.9500 |

Permission evaluation:

| Metric | Result |
| --- | ---: |
| No-filter Unauthorized Retrieval Rate | 1.0000 |
| Pre-retrieval filtered Unauthorized Retrieval Rate | 0.0000 |
| Authorization decision accuracy | 1.0000 |
| Authorized HitRate@5 | 1.0000 |
| Authorized MRR@5 | 0.9167 |

Generation evaluation on the same 20 questions (deterministic rubric):

| Artifact / strategy | Overall | Groundedness | Relevance | Citation correctness | Refusal correctness | Non-empty answers |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Historical `phase06_generation.json` / `basic_grounded_v1` | 0.4875 | 0.3500 | 0.3500 | 0.5500 | 0.7000 | 0.3500 |
| Historical `phase06_generation.json` / `structured_grounded_v1` | 0.4500 | 0.2750 | 0.2750 | 0.4500 | 0.8000 | 0.3500 |
| Current `phase06_generation_reasoning_none.json` / `basic_grounded_v1` | 0.7917 | 0.7083 | 0.7583 | 0.9000 | 0.8000 | 1.0000 |
| Current `phase06_generation_reasoning_none.json` / `structured_grounded_v1` | 0.7292 | 0.6583 | 0.6583 | 0.9000 | 0.7000 | 1.0000 |

`basic_grounded_v1` remains the default. Production Qwen requests use
`temperature=0.1`, `max_tokens=500`, and explicit
`reasoning.effort="none"`. The historical machine-readable artifact is
`evals/results/phase06_generation.json`; the current production-settings
artifact is `evals/results/phase06_generation_reasoning_none.json`. The new
full run recorded average latency of 3.742 seconds for basic and 3.867 seconds
for structured. The historical artifact did not record latency; the controlled
five-question comparison recorded 18.119 seconds with the old implicit
reasoning behavior versus 4.359 seconds with reasoning disabled. Other
generated evaluation outputs remain ignored by default. The full Enron corpus
is never committed.

## Local setup

Requirements: Python 3.12+, `uv`, and optionally Docker Desktop.

```bash
git clone https://github.com/MyatKaung/securemail-rag.git
cd securemail-rag
cp .env.example .env
# Edit .env and set OPENROUTER_API_KEY locally.
make setup
make test
make lint
```

`make setup` installs the exact versions from `uv.lock`. `.env` is ignored and
must never be committed. `make ingest` is an explicit acquisition/preprocessing
step; application startup never downloads the Enron archive. `make eval` runs
the offline dense/BM25/hybrid retrieval evaluation and does not make OpenRouter
calls. The Phase 06 live generation evaluation is an explicit, paid operation.

## Docker Compose

The Compose project contains one `app` service. PostgreSQL is not included
because the current P0 implementation uses SQLite for monitoring and feedback.

```bash
cp .env.example .env
# Set OPENROUTER_API_KEY in .env.
docker compose up --build
```

Open:

- Login/UI: <http://127.0.0.1:8000/login>
- health: <http://127.0.0.1:8000/health>
- monitoring: <http://127.0.0.1:8000/monitoring>

The image copies only the normalized 500-email sample and non-secret config.
The retrieval index is generated lazily from that processed JSONL on the first
query after the local embedding model is available. Hugging Face model files
are cached in the named `huggingface_cache` volume; the Enron archive is never
downloaded during startup. Missing processed data or config causes a clear
startup failure. Monitoring SQLite data is persisted in the named
`monitoring_data` volume across app-container restarts.

Stop the stack with:

```bash
make down
```

OpenRouter values are passed as environment variables by Compose. No `.env`,
API key, or secret is copied into the image.

## Interface, monitoring, and security

The FastAPI API provides `POST /query`, `POST /feedback`, and
`GET /monitoring/metrics`; the browser UI provides synthetic demo email
identities, source IDs, and feedback buttons. Request IDs propagate through API headers, responses,
structured logs, telemetry, and feedback. Monitoring stores only timing/status
aggregates and feedback records; it does not log prompts, questions, email
bodies, or credentials.

See [docs/interface.md](docs/interface.md),
[docs/13_monitoring.md](docs/13_monitoring.md),
[docs/deployment_strategy.md](docs/deployment_strategy.md), and
[docs/rubric_compliance.md](docs/rubric_compliance.md).
