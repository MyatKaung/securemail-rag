from types import SimpleNamespace

import pytest

from securemail.config import ConfigurationError, OpenRouterSettings
from securemail.generation import (
    GROUNDED_SYSTEM_PROMPT,
    OpenRouterGenerationClient,
    build_grounded_prompt,
)
from securemail.retrieval import DenseSearchResult, RetrievalDocument


class FakeCompletions:
    def __init__(self):
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="Grounded answer [email-1]"))]
        )


class FakeClient:
    def __init__(self):
        self.chat = SimpleNamespace(completions=FakeCompletions())


def result(email_id="email-1"):
    return DenseSearchResult(
        email_id=email_id,
        score=0.91,
        document=RetrievalDocument(
            email_id=email_id,
            text="Subject: Budget review\nBody: Please review the budget.",
            metadata={},
        ),
    )


def test_grounded_prompt_contains_only_selected_ids_and_instructions():
    prompt = build_grounded_prompt("What is the budget topic?", [result()])

    assert "email-1" in prompt
    assert "Please review the budget." in prompt
    assert "only this evidence" in prompt
    assert "insufficient" in prompt


def test_openrouter_client_uses_configured_model_without_live_call():
    fake = FakeClient()
    settings = OpenRouterSettings(
        api_key="test-secret",
        base_url="https://openrouter.example/v1",
        model="test/model",
    )
    client = OpenRouterGenerationClient(settings, client=fake)

    answer = client.generate("Question with evidence")

    call = fake.chat.completions.calls[0]
    assert answer == "Grounded answer [email-1]"
    assert call["model"] == "test/model"
    assert call["messages"][0]["content"] == GROUNDED_SYSTEM_PROMPT
    assert call["temperature"] == 0.1
    assert call["max_tokens"] == 500
    assert call["extra_body"] == {"reasoning": {"effort": "none"}}
    assert "test-secret" not in repr(client)


def test_openrouter_client_passes_environment_settings_to_openai_without_call(monkeypatch):
    import openai

    captured = {}

    class FakeOpenAI:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr(openai, "OpenAI", FakeOpenAI)
    settings = OpenRouterSettings(
        api_key="test-secret",
        base_url="https://openrouter.example/v1",
        model="test/model",
        site_url="https://securemail.example",
        app_name="SecureMail test",
    )

    OpenRouterGenerationClient(settings)

    assert captured["api_key"] == "test-secret"
    assert captured["base_url"] == "https://openrouter.example/v1"
    assert captured["default_headers"] == {
        "HTTP-Referer": "https://securemail.example",
        "X-Title": "SecureMail test",
    }


def test_openrouter_client_requires_a_key_for_real_client():
    settings = OpenRouterSettings(api_key="", base_url="https://openrouter.example/v1")

    with pytest.raises(ConfigurationError, match="OPENROUTER_API_KEY"):
        OpenRouterGenerationClient(settings)
