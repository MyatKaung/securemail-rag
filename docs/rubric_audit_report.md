# LLM Zoomcamp 2026 Rubric Audit

**Audit date:** 2026-08-17  
**Scope:** read-only audit of the completed Phase 00–09 repository  
**Application code changed:** no. This report is the only new file created by the audit.

The audit read `AGENTS.md`, the project specification, architecture,
implementation plan, README, all completed phase task files, the rubric tracker,
the rubric-audit instructions, source/tests, and every JSON artifact currently
present under `evals/results/`. Results below are based on repository evidence,
not README claims alone.

## Executive result

| Area | Estimated score | Maximum | Status |
| --- | ---: | ---: | --- |
| Core rubric | **18** | 18 | All core criteria have implementation and tracked evidence. |
| Best-practice points | **3** | 3 | Hybrid search, reranking, and an evaluated query-rewriting experiment pass; rewriting remains disabled because it did not improve results. |
| Cloud bonus | **0** | 2 | No public cloud deployment, intentionally. |
| Other bonus | **0** | — | No additional bonus is evidenced. |

The implementation is substantially complete for P0. The exact Phase 06
machine-readable result artifact is now tracked, so a fresh reviewer clone can
verify the LLM metrics without relying on local-only files.

## Core rubric criteria

### 1. Problem description — PASS — expected 2/2, estimated 2/2

Evidence:

- `project_spec.md` §2–§3 identifies the target user as an enterprise knowledge
  worker and explains the authorization-versus-relevance problem.
- `README.md` explains the business problem in the opening section.
- `docs/01_problem_and_scope.md` provides the project scope and motivation.
- `docs/rubric_compliance.md` still has the `Target user identified` checkbox
  unchecked, but the underlying repository specification does contain that
  evidence. This is a tracker inconsistency, not a demonstrated product gap.

Test/evaluation evidence: documentation criterion; no runtime test is expected.

Missing requirement: update the stale rubric checkbox before submission.
Impact: documentation hygiene only; no core score loss if the reviewer accepts
the evidence in `project_spec.md`.

### 2. Retrieval flow — PASS — expected 2/2, estimated 2/2

Evidence:

- `src/securemail/retrieval/` contains dense, BM25, hybrid, indexing, and
  evaluation components behind shared interfaces.
- `src/securemail/retrieval/reranking.py` provides candidate-to-final reranking.
- `src/securemail/generation/pipeline.py` implements retrieval → authorization
  re-check → prompt → generation.
- `src/securemail/api/service.py` wires the production path as hybrid retrieval,
  cross-encoder reranking, synthetic pre-retrieval authorization, grounded
  generation, and OpenRouter/Qwen.
- `tests/integration/test_basic_rag.py` and
  `tests/integration/test_phase06_generation.py` cover the end-to-end boundary.

Test/evaluation evidence: full suite passes; Phase 06 records permission-aware
hybrid + reranker generation calls.

Missing requirement: the architecture diagram mentions LangGraph, but LangGraph
is not implemented. It is not a P0 requirement in `project_spec.md`, and the
phase instructions explicitly deferred it.
Impact: none to the core rubric; it is an intentionally deferred architecture
option.

### 3. Retrieval evaluation — PASS — expected 2/2, estimated 2/2

Evidence:

- `evals/datasets/retrieval_ground_truth.phase02.json` contains 20 grounded
  questions tied to inspected email IDs and notes.
- `evals/results/dense_retrieval_phase02.json` preserves the Phase 02 baseline.
- `evals/results/phase03_retrieval_comparison.json` compares dense, BM25, and
  hybrid on the same 500-email corpus and 20 questions.
- `evals/results/phase04_reranking_comparison.json` compares hybrid and hybrid
  + reranker on the same corpus/questions and includes per-query rank changes.
- `tests/integration/test_phase03_retrieval.py` and
  `tests/integration/test_phase04_reranking.py` cover the evaluation paths.

Test/evaluation evidence: exact metrics verified from the JSON artifacts:

| Retriever | HitRate@5 | MRR@5 |
| --- | ---: | ---: |
| Dense | 0.9500 | 0.7267 |
| BM25 | 1.0000 | 0.8017 |
| Hybrid | 0.9500 | 0.8667 |
| Hybrid + reranker | 1.0000 | 0.9500 |

The selected production path is justified by measured reranker results; dense,
BM25, hybrid, and hybrid + reranker remain independently runnable.

