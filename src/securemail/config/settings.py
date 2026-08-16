"""Configuration loading and validation for the Phase 00 application skeleton.

Secrets are read from the process environment or a local dotenv file. YAML files
contain non-secret configuration and are returned as mappings so later phases can
introduce typed settings without coupling business logic to a provider.
"""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml
from dotenv import dotenv_values

DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "qwen/qwen3.6-27b"
PROJECT_ROOT = Path(__file__).resolve().parents[3]


class ConfigurationError(ValueError):
    """Raised when required application configuration is missing or invalid."""


@dataclass(frozen=True)
class OpenRouterSettings:
    """Validated OpenRouter settings.

    ``repr`` intentionally masks the API key so accidental logging does not
    expose credentials. The key remains available through the normal attribute
    for the client that needs to authenticate a request.
    """

    api_key: str
    base_url: str = DEFAULT_BASE_URL
    model: str = DEFAULT_MODEL
    site_url: str = ""
    app_name: str = "SecureMail RAG"

    def __repr__(self) -> str:
        return (
            "OpenRouterSettings(api_key='***', "
            f"base_url={self.base_url!r}, model={self.model!r}, "
            f"site_url={self.site_url!r}, app_name={self.app_name!r})"
        )


@dataclass(frozen=True)
class ApplicationSettings:
    """Combined Phase 00 settings with non-secret YAML configuration."""

    openrouter: OpenRouterSettings
    app: Mapping[str, Any]
    models: Mapping[str, Any]


def _read_dotenv_values(env_file: Path | None) -> Mapping[str, str]:
    if env_file is None or not env_file.exists():
        return {}
    return {key: value for key, value in dotenv_values(env_file).items() if value is not None}


def _setting_value(name: str, dotenv_data: Mapping[str, str], default: str) -> str:
    value = os.getenv(name)
    if value is None:
        value = dotenv_data.get(name, default)
    return value.strip()


def _validate_base_url(base_url: str) -> None:
    parsed = urlparse(base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ConfigurationError("OPENROUTER_BASE_URL must be an absolute HTTP(S) URL")


def load_openrouter_settings(
    env_file: str | Path | None = None,
    *,
    require_api_key: bool = True,
) -> OpenRouterSettings:
    """Load and validate OpenRouter settings without mutating the environment.

    Environment variables take precedence over values in ``env_file``. The
    default file is the project ``.env`` when present. Set
    ``require_api_key=False`` for commands that only need to inspect config.
    """

    dotenv_path = PROJECT_ROOT / ".env" if env_file is None else Path(env_file)
    dotenv_data = _read_dotenv_values(dotenv_path)
    api_key = _setting_value("OPENROUTER_API_KEY", dotenv_data, "")
    base_url = _setting_value("OPENROUTER_BASE_URL", dotenv_data, DEFAULT_BASE_URL)
    model = _setting_value("OPENROUTER_MODEL", dotenv_data, DEFAULT_MODEL)
    site_url = _setting_value("OPENROUTER_SITE_URL", dotenv_data, "")
    app_name = _setting_value("OPENROUTER_APP_NAME", dotenv_data, "SecureMail RAG")

    if require_api_key and not api_key:
        raise ConfigurationError(
            "OPENROUTER_API_KEY is required to use the OpenRouter generation client"
        )
    if not base_url:
        raise ConfigurationError("OPENROUTER_BASE_URL must not be empty")
    _validate_base_url(base_url)
    if not model:
        raise ConfigurationError("OPENROUTER_MODEL must not be empty")

    return OpenRouterSettings(
        api_key=api_key,
        base_url=base_url,
        model=model,
        site_url=site_url,
        app_name=app_name,
    )


def load_yaml_config(path: str | Path) -> dict[str, Any]:
    """Load one non-secret YAML mapping and reject malformed top-level values."""

    config_path = Path(path)
    try:
        with config_path.open(encoding="utf-8") as handle:
            loaded = yaml.safe_load(handle)
    except OSError as exc:
        raise ConfigurationError(f"Unable to read config file: {config_path}") from exc
    except yaml.YAMLError as exc:
        raise ConfigurationError(f"Invalid YAML in config file: {config_path}") from exc

    if loaded is None:
        return {}
    if not isinstance(loaded, dict):
        raise ConfigurationError(f"Config file must contain a mapping: {config_path}")
    return loaded


def load_application_settings(
    config_dir: str | Path | None = None,
    env_file: str | Path | None = None,
    *,
    require_api_key: bool = True,
) -> ApplicationSettings:
    """Load the Phase 00 dotenv, app YAML, and model YAML configuration."""

    directory = PROJECT_ROOT / "config" if config_dir is None else Path(config_dir)
    return ApplicationSettings(
        openrouter=load_openrouter_settings(
            env_file=env_file,
            require_api_key=require_api_key,
        ),
        app=load_yaml_config(directory / "app.yaml"),
        models=load_yaml_config(directory / "models.yaml"),
    )


def settings_for_json(settings: OpenRouterSettings) -> str:
    """Return a safe JSON representation for diagnostics and tests."""

    return json.dumps(
        {
            "api_key": "***" if settings.api_key else "",
            "base_url": settings.base_url,
            "model": settings.model,
            "site_url": settings.site_url,
            "app_name": settings.app_name,
        },
        sort_keys=True,
    )
