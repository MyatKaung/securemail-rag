# Implementation Plan

## P0 — Submission-Critical
- [x] Phase 00 — Skeleton + evaluation contracts
- [x] Phase 01 — Enron ingestion + normalization
- [x] Phase 02 — Basic dense RAG
- [x] Phase 03 — BM25 + hybrid search
- [x] Phase 04 — reranking
- [x] Phase 05 — permission-aware retrieval
- [x] Phase 06 — generation + citations + LLM eval
- [x] Phase 07 — FastAPI + minimal UI
- [x] Phase 08 — monitoring + feedback
- [x] Phase 09 — Docker + reproducibility
- [ ] Phase 10 — final rubric audit

## P1 — High-Value Enhancements
- [ ] query rewriting experiment
- [ ] caching
- [ ] guardrails
- [ ] Text2SQL over email metadata

## P2 — Advanced RAG Experiments
- [ ] HyDE
- [ ] CRAG
- [ ] Self-RAG

## P3 — Stretch
- [ ] cloud deployment
- [ ] Rust `aprender-rag` backend
- [ ] Python-vs-Rust benchmark

## Rule
P1/P2/P3 must not delay or destabilize P0.

Phase 06 has measured live evidence for versioned grounded prompts,
permission-safe generation boundaries, response parsing, and deterministic
evaluation. Basic grounded is selected from the 20-question comparison.

Phase 07 adds a tested FastAPI `/query` boundary and a lightweight browser UI.
The endpoint preserves the production retrieval/generation defaults, accepts an
explicit synthetic principal, and returns source IDs without email bodies.

Phase 08 adds request-level SQLite telemetry, correlation IDs, safe structured
logs, feedback persistence, and an aggregated monitoring dashboard. No
retrieval or generation behavior was changed.

Phase 09 adds a Python 3.12 locked Docker image, a single-service Compose
deployment with health checks, persistent monitoring/model-cache volumes, an
explicit data preparation path, and reviewer-oriented setup documentation.