Missing requirement: optional NDCG@5 is not present, but it was optional.
Impact: none to the core score.

### 4. LLM evaluation — PASS — expected 2/2, estimated 2/2

Evidence:

- `evals/datasets/generation_ground_truth.phase06.json` contains 20 cases.
- `src/securemail/generation/strategies.py` defines independently selectable,
  versioned `basic_grounded_v1` and `structured_grounded_v1` prompts.
- `src/securemail/generation/evaluation.py` defines deterministic groundedness,
  answer relevance, citation correctness, and refusal correctness scoring.
- `tasks/phase_06_generation_eval.md`, `docs/model_strategy.md`, and
  `docs/rubric_compliance.md` document 40 successful OpenRouter calls.
- The tracked historical `evals/results/phase06_generation.json` and current
  `evals/results/phase06_generation_reasoning_none.json` contain model, base URL,
  timestamp, prompt versions, configuration, per-question results, and scores.

Test/evaluation evidence from the local JSON artifact:

| Approach | Overall | Groundedness | Relevance | Citation correctness | Refusal correctness |
| --- | ---: | ---: | ---: | ---: | ---: |
| Basic grounded | 0.4875 | 0.3500 | 0.3500 | 0.5500 | 0.7000 |
| Structured grounded | 0.4500 | 0.2750 | 0.2750 | 0.4500 | 0.8000 |

The current production-settings artifact uses explicit
`reasoning.effort="none"`, `max_tokens=500`, and `temperature=0.1` without
changing retrieval or prompts:

| Approach | Overall | Groundedness | Relevance | Citation correctness | Refusal correctness | Non-empty answers | Average latency |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Basic grounded | 0.7917 | 0.7083 | 0.7583 | 0.9000 | 0.8000 | 1.0000 | 3.742 s |
| Structured grounded | 0.7292 | 0.6583 | 0.6583 | 0.9000 | 0.7000 | 1.0000 | 3.867 s |

`basic_grounded` is selected because its measured overall score is higher. Six
cases expected insufficient-evidence/refusal behavior; the new artifact reports
refusal correctness of 0.3333 for basic and 0.0000 for structured on those
cases. This remains a generation-quality limitation, although it does not
weaken the pre-retrieval authorization boundary. The historical artifact is
preserved for comparison; it did not record average latency. A controlled
five-question comparison recorded 18.119 s old versus 4.359 s with reasoning
disabled.

Missing requirement: none for the rubric criterion. The exact final artifact is
allowed through `.gitignore`, tracked, and referenced by the README and rubric
tracker. Temporary and future evaluation outputs remain ignored by default.
Impact: none; the prior core-evidence gap is closed.

### 5. Interface — PASS — expected 2/2, estimated 2/2

Evidence:

- `src/securemail/api/app.py` exposes `GET /health`, `POST /query`,
  `POST /feedback`, `/monitoring`, and `/monitoring/metrics`.
- `src/securemail/api/ui.py` provides a dependency-free browser UI with demo
  principals, synthetic-RBAC labeling, sources, and feedback controls.
- `docs/interface.md` documents request/response schemas and error behavior.
- `tests/integration/test_health.py` and
  `tests/integration/test_phase07_interface.py` cover health, successful
  mocked queries, validation errors, authorization errors, missing provider
  configuration, and restricted-content exclusion.

Test/evaluation evidence: offline interface tests pass; no paid OpenRouter call
was made by the default suite.

Missing requirement: a manual live UI query was not run, but the optional smoke
path is documented and mocked API coverage exists.
Impact: none to the core rubric; manual demonstration confidence only.

### 6. Ingestion pipeline — PASS — expected 2/2, estimated 2/2

Evidence:

- `src/securemail/ingestion/cli.py` provides explicit source/archive
  acquisition and configurable subset processing.
- `src/securemail/ingestion/parser.py`, `pipeline.py`, and `rbac.py` implement
  normalization, stable IDs, deterministic deduplication, malformed-field
  handling, and synthetic RBAC metadata.
- `docs/data_design.md` and `docs/ingestion.md` document the exact CMU source,
  RFC 2822/MIME archive format, schema, and synthetic-permission limitation.
- `tests/unit/test_ingestion.py` and
  `tests/integration/test_ingestion_pipeline.py` cover parsing, missing fields,
  stable IDs, deduplication, malformed messages, RBAC determinism, and an
  end-to-end sample pipeline.
