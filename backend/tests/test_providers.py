"""Tests for AI provider selection and the OpenRouter client."""

from __future__ import annotations

import pytest

from app.config import settings
from services.ai import openrouter_provider
from services.ai.llm_provider import LLMError, get_provider
from services.ai.openrouter_provider import OpenRouterProvider


class _FakeResponse:
    def __init__(self, status_code: int = 200, payload: dict | None = None) -> None:
        self.status_code = status_code
        self._payload = payload

    def json(self) -> dict:
        if self._payload is None:
            raise ValueError("no JSON body")
        return self._payload


class _FakeClient:
    response = _FakeResponse()
    calls: dict = {}

    def __init__(self, timeout: int | None = None) -> None:
        self.timeout = timeout

    def __enter__(self) -> "_FakeClient":
        return self

    def __exit__(self, *args) -> bool:
        return False

    def post(self, url: str, json: dict | None = None, headers: dict | None = None) -> _FakeResponse:
        type(self).calls = {
            "url": url,
            "json": json,
            "headers": headers,
            "timeout": self.timeout,
        }
        return type(self).response


@pytest.fixture
def install_fake_client(monkeypatch):
    def install(response: _FakeResponse) -> None:
        _FakeClient.response = response
        _FakeClient.calls = {}
        monkeypatch.setattr(openrouter_provider.httpx, "Client", _FakeClient)

    return install


def test_openrouter_requires_api_key(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "openrouter")
    monkeypatch.setattr(settings, "openrouter_api_key", "   ")
    assert get_provider() is None


def test_openrouter_provider_selected_from_settings(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "openrouter")
    monkeypatch.setattr(settings, "openrouter_api_key", "sk-or-test")
    monkeypatch.setattr(settings, "openrouter_model", "meta-llama/llama-3.1-8b-instruct")

    provider = get_provider()

    assert isinstance(provider, OpenRouterProvider)
    assert provider.name == "openrouter"
    assert provider.label() == "openrouter:meta-llama/llama-3.1-8b-instruct"


def test_generate_posts_openai_compatible_request(install_fake_client):
    install_fake_client(
        _FakeResponse(payload={"choices": [{"message": {"content": "  Grounded answer.  "}}]})
    )
    provider = OpenRouterProvider(
        api_key="sk-or-test",
        model="openrouter/auto",
        site_url="http://localhost:5173",
        app_name="MediExplain AI",
        timeout=42,
    )

    assert provider.generate("system prompt", "user question") == "Grounded answer."

    calls = _FakeClient.calls
    assert calls["url"] == "https://openrouter.ai/api/v1/chat/completions"
    assert calls["timeout"] == 42
    assert calls["headers"]["Authorization"] == "Bearer sk-or-test"
    assert calls["headers"]["HTTP-Referer"] == "http://localhost:5173"
    assert calls["headers"]["X-Title"] == "MediExplain AI"
    assert calls["json"]["model"] == "openrouter/auto"
    assert calls["json"]["messages"] == [
        {"role": "system", "content": "system prompt"},
        {"role": "user", "content": "user question"},
    ]


@pytest.mark.parametrize(
    ("status_code", "expected"),
    [
        (401, "API key"),
        (402, "credits"),
        (429, "rate limit"),
        (500, "HTTP 500"),
    ],
)
def test_openrouter_error_messages(install_fake_client, status_code, expected):
    install_fake_client(_FakeResponse(status_code=status_code))
    provider = OpenRouterProvider(api_key="sk-or-test", model="openrouter/auto")

    with pytest.raises(LLMError, match=expected):
        provider.generate("system", "question")
