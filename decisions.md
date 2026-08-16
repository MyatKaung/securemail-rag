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