- `data/sample/enron_dev_500.jsonl` is the reproducible 500-email development
  corpus used by retrieval and permission evaluation.

Test/evaluation evidence: ingestion integration tests pass; the completed
Phase 01 checklist records the public-source sample and 17-test milestone.

Missing requirement: no full-corpus ingestion is committed, by design.
Impact: none; the project specification explicitly requires a manageable subset.

### 7. Monitoring — PASS — expected 2/2, estimated 2/2

Evidence:

- `src/securemail/monitoring/storage.py` defines the replaceable
  `MonitoringStore` interface and SQLite implementation.
- Telemetry records request ID, timestamp, total/retrieval/reranking/LLM
  latency, status, permission denial, refusal, and insufficient-evidence flags.
- `src/securemail/monitoring/dashboard.py` exposes request volume, average/p95
  end-to-end latency, retrieval latency, reranking latency, LLM latency,
  permission denials, refusal rate, and feedback counts.
- `tests/integration/test_phase08_monitoring.py` uses
  `tests/fixtures/monitoring_events.json` and verifies telemetry, feedback,
  aggregation, request IDs, and secret-safe logs.
- `docs/13_monitoring.md` documents the safe aggregated dashboard.

Test/evaluation evidence: monitoring tests pass; the dashboard has more than
five useful metrics and excludes prompts, questions, email bodies, comments,
and credentials.

Missing requirement: no manual UI feedback click-through was run.
Impact: none to the core rubric; the manual path is optional and documented.

### 8. Containerization — PASS — expected 2/2, estimated 2/2

Evidence:

- `Dockerfile` builds a Python 3.12 image with locked dependencies, source,
  config, and the normalized 500-email sample.
- `.dockerignore` excludes `.env`, raw/processed data, monitoring SQLite, and
  evaluation outputs from the image context while retaining `.env.example` and
  the sample corpus.
- `docker-compose.yml` defines one `app` service with FastAPI/UI, named
  monitoring and Hugging Face cache volumes, and a `/health` health check.
- PostgreSQL is intentionally absent because the current P0 implementation
  uses SQLite.
- `tasks/phase_09_docker_repro.md` records a successful `docker compose up
  --build -d` on 2026-08-16, `/health` response `{"status":"ok"}`, and Docker
  health status `healthy`.

Test/evaluation evidence: current audit ran `docker compose config --quiet`
with a non-secret placeholder environment value and it passed. The prior
fresh-start evidence recorded successful image build and health.

Missing requirement: no live Docker `/query` was run, intentionally, to avoid a
paid provider call and model downloads.
Impact: none to the core score; health/startup is verified and the live query is
an optional manual demonstration.

### 9. Reproducibility — PASS — expected 2/2, estimated 2/2

Evidence:

- `pyproject.toml` pins direct dependencies; `uv.lock` is committed and passes
  `uv lock --check`.
- `Makefile` provides `setup`, `test`, `lint`, `ingest`, `eval`, `up`, `down`,
  and `audit` targets.
- `docs/ingestion.md`, `docs/deployment_strategy.md`, and `README.md` provide
  clone, `.env`, data acquisition, evaluation, startup, UI, health, and
  monitoring commands.
- `.env.example` is tracked with a blank key; `.env` is ignored by `.gitignore`.
- The current audit reproduced `73 passed in 0.41s`, Ruff check passed, format
  check passed, and `uv lock --check` passed.
- The completed Phase 09 task records a fresh-clone Docker startup verification.

Test/evaluation evidence: the current repository passes the complete offline
test/lint/lock checks; Compose configuration validates with a placeholder key.

Missing requirement: the ignored Phase 06 result artifact weakens reproducible
evaluation evidence, but not the fresh application setup itself.
Impact: no additional core deduction beyond the LLM-evaluation evidence gap.

## Best-practice points

### Hybrid search — PASS — expected 1/1

Evidence: `src/securemail/retrieval/hybrid.py`,
`tests/unit/test_hybrid_retrieval.py`, `tasks/phase_03_hybrid_search.md`, and
tracked `evals/results/phase03_retrieval_comparison.json`. RRF is explicit and
configurable; the comparison shows BM25, dense, and hybrid results on the same
20 questions. Hybrid improves MRR@5 from dense 0.7267 to 0.8667, although BM25
has the highest HitRate@5.

Missing requirement: none for this point.

### Reranking — PASS — expected 1/1

