from pathlib import Path

import pytest

from securemail.config import (
    ConfigurationError,
    load_application_settings,
    load_openrouter_settings,
    settings_for_json,
)


def write_env(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


def test_load_openrouter_settings_reads_dotenv_and_masks_secret(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_BASE_URL", raising=False)
    monkeypatch.delenv("OPENROUTER_MODEL", raising=False)
    env_file = write_env(
        tmp_path / ".env",
        "OPENROUTER_API_KEY=test-secret\n"
        "OPENROUTER_BASE_URL=https://example.test/v1\n"
        "OPENROUTER_MODEL=test/model\n",
    )

    settings = load_openrouter_settings(env_file=env_file)

    assert settings.api_key == "test-secret"
    assert settings.base_url == "https://example.test/v1"
    assert settings.model == "test/model"
    assert "test-secret" not in repr(settings)
    assert "test-secret" not in settings_for_json(settings)


def test_environment_takes_precedence_over_dotenv(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "environment-secret")
    env_file = write_env(tmp_path / ".env", "OPENROUTER_API_KEY=dotenv-secret\n")

    settings = load_openrouter_settings(env_file=env_file)

    assert settings.api_key == "environment-secret"


def test_missing_required_key_fails_clearly(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    with pytest.raises(ConfigurationError, match="OPENROUTER_API_KEY is required"):
        load_openrouter_settings(env_file=tmp_path / ".env")


def test_invalid_base_url_fails_validation(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    env_file = write_env(
        tmp_path / ".env",
        "OPENROUTER_API_KEY=test-secret\nOPENROUTER_BASE_URL=not-a-url\n",
    )

    with pytest.raises(ConfigurationError, match=r"absolute HTTP\(S\) URL"):
        load_openrouter_settings(env_file=env_file)


def test_load_application_settings_loads_both_yaml_files(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "app.yaml").write_text("app:\n  name: Test\n", encoding="utf-8")
    (config_dir / "models.yaml").write_text("llm:\n  provider: openrouter\n", encoding="utf-8")
    env_file = write_env(tmp_path / ".env", "OPENROUTER_API_KEY=test-secret\n")

    settings = load_application_settings(config_dir, env_file)

    assert settings.app == {"app": {"name": "Test"}}
    assert settings.models == {"llm": {"provider": "openrouter"}}
