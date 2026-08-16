# Implementation Plan

## P0 — Submission-Critical
- [x] Phase 00 — Skeleton + evaluation contracts
- [x] Phase 01 — Enron ingestion + normalization
- [x] Phase 02 — Basic dense RAG
- [x] Phase 03 — BM25 + hybrid search
- [x] Phase 04 — reranking
- [x] Phase 05 — permission-aware retrieval
- [x] Phase 06 — generation + citations + LLM eval
- [ ] Phase 07 — FastAPI + minimal UI
- [ ] Phase 08 — monitoring + feedback
- [ ] Phase 09 — Docker + reproducibility
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
