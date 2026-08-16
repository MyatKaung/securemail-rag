# Permission-Aware RAG

Phase 05 implements pre-retrieval authorization using the deterministic
`synthetic-enron-overlay-v1` metadata from Phase 01. This overlay is an
experiment-only policy and does not represent Enron's historical permissions.

## Principal schema

Every authorization decision receives an explicit `PrincipalContext`:

```text
role, department, access_level, resource_scope
```

Supported access levels are `standard < department < global`. The policy is:

1. `admin` principals may retrieve every synthetic resource.
2. `global` resources require both global access level and global scope.
3. `shared` resources require sufficient access and shared/global scope.
4. Department resources require matching department, sufficient access, and a
   department/global scope.

The query text, including identity claims or instructions to ignore policy, is
never used to grant access.

## Enforcement boundary

The same `AuthorizationFilter` is applied before candidate scoring for dense
and BM25. Hybrid propagates it to both branches, and hybrid + reranker receives
only the filtered candidates. Grounded prompt construction performs a second
check and raises `AuthorizationError` if unauthorized evidence is supplied.
Therefore restricted content is blocked before reranking and before LLM prompt
construction.

The no-filter retriever remains available only as an intentionally insecure
evaluation baseline. It is not the permission-aware path.

## Evaluation evidence

The permission dataset contains 24 grounded cases over the current 500-email
corpus, including same-department/admin/global, cross-department, access-level,
shared-scope, and adversarial prompt cases.

| Metric | No filter | Pre-retrieval filter |
| --- | ---: | ---: |
| Unauthorized Retrieval Rate | 1.0000 | 0.0000 |
| Authorization decision accuracy | — | 1.0000 |
| Authorized HitRate@5 | — | 1.0000 |
| Authorized MRR@5 | — | 0.9167 |

Machine-readable evidence is in
`evals/results/phase05_permission.json`. The four adversarial cases all had
unauthorized no-filter retrieval and zero unauthorized filtered retrieval.