Evidence: `src/securemail/retrieval/reranking.py`,
`tests/unit/test_reranking.py`, `tasks/phase_04_reranking.md`, and tracked
`evals/results/phase04_reranking_comparison.json`. Candidate depth is 20,
final depth is 5, and the configured cross-encoder improves Hybrid from
0.9500/0.8667 to 1.0000/0.9500 for HitRate@5/MRR@5. The artifact records three
improvements, 16 unchanged cases, one regression, and latency.

Missing requirement: none for this point.

### Query rewriting — PASS — expected 1/1

Evidence: `src/securemail/retrieval/query_rewriting.py` provides the optional
feature flag, versioned rewrite prompt, OpenRouter/Qwen adapter, persistent
cache, malformed-response fallback, and a wrapper that delegates authorization
to the unchanged retriever. `evals/results/phase10_query_rewriting.json`
evaluates the same 500-email corpus and unchanged 20-question benchmark.

Test/evaluation evidence: the explicit live evaluation made 20 OpenRouter calls.
The baseline hybrid + reranker measured HitRate@5 `1.0000` / MRR@5 `0.9500`;
the query-rewrite treatment measured `1.0000` / `0.9500`. All 20 model outputs
were empty or invalid verbose/truncated responses and safely fell back to the
original query. The feature therefore remains disabled by default, as required
when the measured result is equal rather than better.

Missing requirement: no measured improvement and no valid non-fallback rewrite
was observed in this run. This is a documented experiment outcome, not an
unreported failure.
Impact: none; the best-practice implementation/evaluation point is supported,
while the production default remains the stronger measured baseline.

## Cloud deployment bonus

### Cloud deployment — FAIL — expected 2/2 bonus

Evidence: `implementation_plan.md` and `tasks/phase_11_cloud.md` leave public
cloud deployment unchecked. `docs/deployment_strategy.md` explicitly treats
cloud as optional P3 work. The local Docker Compose deployment is present and
verified, but no public deployment URL or cloud evidence exists.

Missing requirement: public cloud deployment and corresponding reproducible
evidence.
Impact: cloud bonus only; it does not reduce the core score.

## Project differentiator: permission-aware secure RAG

| Security criterion | Status | Evidence and result |
| --- | --- | --- |
| Pre-retrieval authorization | **PASS** | `src/securemail/security/authorization.py`, `src/securemail/retrieval/dense.py`, `bm25.py`, `hybrid.py`, `reranking.py`, and `src/securemail/api/service.py` apply the shared filter before scoring/candidate generation. |
| Unauthorized Retrieval Rate | **PASS** | Tracked `evals/results/phase05_permission.json`: no-filter URR `1.0000`, filtered URR `0.0000` over 24 cases; authorization decision accuracy `1.0000`. |
| Authorized quality retained | **PASS** | The same artifact reports authorized HitRate@5 `1.0000` and authorized MRR@5 `0.9167`. |
| Unauthorized candidates to reranker | **PASS** | `tests/unit/test_authorization.py::test_reranker_receives_only_authorized_hybrid_candidates` and `tests/integration/test_phase05_permissions.py` cover the boundary. |
| Unauthorized evidence to LLM context | **PASS** | `src/securemail/generation/pipeline.py` calls `assert_allowed` before prompt construction/provider calls; `tests/unit/test_generation_phase06.py` verifies fail-closed behavior. |
| Prompt text cannot override policy | **PASS** for the authorization boundary | `tests/unit/test_authorization.py::test_prompt_rejects_unauthorized_content_even_when_query_requests_override` and policy tests cover “Ignore permissions”/identity-claim style requests. |
| End-to-end refusal quality for adversarial/insufficient cases | **PARTIAL** | The Phase 06 artifact includes adversarial and permission-sensitive cases, but six expected refusal/insufficient cases have basic refusal correctness `0.1667` and structured refusal correctness `0.3333`. This is a generation-quality weakness, not an observed retrieval leak. |

The strongest verified security claim is therefore: restricted content is blocked
before reranking and before LLM prompt construction, and measured filtered URR is
zero. The weaker claim is that the model always produces the ideal refusal text;
the generation evaluation does not support that stronger claim.

## Verified reported results

