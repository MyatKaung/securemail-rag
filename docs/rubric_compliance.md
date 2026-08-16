# LLM Zoomcamp 2026 Rubric Compliance Tracker

Codex must update this file only when implementation evidence exists.

## Phase 00 Evidence (2026-08-16)

- Configuration contracts are implemented in `src/securemail/config/settings.py` and tested for dotenv loading, YAML loading, validation, and secret masking.
- Evaluation record contracts and sample dataset validation are implemented in `src/securemail/evaluation/schemas.py` and covered by tests.
- A health-only FastAPI app is implemented in `src/securemail/api/app.py`; this is not evidence that the full user-facing interface is complete.
- The Phase 00 test/lint commands pass: 10 tests and Ruff checks. No retrieval, generation, authorization, monitoring, ingestion, containerization, or full-interface rubric item is marked complete by this phase.
- Phase 01 adds a tested CMU Enron acquisition/normalization path, stable IDs, deterministic deduplication, a synthetic RBAC overlay, and a 25-record processed sample. No retrieval ground-truth labels are claimed.
- Phase 02 adds a modular dense embedding/index/retrieval path, a grounded OpenRouter client boundary, 20 real-email retrieval questions, and measured dense results over 500 indexed emails.
- Phase 03 adds a tested `rank-bm25` sparse retriever and configurable RRF hybrid retriever. On the unchanged 500-email corpus and 20-question set, dense/BM25/hybrid HitRate@5 is `0.9500`/`1.0000`/`0.9500` and MRR@5 is `0.7267`/`0.8017`/`0.8667`; the machine-readable comparison is `evals/results/phase03_retrieval_comparison.json`.
- Phase 04 adds an injected CrossEncoder reranker over 20 hybrid candidates. On the same corpus and questions, Hybrid + reranker reaches HitRate@5 `1.0000` and MRR@5 `0.9500`; `evals/results/phase04_reranking_comparison.json` records three improvements, 16 unchanged ranks, one regression, and measured latency.
- Phase 05 adds pre-retrieval synthetic RBAC filtering shared by dense, BM25, hybrid, hybrid + reranker, and grounded prompt construction. On 24 permission cases over the 500-email corpus, no-filter URR is `1.0000`, filtered URR is `0.0000`, policy decision accuracy is `1.0000`, authorized HitRate@5 is `1.0000`, and authorized MRR@5 is `0.9167`.

## Core

### Problem Description — target 2/2
- [ ] Target user identified.
- [ ] Problem clearly explained.
- [x] Dataset source and limitations documented.
Evidence:
Phase 01 documents the exact CMU source URL, RFC 2822/MIME raw format, manageable-subset strategy, and synthetic-permissions limitation in `docs/data_design.md` and `docs/ingestion.md`.

### Retrieval Flow — target 2/2
- [x] Knowledge base used.
- [x] LLM used.
- [x] End-to-end RAG demonstrated.
Evidence:
Phase 02 indexes 500 normalized Enron emails. Phase 06 runs the permission-aware hybrid + reranker to OpenRouter/Qwen generation boundary on 20 questions; `evals/results/phase06_generation.json` records 40 successful calls and source-bearing responses.

### Retrieval Evaluation — target 2/2
- [x] Ground-truth evaluation dataset exists.
- [x] BM25 evaluated.
- [x] Dense evaluated.
- [x] Hybrid evaluated.
- [x] Best approach selected based on results.
Evidence:
`evals/datasets/retrieval_ground_truth.phase02.json` contains 20 questions tied to inspected normalized emails with notes. `evals/results/dense_retrieval_phase02.json` preserves the Phase 02 dense result. Phase 03 writes separate dense, BM25, and hybrid results plus a per-query comparison under `evals/results/`; hybrid is selected for its measured MRR@5 improvement, not for HitRate.

