from pathlib import Path

import pytest

from securemail.api.service import validate_runtime_assets
from securemail.config import ConfigurationError


def test_missing_runtime_data_fails_with_acquisition_guidance(tmp_path: Path) -> None:
    with pytest.raises(
        ConfigurationError, match=r"required runtime data/config is missing.*make ingest"
    ):
        validate_runtime_assets(tmp_path / "missing.jsonl")


def test_docker_and_compose_scope_is_local_and_secret_safe() -> None:
    root = Path(__file__).resolve().parents[2]
    dockerfile = (root / "Dockerfile").read_text(encoding="utf-8")
    compose = (root / "docker-compose.yml").read_text(encoding="utf-8")
    dockerignore = (root / ".dockerignore").read_text(encoding="utf-8")

    assert "COPY .env " not in dockerfile
    assert "OPENROUTER_API_KEY" in compose
    assert "healthcheck" in compose
    assert "postgres" not in compose
    assert ".env" in dockerignore
    assert "data/raw" in dockerignore
    assert "data/sample" not in dockerignore


def test_makefile_exposes_reproducible_workflow_targets() -> None:
    root = Path(__file__).resolve().parents[2]
    makefile = (root / "Makefile").read_text(encoding="utf-8")

    for target in ("setup:", "test:", "lint:", "ingest:", "eval:", "up:", "down:"):
        assert target in makefile
