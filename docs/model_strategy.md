# Model Strategy

## Generation
Provider: OpenRouter  
Model: `qwen/qwen3.6-27b`

Configuration comes from environment variables and `config/models.yaml`.

## Why One Primary Model
The assignment should spend evaluation effort on:
- retrieval strategies
- permission safety
- prompt/generation approach

Do not create unnecessary multi-model complexity.

## LLM Evaluation
Full evaluation compares generation approaches/prompts rather than many model
providers. Phase 06 defines two independently selectable, versioned strategies:
`basic_grounded_v1` and `structured_grounded_v1`. Both receive only evidence
after the Phase 05 authorization filter and require source email IDs. The
structured strategy additionally separates Answer, Uncertainty, and Sources
sections and refuses unsupported or restricted requests.

The Phase 06 evaluation rubric is deterministic and non-LLM: groundedness,
answer relevance, citation correctness, and refusal correctness are scored from
case-specific expected terms/source IDs and the returned structure. This keeps
the generation and judge prompts separate and makes the first evaluation
reproducible. On the 20-question evaluation, Basic grounded scored `0.4875`
overall versus `0.4500` for Structured grounded, so `basic_grounded_v1` is the
configured default.

The opt-in smoke command is:
`PYTHONPATH=src uv run python -m securemail.generation.smoke`.
It reads `.env`, performs one live request, and is not part of the default test
suite.

## Embeddings
Baseline:
`sentence-transformers/all-MiniLM-L6-v2`

Keep the embedding interface swappable so a stronger model can be tested later.
Phase 02 uses this configured baseline unchanged over a 500-email development
corpus. The embedding model is loaded only by the dense indexing/evaluation path;
tests inject a fake embedder and never download model weights.

## Reranker
Baseline:
`cross-encoder/ms-marco-MiniLM-L-6-v2`

## Rule
Do not change the production model based on intuition alone. Record model changes in `decisions.md`.
