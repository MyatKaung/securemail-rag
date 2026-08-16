# Hybrid Search

Phase 03 compares the unchanged Phase 02 dense baseline with a sparse BM25
retriever and an RRF-fused hybrid retriever over the same 500 normalized Enron
emails and the same 20 manually grounded questions.

BM25 uses the `rank-bm25` library with deterministic Unicode word tokenization,
case folding, `k1=1.5`, and `b=0.75`. The sparse index returns the original
`email_id` and normalized retrieval document for every result. Queries with no
indexed token return no results; equal BM25 scores use corpus input order as a
stable tie-breaker.

Hybrid retrieval uses Reciprocal Rank Fusion:

```text
RRF(d) = sum over retrievers r of 1 / (60 + rank_r(d))
```

Ranks are one-based. The rank constant (`60`), candidate depth (`20`), BM25
parameters, and final `top_k` are explicit in `config/app.yaml`, the retrieval
classes, and the Phase 03 evaluation CLI. Evaluation artifacts are written to
`evals/results/phase03_retrieval_comparison.json` plus one result file per
retriever. The comparison artifact records per-query cases where BM25 or dense
wins, where hybrid improves either baseline, and where it does not.

Measured result over the development corpus:

| Retriever | HitRate@5 | MRR@5 |
| --- | ---: | ---: |
| Dense | 0.9500 | 0.7267 |
| BM25 | 1.0000 | 0.8017 |
| Hybrid RRF | 0.9500 | 0.8667 |

Hybrid is selected as the Phase 03 default retrieval composition because it
improves MRR over both independent baselines, while its unchanged HitRate@5 is
reported explicitly. The dense and BM25 retrievers remain independently
selectable for comparison. Permission filtering and reranking are outside
this phase.
