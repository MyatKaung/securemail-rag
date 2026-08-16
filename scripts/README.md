# Scripts

Phase-specific scripts belong here. Do not add the full dataset to Git.

Phase 01 acquisition and normalization is exposed by the package CLI:

```bash
PYTHONPATH=src uv run --extra dev python -m securemail.ingestion.cli --help
```

The default development limit is 25 unique messages. See
`docs/ingestion.md` for the exact source URL and offline-download path.