| Result | Actual artifact | Verified value |
| --- | --- | --- |
| Dense HitRate@5 / MRR@5 | tracked `evals/results/dense_retrieval_phase02.json` | `0.9500 / 0.7266666667` |
| BM25 HitRate@5 / MRR@5 | tracked `evals/results/phase03_retrieval_comparison.json` | `1.0000 / 0.8016666667` |
| Hybrid HitRate@5 / MRR@5 | tracked `evals/results/phase03_retrieval_comparison.json` | `0.9500 / 0.8666666667` |
| Hybrid + reranker HitRate@5 / MRR@5 | tracked `evals/results/phase04_reranking_comparison.json` | `1.0000 / 0.9500000000` |
| Permission metrics | tracked `evals/results/phase05_permission.json` | no-filter URR `1.0000`; filtered URR `0.0000`; decision accuracy `1.0000`; authorized HitRate@5 `1.0000`; authorized MRR@5 `0.9166666667` |
| Generation metrics | tracked `evals/results/phase06_generation.json` and `evals/results/phase06_generation_reasoning_none.json` | historical basic `0.4875` / structured `0.4500`; current basic `0.7917` / structured `0.7292`; basic selected; 20 questions; 40 calls per artifact |
| Query rewriting metrics | tracked `evals/results/phase10_query_rewriting.json` | baseline `1.0000 / 0.9500`; treatment `1.0000 / 0.9500`; 20 rewrite calls; rewriting disabled |

All values match the README, rubric tracker, and the two tracked generation
artifacts. The historical result remains available for reproducibility and the
new production-settings result can be inspected from a fresh clone.

## Repository and security checks

- **Tests:** `uv run pytest -q` → `88 passed` for the current repository.
- **Ruff:** `uv run ruff check src tests` → `All checks passed!`.
- **Formatting:** `uv run ruff format --check src tests` → 75 files already formatted.
- **Lockfile:** `uv lock --check` passed.
- **Compose:** configuration validation with a non-secret placeholder value passed. Existing Phase 09 evidence records a successful fresh `docker compose up --build -d`, healthy container, and `/health` response.
- **`.env`:** ignored by `.gitignore`; only `.env.example` is tracked.
- **Secret scan:** no real OpenRouter key pattern or private-key file is tracked. `git grep` found only intentional dummy test strings such as `test-secret` and `dotenv-secret` in `tests/unit/test_config.py`; these are not credentials.
- **Dataset scope:** tracked data contains only `.gitkeep`, a 59.6 KB 25-email sample, and a 1.17 MB normalized 500-email sample. No full Enron archive is tracked.
- **Phase 06 artifact safety:** both tracked Phase 06 artifacts contain no API-key, secret, credential, or private-key values; only the configured public endpoint/model, generation controls, evaluation metadata, scores, timings, and generated evaluation records are tracked.
- **Synthetic RBAC disclosure:** clearly stated in `README.md`, `docs/data_design.md`, `docs/ingestion.md`, and the policy docstring; it is not presented as Enron historical authorization.
- **Reviewer setup:** `README.md` includes clone, `.env`, setup, test, lint, ingest, evaluation, Docker, UI, health, and monitoring instructions.

## Prioritized remediation list

### P0 — must fix before submission

No outstanding P0 remediation items remain from this audit. The specific Phase
06 artifact is tracked, the rubric evidence points to it, and the stale problem
description checklist entries are aligned with the repository evidence.

### P1 — easy score/improvement items

1. Add a documented, offline-safe command for reproducing the deterministic
   retrieval evaluation and a clearly opt-in command for the paid generation
   evaluation, including where the generated result artifact is written.
2. Add a short README note explaining the generation refusal limitation shown by
   the measured adversarial/insufficient-evidence cases, rather than presenting
   the overall generation score without the refusal tradeoff.
3. Optionally run and document one manual UI query/feedback smoke test after
   confirming cost and model-download expectations.

### P2 — optional bonus/stretch

1. Deploy the existing Compose application publicly for the +2 cloud bonus,
   with secret-safe configuration and a reproducible health check.
2. Consider HyDE, CRAG, Self-RAG, Text2SQL, caching, or Rust only after the
   tracked-evidence gap is fixed and only if measured results justify them.

## Final audit conclusion

SecureMail RAG has strong, directly tested and tracked P0 implementation evidence,
especially the permission boundary: pre-retrieval filtering reduces measured
unauthorized retrieval from 100% to 0%, while authorized HitRate@5 remains
1.0000, and restricted records are excluded from reranking and LLM context.
The Phase 06 result artifact is now included in the committed evidence set;
query rewriting has also been evaluated and documented without changing the
production default. Remaining work is optional cloud/stretch work.
