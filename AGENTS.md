# AGENTS.md — Codex Operating Contract

## Mission
Build **SecureMail RAG**, a permission-aware enterprise email RAG system over the publicly available Enron Email Dataset.

The project must optimize for:
1. LLM Zoomcamp rubric compliance.
2. Reproducibility.
3. Measurable retrieval quality.
4. Permission-safe retrieval.
5. Small, testable increments.
6. Optional advanced RAG features only when they improve evaluation or have a documented production rationale.

## Source of Truth
Before modifying code, read:
- `project_spec.md`
- `architecture.md`
- `implementation_plan.md`
- `docs/rubric_compliance.md`
- the current `tasks/phase_*.md`

If files conflict, priority is:
1. `AGENTS.md`
2. `project_spec.md`
3. `architecture.md`
4. current phase task
5. other docs

## Required Working Style
- Implement **one phase at a time**.
- Do not silently implement future phases.
- Inspect existing code before editing.
- Add or update tests with every functional change.
- Run relevant tests before declaring a phase complete.
- Preserve behavior during refactors.
- Keep provider/model configuration outside business logic.
- Never hard-code API keys.
- Never commit `.env`.
- Record non-trivial architecture decisions in `decisions.md`.
- Update `docs/rubric_compliance.md` when a rubric-relevant feature becomes verifiably complete.
- Prefer dependency injection for retrievers, rerankers, LLM clients, caches, and authorization policies.

## Security Invariants
- Authorization must be applied **before retrieval**, not only after retrieval.
- Unauthorized email content must never enter LLM context.
- Prompt instructions can never override authorization.
- All retrieval implementations must share the same authorization enforcement path.
- Security tests are mandatory for any change touching retrieval.

## Evaluation Invariants
Do not claim an approach is better without measured evidence.
Keep baselines available for evaluation:
- BM25
- dense retrieval
- hybrid retrieval
- hybrid + reranking

Optional techniques must be evaluated:
- query rewriting
- HyDE
- CRAG
- Self-RAG
- semantic caching

Disable optional features when they do not improve the chosen metric or production behavior.

## Model Provider
Generation model:
- Provider: OpenRouter
- Model slug: `qwen/qwen3.6-27b`
- Base URL: `https://openrouter.ai/api/v1`
- API key env var: `OPENROUTER_API_KEY`

The application must fail clearly when the key is required but absent.

## Definition of Done for a Phase
A phase is complete only when:
1. Implementation is present.
2. Tests pass.
3. Evaluation is run where applicable.
4. Documentation is updated.
5. Relevant rubric items contain evidence.
6. No secret is committed.
7. The current phase checklist is updated truthfully.

## Refactoring Rules
- Do not combine large refactors with feature additions.
- Refactor only after baseline tests exist.
- Preserve public interfaces unless a documented architecture decision approves a change.
- Prefer focused modules.
- Avoid duplicated retrieval/security logic.
- Do not optimize prematurely.

## Final Audit
Before submission, execute the instructions in `tasks/rubric_audit.md`.
Produce `docs/rubric_audit_report.md` with PASS / PARTIAL / FAIL and repository evidence for each criterion.
