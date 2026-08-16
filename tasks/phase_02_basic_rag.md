# Phase 02 — Basic Dense RAG

- [x] Chunk/represent emails appropriately.
- [x] Embed.
- [x] Dense top-k retrieval.
- [x] Grounded Qwen generation via OpenRouter.
- [x] Source IDs/citations.
- [x] Baseline retrieval eval.

## Phase 02 verification

- Embedding model: `sentence-transformers/all-MiniLM-L6-v2`.
- Index: exact cosine similarity over normalized NumPy vectors, with stable email IDs and JSON/NumPy persistence.
- Indexed corpus: 500 normalized Enron emails.
- Ground truth: 20 manually/verifiably grounded questions from inspected emails.
- Dense HitRate@5: `0.9500`.
- Dense MRR@5: `0.7266666667`.
- Results: `evals/results/dense_retrieval_phase02.json`.
- Ruff passes; the full suite passes with 29 tests.
- No live Qwen smoke test was run; OpenRouter tests use an injected fake client.

## Scope boundary

BM25, hybrid retrieval, reranking, query rewriting, HyDE, CRAG, Self-RAG,
Text2SQL, caching, cloud, and Rust remain future phases.