### LLM Evaluation — target 2/2
- [x] At least two generation approaches/prompts evaluated.
- [x] Metrics/results documented.
- [x] Best approach used in final system.
Evidence:
Phase 06 evaluates `basic_grounded_v1` and `structured_grounded_v1` on the same 20 cases with deterministic groundedness, relevance, citation, and refusal metrics. Basic grounded scores `0.4875` overall versus `0.4500` for structured grounded and is configured as the default. Full per-question and aggregate results are in `evals/results/phase06_generation.json`.

### Interface — target 2/2
- [x] FastAPI interface works.
- [x] Minimal user-facing interface works.
Evidence:
Phase 07 adds `POST /query` with validated question/principal schemas and a lazy production service using permission-aware hybrid + reranking + `basic_grounded_v1`. `tests/integration/test_phase07_interface.py` verifies health, successful mocked end-to-end queries, validation errors, authorization failures, missing OpenRouter configuration, and restricted-content exclusion. A dependency-free browser UI is served at `/` and its synthetic-principal labels are tested; the manual live UI smoke path is documented in `docs/interface.md` but was not run.

### Ingestion Pipeline — target 2/2
- [x] Repeatable/automated ingestion pipeline exists.
- [x] Fresh ingestion tested.
Evidence:
`src/securemail/ingestion/cli.py` and `src/securemail/ingestion/pipeline.py` stream or download the documented CMU archive, normalize a configurable subset, and write JSONL. Unit and end-to-end integration tests pass; a 25-record sample was generated from the public source.

### Monitoring — target 2/2
- [x] User feedback captured.
- [x] Dashboard/monitoring includes at least five useful charts/metrics.
Evidence:
Phase 08 adds `POST /feedback` with request-ID validation and SQLite persistence, thumbs-up/down controls in the existing UI, and the aggregated `/monitoring` dashboard. `tests/integration/test_phase08_monitoring.py` verifies request IDs, telemetry timing fields, feedback persistence, permission-denial aggregation, refusal rate, latency metrics, request volume over time, and secret-safe JSON logs. The dashboard exposes more than five metrics without displaying prompts, email bodies, comments, or credentials.

### Containerization — target 2/2
- [ ] Full application starts with Docker Compose.
Evidence:

### Reproducibility — target 2/2
- [x] Dataset acquisition documented.
- [ ] Dependency versions pinned.
- [x] `.env.example` provided.
- [ ] Fresh-clone setup tested.
Evidence:
Phase 01 documents the exact source URL and streaming/offline acquisition commands in `docs/ingestion.md`. Dependency pinning and fresh-clone verification remain future work.

## Best-Practice Points
### Hybrid Search +1
- [x] Implemented and evaluated.
Evidence:
`src/securemail/retrieval/hybrid.py` implements configurable RRF over the common retriever interface. `evals/results/phase03_retrieval_comparison.json` records the exact same-corpus comparison, including query-level wins and hybrid non-improvements.

### Reranking +1
- [x] Implemented and evaluated.
Evidence:
`src/securemail/retrieval/reranking.py` provides the swappable reranker interface and configured CrossEncoder implementation. The Phase 04 result artifacts compare Hybrid `0.9500 / 0.8667` with Hybrid + reranker `1.0000 / 0.9500` for HitRate@5 / MRR@5 and preserve query-level rank changes.

### Query Rewriting +1
- [ ] Implemented and evaluated.
Evidence:

## Bonus
### Cloud Deployment +2
- [ ] Public deployment available.
Evidence:

## Project Differentiator — not a substitute for rubric
### Permission-Aware Retrieval
- [x] Pre-retrieval authorization implemented.
- [x] Unauthorized Retrieval Rate measured.
- [x] Prompt-injection security tests included.
Evidence:
`src/securemail/security/authorization.py` defines the principal and policy. Dense and BM25 restrict candidate scoring before retrieval, hybrid propagates the same filter, reranking receives only authorized candidates, and `build_grounded_prompt` rejects unauthorized evidence. `evals/results/phase05_permission.json` and `tests/unit/test_authorization.py` provide the measurement and adversarial evidence.

## Rule
Never mark an item complete merely because code exists. Require a passing test, evaluation output, or reproducible runtime evidence.
