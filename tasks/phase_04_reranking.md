# Phase 04 — Reranking

- [x] Retrieve candidate_k.
- [x] Rerank to final_k.
- [x] Evaluate hybrid vs hybrid+reranker.
- [x] Use winner as default.

Evidence: the configured cross-encoder reranked 20 hybrid candidates to five
final results over 500 emails and 20 unchanged questions. Hybrid measured
`0.9500 / 0.8667`; Hybrid + reranker measured `1.0000 / 0.9500` for
HitRate@5 / MRR@5. Three queries improved, 16 were unchanged, and one worsened.
Raw results and score/rank provenance are under `evals/results/`.
