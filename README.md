# SecureMail RAG

Permission-aware enterprise email RAG over the Enron Email Dataset.

> Status: Phases 00–07 implemented; Phases 08–10 remain.

## Start Here for Codex
For current development, read in order:
1. `AGENTS.md`
2. `project_spec.md`
3. `architecture.md`
4. `implementation_plan.md`
5. `docs/rubric_compliance.md`
6. `tasks/phase_07_interface.md`

Implement only the current phase; later phases remain intentionally disabled.

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

## Run the interface

```bash
PYTHONPATH=src uv run uvicorn securemail.api.app:app --reload
```

Then open <http://127.0.0.1:8000/>. The interface uses the synthetic RBAC
overlay documented in [docs/interface.md](docs/interface.md); it is not a
reconstruction of Enron's historical permissions. `GET /health` is available
without loading models or requiring an OpenRouter key.

## Project Principle
A secure enterprise RAG system must decide both:
1. what is relevant, and
2. what the user is authorized to retrieve.
