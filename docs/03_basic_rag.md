# Basic RAG

Phase 02 baseline:

```text
normalized JSONL -> document preparation -> SentenceTransformer embeddings
    -> exact cosine dense index -> top-k evidence -> grounded OpenRouter prompt
    -> Qwen3.6-27B answer + retrieved source email IDs
```

The configured embedding model is `sentence-transformers/all-MiniLM-L6-v2`.
Emails are represented as one retrieval document each, combining subject,
sender, recipients, date, and body while preserving the stable `email_id`.
`DenseIndex` uses normalized NumPy vectors and deterministic score ordering;
its interface is independent of future BM25 and hybrid implementations.

The OpenRouter client reads `OPENROUTER_BASE_URL`, `OPENROUTER_API_KEY`, and
`OPENROUTER_MODEL` through the Phase 00 settings boundary. The grounded prompt
requires evidence-only answers, an insufficient-evidence response when needed,
and source email IDs. No live generation call is required by the default tests.
