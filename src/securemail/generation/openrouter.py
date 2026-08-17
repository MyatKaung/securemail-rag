"""OpenRouter generation client with environment-only secret handling."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from securemail.config import (
    PROJECT_ROOT,
    ConfigurationError,
    OpenRouterSettings,
    load_openrouter_settings,
    load_yaml_config,
)

from .prompts import GROUNDED_SYSTEM_PROMPT


@dataclass(frozen=True)
class OpenRouterGenerationConfig:
    """Non-secret generation controls loaded from ``config/models.yaml``."""

    temperature: float = 0.1
    max_tokens: int = 500
    reasoning_effort: str = "none"


def load_generation_config(config_path: str | None = None) -> OpenRouterGenerationConfig:
    """Load and validate the production generation controls."""

    path = config_path or str(PROJECT_ROOT / "config" / "models.yaml")
    config = load_yaml_config(path).get("llm", {})
    if not isinstance(config, dict):
        raise ConfigurationError("config/models.yaml llm section must be a mapping")
    try:
        temperature = float(config.get("temperature", 0.1))
        max_tokens = int(config.get("max_tokens", 500))
        reasoning_effort = str(config.get("reasoning_effort", "none")).strip().lower()
    except (TypeError, ValueError) as exc:
        raise ConfigurationError("Invalid generation controls in config/models.yaml") from exc
    if not 0 <= temperature <= 2:
        raise ConfigurationError("llm.temperature must be between 0 and 2")
    if max_tokens <= 0:
        raise ConfigurationError("llm.max_tokens must be positive")
    if reasoning_effort not in {"none", "low", "medium", "high"}:
        raise ConfigurationError("llm.reasoning_effort must be none, low, medium, or high")
    return OpenRouterGenerationConfig(temperature, max_tokens, reasoning_effort)


class OpenRouterGenerationClient:
    """Thin injectable client for the configured OpenRouter chat model."""

    def __init__(
        self,
        settings: OpenRouterSettings | None = None,
        *,
        client: Any | None = None,
        generation_config: OpenRouterGenerationConfig | None = None,
    ):
        self.settings = settings or load_openrouter_settings()
        self.generation_config = generation_config or load_generation_config()
        if not self.settings.api_key and client is None:
            raise ConfigurationError(
                "OPENROUTER_API_KEY is required to create the OpenRouter client"
            )
        if client is not None:
            self._client = client
        else:
            try:
                from openai import OpenAI
            except ImportError as exc:
                raise RuntimeError("openai is required for OpenRouter generation") from exc
            headers = {}
            if self.settings.site_url:
                headers["HTTP-Referer"] = self.settings.site_url
            if self.settings.app_name:
                headers["X-Title"] = self.settings.app_name
            self._client = OpenAI(
                api_key=self.settings.api_key,
                base_url=self.settings.base_url,
                default_headers=headers or None,
            )

    def __repr__(self) -> str:
        return (
            "OpenRouterGenerationClient("
            f"base_url={self.settings.base_url!r}, model={self.settings.model!r})"
        )

    def generate(
        self,
        prompt: str,
        *,
        system_prompt: str = GROUNDED_SYSTEM_PROMPT,
        temperature: float | None = None,
        max_tokens: int | None = None,
        reasoning_effort: str | None = None,
    ) -> str:
        """Generate one grounded answer; the API key never enters the prompt/log data."""

        if not prompt.strip():
            raise ValueError("prompt must not be empty")
        effective_reasoning = (
            self.generation_config.reasoning_effort
            if reasoning_effort is None
            else reasoning_effort.strip().lower()
        )
        if effective_reasoning not in {"none", "low", "medium", "high"}:
            raise ValueError("reasoning_effort must be none, low, medium, or high")
        response = self._client.chat.completions.create(
            model=self.settings.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=(
                self.generation_config.temperature
                if temperature is None
                else temperature
            ),
            max_tokens=(self.generation_config.max_tokens if max_tokens is None else max_tokens),
            extra_body={"reasoning": {"effort": effective_reasoning}},
        )
        content = response.choices[0].message.content
        return content.strip() if isinstance(content, str) else ""
