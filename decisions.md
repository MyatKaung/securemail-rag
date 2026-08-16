# Architecture Decision Log

Record decisions as:

## ADR-XXX — Title
**Status:** proposed / accepted / rejected  
**Date:** YYYY-MM-DD

### Context
Why a decision is needed.

### Decision
What was chosen.

### Alternatives
What was considered.

### Consequences
Benefits, risks, follow-up work.

## ADR-001 — Keep Phase 00 configuration and evaluation contracts provider-neutral
**Status:** accepted
**Date:** 2026-08-16

### Context
The project needs a runnable skeleton before retrieval or generation features are added. Configuration must support OpenRouter while keeping secrets out of YAML and diagnostics, and evaluation data must be validated before any retriever is selected.

### Decision
Use a small configuration boundary that reads dotenv values without mutating the process environment, validates OpenRouter settings on demand, loads non-secret YAML mappings, and masks API keys in representations. Use Pydantic models for retrieval, permission, and generation evaluation records.

### Alternatives
Load settings directly throughout the application, or defer validation until a provider client is constructed. Use unvalidated dictionaries for evaluation records.

### Consequences
Phase 00 remains independently testable and provider-neutral. Future phases must inject retrievers and generation clients behind these boundaries and must not treat the sample evaluation records as final Enron ground truth.

## ADR-002 — Stream the CMU Enron archive for a deterministic development subset
**Status:** accepted  
**Date:** 2026-08-16

### Context
The public CMU May 7, 2015 Enron release is large and the project must not commit the full corpus before the ingestion pipeline is proven. The normalized record also needs a stable identity and synthetic permission metadata for later controlled experiments.

### Decision
Use the exact CMU archive URL `https://www.cs.cmu.edu/~enron/enron_mail_20150507.tar.gz` as the source of truth. The CLI streams the gzip tar archive for the first configurable number of unique messages, or supports an explicit full-archive download for offline processing. Parse RFC 2822/MIME files into JSONL records, derive IDs from Message-ID or normalized content, and deduplicate by ID with lexicographic source-path tie-breaking. Attach deterministic synthetic RBAC fields derived from mailbox names.

### Alternatives
Commit a corpus subset without an acquisition path, use a processed third-party mirror as the primary source, or download and retain the full archive during every development run.

### Consequences
Fresh development runs are small and reproducible, while the full public source remains available for later scale-up. The checked-in sample contains normalized email content but no retrieval labels. Synthetic roles are test metadata only and must never be described as Enron's historical permissions.

## ADR-003 — Use a modular SentenceTransformer plus exact NumPy dense baseline
**Status:** accepted  
**Date:** 2026-08-16

### Context
Phase 02 needs a measurable dense baseline while leaving room for BM25 and hybrid retrieval in later phases. The configured model strategy specifies `sentence-transformers/all-MiniLM-L6-v2`.

### Decision
Use the configured SentenceTransformer model for embeddings and an exact cosine-similarity NumPy index for the 500-email development corpus. Keep document preparation, embedding, index storage, retrieval, evaluation, prompt construction, and generation as separate injectable components. Represent each email as one bounded retrieval document so its stable `email_id` is preserved without introducing chunk-to-email aggregation in this phase.

### Alternatives
Use a vector database before measuring the baseline, replace the configured embedding model, or couple retrieval directly to the future hybrid implementation.

### Consequences
The baseline is easy to inspect, persist, test with fake embedders, and compare against later retrievers. Exact search is appropriate for the current development size; a larger production index can replace `DenseIndex` behind the same interface. No compatibility change was needed for the configured embedding model.

## ADR-004 — Select RRF hybrid retrieval for the Phase 03 default
**Status:** accepted
**Date:** 2026-08-16

### Context
Phase 03 requires a sparse BM25 baseline and a hybrid comparison without changing the dense baseline or the 20-question ground truth. Enron messages contain exact names, abbreviations, and project terms that may favor sparse matching on some questions.

### Decision
Use `rank-bm25` with deterministic case-folded word tokens and BM25 `k1=1.5`, `b=0.75`. Fuse the independent BM25 and dense rankings with Reciprocal Rank Fusion using one-based ranks, rank constant `60`, and candidate depth `20`. Select the hybrid composition as the default retrieval strategy for the next phase because, on exactly the same 500 emails and 20 questions, it improves MRR@5 to `0.8667` versus BM25 `0.8017` and dense `0.7267`. Do not claim a HitRate gain: hybrid and dense are both `0.9500`, while BM25 is `1.0000`.

### Alternatives
Keep dense as the default because it is the original baseline, select BM25 because it has the highest HitRate@5, or tune RRF until it wins every query. The latter would violate the requirement to preserve the ground truth and report failures honestly.

### Consequences
The hybrid retriever is modular and independently testable, while dense and BM25 remain selectable for ablation. The result is evidence for this fixed development corpus and query set only; reranking and authorization are intentionally deferred.

## ADR-005 — Enable cross-encoder reranking after Phase 04 evaluation
**Status:** accepted
**Date:** 2026-08-16

### Context
Phase 03 selected hybrid retrieval for its best MRR@5, but the hybrid output can place a relevant email below other candidates. Phase 04 evaluates whether a wider candidate set and a cross-encoder improve relevant-email rank on the same corpus and ground truth.

### Decision
Use the configured `cross-encoder/ms-marco-MiniLM-L-6-v2` through the `sentence-transformers` CrossEncoder API. Generate 20 candidates with hybrid retrieval, score the original query against each original retrieval document, and return five results while preserving the stable email ID, original retrieval score/rank, and reranker score. Enable Hybrid + reranker as the default because it improves HitRate@5 from `0.9500` to `1.0000` and MRR@5 from `0.8667` to `0.9500` on 500 emails and 20 questions.

### Alternatives
Keep hybrid because reranking adds latency, use BM25 because it had the best Phase 03 HitRate, or select a different reranker without compatibility evidence. None is justified by the Phase 04 result.

### Consequences
Reranking is a separately injectable component with deterministic tie handling and test doubles, and the original retrieval evidence remains inspectable. The measured mean added reranking time was 44.94 ms per question in the local evaluation run. Authorization is still intentionally deferred to Phase 05, so this decision does not authorize unrestricted retrieval in a production system.
