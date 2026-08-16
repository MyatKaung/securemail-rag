# SecureMail RAG

Permission-aware enterprise email RAG over the Enron Email Dataset.

> Status: architecture/skeleton only. Implementation is intentionally staged through `tasks/`.

## Start Here for Codex
Read, in order:
1. `AGENTS.md`
2. `project_spec.md`
3. `architecture.md`
4. `implementation_plan.md`
5. `docs/rubric_compliance.md`
6. `tasks/phase_00_skeleton.md`

Then implement **only Phase 00**.

## Model
Generation uses Qwen3.6-27B through OpenRouter.

Copy:
```bash
cp .env.example .env
```

Then set:
```bash
OPENROUTER_API_KEY=...
```

Never commit `.env`.

## Project Principle
A secure enterprise RAG system must decide both:
1. what is relevant, and
2. what the user is authorized to retrieve.
