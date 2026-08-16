# Phase 06 — Generation + LLM Evaluation

- [x] Implement basic grounded prompt (`basic_grounded_v1`).
- [x] Implement structured grounded/citation/refusal prompt (`structured_grounded_v1`).
- [x] Evaluate both approaches with live Qwen responses.
- [x] Select the better approach from measured live results.
- [x] Ensure unauthorized content cannot enter context; fail closed before prompt construction/provider calls.

## Evidence and blocker

The 20-case dataset is `evals/datasets/generation_ground_truth.phase06.json`.
Offline unit and integration coverage verifies prompt construction, response
parsing, deterministic scoring, and the permission-aware hybrid + reranker to
generation boundary. `uv run pytest -q` passes 58 tests and Ruff passes.

The live evaluation completed with the configured OpenRouter endpoint and model.
`evals/results/phase06_generation.json` records 40 successful calls, both
approach results, the deterministic scoring configuration, and the selected
default. Basic grounded scored `0.4875` overall versus `0.4500` for structured
grounded. No OpenRouter key is stored in Git or in evaluation artifacts.
