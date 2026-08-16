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

## ADR-006 — Enforce synthetic RBAC before every retrieval branch
**Status:** accepted
**Date:** 2026-08-16

### Context
Phase 05 must demonstrate that strong hybrid + reranker relevance can coexist with zero unauthorized retrieval. The Phase 01 overlay is synthetic and the current 500-record sample happens to contain global/admin-tagged resources, so permission cases must be explicit about that limitation.

### Decision
Use a `PrincipalContext` containing `role`, `department`, `access_level`, and `resource_scope`, and a versioned `SyntheticRBACPolicy`. Bind it through one `AuthorizationFilter` before dense or BM25 candidate scoring. Propagate the same filter through hybrid and reranking; reject unauthorized evidence again at grounded prompt construction. Keep the existing no-filter implementation only as an insecure evaluation baseline.

### Alternatives
Retrieve all documents and remove unauthorized results afterward, filter only the final top five, or trust prompt instructions to avoid disclosure. These violate the security invariant because restricted content could reach candidate or downstream context.

### Consequences
The filter is independently testable and all retrieval branches share the same policy path. On 24 permission cases, no-filter URR was `1.0000` and filtered URR was `0.0000`; authorization decision accuracy was `1.0000`. Authorized HitRate@5 was `1.0000` and MRR@5 `0.9167`. The policy is an experiment overlay, not a reconstruction of Enron permissions.

## ADR-007 — Use versioned grounded prompts with a deterministic first judge
**Status:** accepted
**Date:** 2026-08-16

### Context
Phase 06 needs two independently selectable generation approaches and a
reproducible comparison, while the evaluation corpus is small and the model
provider is paid. Generation must receive only Phase 05-authorized evidence.

### Decision
Implement `basic_grounded_v1` and `structured_grounded_v1` behind a common
generation pipeline. The pipeline requires a pre-retrieval authorization filter,
re-checks every result before prompt construction, and fails closed before the
provider call if an unauthorized document appears. Use a deterministic rubric
for groundedness, answer relevance, citation correctness, and refusal
correctness; do not use the generation prompt as a judge prompt.

Keep the configured OpenRouter model `qwen/qwen3.6-27b` and expose an opt-in
smoke/evaluation command. Select the default only from valid live results on the
same 20-case dataset.

### Alternatives

Use an LLM judge immediately, evaluate only one prompt, or select the
structured prompt by preference. These would make the first comparison harder
to reproduce or would claim an improvement without measured evidence.

### Consequences

The prompt and parser contracts are testable without network calls. The live
evaluation completed with 40 successful calls. Basic grounded scored `0.4875`
overall versus `0.4500` for structured grounded, so `basic_grounded_v1` is
selected as the default. The six insufficient-evidence cases had refusal
correctness of `0.1667` for basic and `0.3333` for structured; this tradeoff is
retained in the result artifact rather than hidden.

## ADR-008 — Serve a lazy FastAPI API with a dependency-free demo UI
**Status:** accepted
**Date:** 2026-08-16

### Context
Phase 07 needs a usable end-to-end interface without changing the measured
retrieval, authorization, or generation components. API tests must remain
offline and must not load models or require an OpenRouter key merely to check
health.

### Decision
Expose `GET /health`, `POST /query`, and a small HTML/JavaScript UI at `/` from
FastAPI. Build the production RAG service lazily on the first query so health
remains credential-independent. Create request-scoped dense, BM25, hybrid, and
reranked wrappers around the shared index/model objects so each request carries
its own `AuthorizationFilter`. Return answer text, source IDs, retrieval method,
evidence count, and refusal metadata, but never return email bodies.

Use explicit demo principals for finance, legal, shared/general, and admin. The
RBAC overlay is labeled synthetic in the UI and documentation. Do not add a
frontend dependency or expose credentials in browser state/code.

### Alternatives

Add Streamlit as a second application server, construct all models at module
import time, or return retrieved email text for UI convenience. These would add
unneeded dependency/startup coupling or weaken the interface security boundary.

### Consequences

The API and UI are easy to run locally and test with injected fakes. A live UI
smoke command is documented but remains manual; the default suite makes no paid
OpenRouter calls.
