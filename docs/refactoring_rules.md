# Refactoring Rules

- Refactoring must preserve observable behavior.
- Tests must pass before and after.
- Do not mix broad refactors with feature work.
- Retrieval implementations must conform to a shared interface.
- Authorization must remain centralized and impossible to bypass.
- Provider configuration must remain outside business logic.
- Prefer dependency injection.
- Remove duplication only after tests establish behavior.
- Record material architecture changes in `decisions.md`.
