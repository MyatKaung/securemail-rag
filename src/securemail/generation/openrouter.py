"""OpenRouter generation client with environment-only secret handling."""

from __future__ import annotations

from typing import Any

from securemail.config import ConfigurationError, OpenRouterSettings, load_openrouter_settings

from .prompts import GROUNDED_SYSTEM_PROMPT


class OpenRouterGenerationClient:
    """Thin injectable client for the configured OpenRouter chat model."""

    def __init__(
        self,
        settings: OpenRouterSettings | None = None,
        *,
        client: Any | None = None,
    ):
        self.settings = settings or load_openrouter_settings()
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
        temperature: float = 0.1,
        max_tokens: int = 800,
    ) -> str:
        """Generate one grounded answer; the API key never enters the prompt/log data."""

        if not prompt.strip():
            raise ValueError("prompt must not be empty")
        response = self._client.chat.completions.create(
            model=self.settings.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        content = response.choices[0].message.content
        return content.strip() if isinstance(content, str) else ""
