# LLM Zoomcamp 2026 Rubric Compliance Tracker

Codex must update this file only when implementation evidence exists.

## Phase 00 Evidence (2026-08-16)

- Configuration contracts are implemented in `src/securemail/config/settings.py` and tested for dotenv loading, YAML loading, validation, and secret masking.
- Evaluation record contracts and sample dataset validation are implemented in `src/securemail/evaluation/schemas.py` and covered by tests.
- A health-only FastAPI app is implemented in `src/securemail/api/app.py`; this is not evidence that the full user-facing interface is complete.
- The Phase 00 test/lint commands pass: 10 tests and Ruff checks. No retrieval, generation, authorization, monitoring, ingestion, containerization, or full-interface rubric item is marked complete by this phase.
- Phase 01 adds a tested CMU Enron acquisition/normalization path, stable IDs, deterministic deduplication, a synthetic RBAC overlay, and a 25-record processed sample. No retrieval ground-truth labels are claimed.
- Phase 02 adds a modular dense embedding/index/retrieval path, a grounded OpenRouter client boundary, 20 real-email retrieval questions, and measured dense results over 500 indexed emails.

## Core

### Problem Description — target 2/2
- [ ] Target user identified.
- [ ] Problem clearly explained.
- [x] Dataset source and limitations documented.
Evidence:
Phase 01 documents the exact CMU source URL, RFC 2822/MIME raw format, manageable-subset strategy, and synthetic-permissions limitation in `docs/data_design.md` and `docs/ingestion.md`.

### Retrieval Flow — target 2/2
- [x] Knowledge base used.
- [ ] LLM used.
- [ ] End-to-end RAG demonstrated.
Evidence:
Phase 02 indexes 500 normalized Enron emails and exercises question-to-dense-retrieval plus grounded prompt construction. No live LLM call was run, so LLM-used and end-to-end claims remain open.

### Retrieval Evaluation — target 2/2
- [x] Ground-truth evaluation dataset exists.
- [ ] BM25 evaluated.
- [x] Dense evaluated.
- [ ] Hybrid evaluated.
- [ ] Best approach selected based on results.
Evidence:
`evals/datasets/retrieval_ground_truth.phase02.json` contains 20 questions tied to inspected normalized emails with notes. `evals/results/dense_retrieval_phase02.json` records dense HitRate@5 `0.9500` and MRR@5 `0.7266666667` over 500 indexed emails. BM25, hybrid, and best-approach selection remain future work.

### LLM Evaluation — target 2/2
- [ ] At least two generation approaches/prompts evaluated.
- [ ] Metrics/results documented.
- [ ] Best approach used in final system.
Evidence:
Phase 00: no generation approach or LLM evaluation is claimed.

### Interface — target 2/2
- [ ] FastAPI interface works.
- [ ] Minimal user-facing interface works.
Evidence:
Phase 00: the `/health` endpoint is verified; the required FastAPI search interface and minimal UI remain future work.

### Ingestion Pipeline — target 2/2
- [x] Repeatable/automated ingestion pipeline exists.
- [x] Fresh ingestion tested.
Evidence:
`src/securemail/ingestion/cli.py` and `src/securemail/ingestion/pipeline.py` stream or download the documented CMU archive, normalize a configurable subset, and write JSONL. Unit and end-to-end integration tests pass; a 25-record sample was generated from the public source.

### Monitoring — target 2/2
- [ ] User feedback captured.
- [ ] Dashboard/monitoring includes at least five useful charts/metrics.
Evidence:

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
- [ ] Implemented and evaluated.
Evidence:

### Reranking +1
- [ ] Implemented and evaluated.
Evidence:

### Query Rewriting +1
- [ ] Implemented and evaluated.
Evidence:

## Bonus
### Cloud Deployment +2
- [ ] Public deployment available.
Evidence:

## Project Differentiator — not a substitute for rubric
### Permission-Aware Retrieval
- [ ] Pre-retrieval authorization implemented.
- [ ] Unauthorized Retrieval Rate measured.
- [ ] Prompt-injection security tests included.
Evidence:

## Rule
Never mark an item complete merely because code exists. Require a passing test, evaluation output, or reproducible runtime evidence.
