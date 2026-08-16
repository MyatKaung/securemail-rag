# Phase 03 — Hybrid Search

- [x] Add BM25 retriever.
- [x] Keep dense retriever.
- [x] Add RRF hybrid retriever.
- [x] Evaluate BM25 vs dense vs hybrid.
- [x] Preserve raw eval outputs.

Evidence: `rank-bm25` runs over the 500-email Phase 02 corpus with the shared
retriever interface. RRF uses rank constant 60 and candidate depth 20. The
20-question evaluation reports Dense `0.9500 / 0.7267`, BM25 `1.0000 / 0.8017`,
and Hybrid `0.9500 / 0.8667` for HitRate@5 / MRR@5. Raw per-retriever results
and the per-query comparison are in `evals/results/`.
