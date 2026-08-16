# Deployment Strategy

## Decision
Local Docker Compose is mandatory.
Public cloud deployment is optional P3 bonus.

## Sequence
1. Core RAG passes.
2. Retrieval and LLM evals pass.
3. Permission tests pass.
4. Docker Compose works from a fresh clone.
5. README/setup is complete.
6. Only then attempt public cloud deployment.

## Cloud Constraint
Do not require a cloud GPU.
Generation uses OpenRouter.
Prefer a low-cost CPU/container deployment if cloud deployment is attempted.
