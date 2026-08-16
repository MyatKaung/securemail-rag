# Reranking

Phase 04 uses the Phase 03 hybrid retriever as the candidate generator. It
retrieves 20 candidates, scores each original user-query/original email-text
pair with the configured
`cross-encoder/ms-marco-MiniLM-L-6-v2` model through
`sentence-transformers.CrossEncoder`, and returns the final top 5.

The reranking interface is injected and swappable. Each result preserves the
stable `email_id`, normalized document metadata, original hybrid retrieval
score, original candidate rank, and cross-encoder score. Ties preserve the
candidate order, making reranking deterministic for equal scores. Tests inject
a fake scorer; normal tests make no model or OpenRouter calls.

Evaluation uses the unchanged 500-email corpus and 20-question Phase 02 ground
truth:

| Retriever | HitRate@5 | MRR@5 |
| --- | ---: | ---: |
| Hybrid | 0.9500 | 0.8667 |
| Hybrid + reranker | 1.0000 | 0.9500 |

The reranker improved three relevant-email ranks, left 16 unchanged, and made
one worse. It improved both measured metrics, so Hybrid + reranker is selected
as the Phase 04 default. Mean measured reranking time was 44.94 ms per
question in the evaluation run. Per-query rank changes and score provenance
are stored in `evals/results/phase04_reranking_comparison.json` and
`evals/results/hybrid_reranked_phase04.json`.

Authorization filtering is not part of this phase; the existing pre-retrieval
security boundary remains a Phase 05 requirement.
