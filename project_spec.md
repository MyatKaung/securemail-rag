# SecureMail RAG — Project Specification

## 1. Project Summary
SecureMail RAG is a permission-aware enterprise Retrieval-Augmented Generation system over the Enron Email Dataset.

## 2. Target User
An enterprise knowledge worker searching internal email and organizational knowledge.

## 3. Business Problem
Ordinary RAG optimizes for relevance but may retrieve information a user is not authorized to access. Enterprise search must answer two questions:
1. Is this document relevant?
2. Is this user authorized to retrieve it?

## 4. Core Research Questions
### RQ1 — Retrieval Quality
Does hybrid BM25 + dense retrieval outperform either method alone on enterprise email search?

### RQ2 — Permission Safety
Can pre-retrieval authorization filtering reduce unauthorized retrieval to zero while maintaining useful authorized retrieval quality?

## 5. Dataset
- Public Enron Email Dataset.
- Use a manageable subset for development and evaluation.
- Do not commit the entire corpus.
- Provide a documented download/ingestion path.
- Overlay a clearly documented **synthetic RBAC policy** for controlled experiments.
- Do not claim synthetic roles are Enron's historical authorization policy.

## 6. P0 Features — Required
- Dataset ingestion and normalization.
- Evaluation dataset created before advanced features.
- Dense retrieval.
- BM25 retrieval.
- Hybrid retrieval.
- Reranking.
- Permission-aware pre-filtering.
- Grounded generation with citations/source IDs.
- Retrieval evaluation.
- LLM evaluation.
- FastAPI interface.
- Minimal usable UI.
- Monitoring + feedback.
- Docker Compose.
- Reproducible setup instructions.

## 7. P1 Features — High Value
- Query rewriting.
- Caching.
- Guardrails.
- Optional Text2SQL over email metadata.

## 8. P2 Features — Experiments
- HyDE.
- CRAG.
- Self-RAG.

## 9. P3 Stretch
- Public cloud deployment.
- Rust `aprender-rag` retrieval backend.
- Python-vs-Rust retrieval benchmark.

## 10. LLM
Generation provider:
- OpenRouter

Generation model:
- `qwen/qwen3.6-27b`

Secrets:
- `OPENROUTER_API_KEY` in local `.env`.
- `.env` must never be committed.

## 11. Baseline Retrieval
Keep all implementations independently runnable:
- BM25
- dense
- hybrid
- hybrid + reranker

## 12. Core Metrics
Retrieval:
- HitRate@5
- MRR@5
- optional NDCG@5

Security:
- Unauthorized Retrieval Rate
- Authorization decision accuracy
- Authorized HitRate@5

Generation:
- groundedness
- answer relevance
- citation correctness
- refusal correctness

System:
- end-to-end latency
- retrieval latency
- LLM latency
- request count
- feedback
- cache hit rate when caching is enabled

## 13. Deployment Policy
- Docker Compose local deployment is mandatory.
- Cloud is optional bonus work only after all P0 requirements pass.
- Cloud work must never block submission.

## 14. Non-Goals for MVP
- Recreating Enron organizational access controls.
- Building a full email client.
- Full-scale indexing of every Enron message before the pipeline is proven.
- Local LLM serving.
- Rust in the critical path before P0 is complete.
