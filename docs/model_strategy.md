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
Full evaluation can compare generation approaches/prompts rather than many model providers.

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
