"""OpenRouter provider (OpenAI-compatible chat completions)."""

from __future__ import annotations

import httpx

from services.ai.llm_provider import LLMError, LLMProvider

DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"


class OpenRouterProvider(LLMProvider):
    name = "openrouter"

    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str = DEFAULT_BASE_URL,
        site_url: str = "",
        app_name: str = "",
        timeout: int = 120,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = (base_url or DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout

        # OpenRouter recommends these attribution headers. They are optional,
        # but they make usage easier to identify in the OpenRouter dashboard.
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        if site_url:
            self.headers["HTTP-Referer"] = site_url
        if app_name:
            self.headers["X-Title"] = app_name

    def generate(self, system: str, prompt: str) -> str:
        url = f"{self.base_url}/chat/completions"
        body = {
            "model": self.model,
            "temperature": 0.2,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        }
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, json=body, headers=self.headers)
        except httpx.HTTPError as exc:
            raise LLMError("OpenRouter is not reachable.") from exc

        if response.status_code == 401:
            raise LLMError("OpenRouter rejected the API key.")
        if response.status_code == 402:
            raise LLMError("The OpenRouter account has insufficient credits.")
        if response.status_code == 429:
            raise LLMError("OpenRouter rate limit reached; try again shortly.")
        if response.status_code != 200:
            raise LLMError(f"OpenRouter returned HTTP {response.status_code}.")

        try:
            text = response.json()["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise LLMError("OpenRouter returned an invalid response.") from exc
        text = (text or "").strip()
        if not text:
            raise LLMError("OpenRouter returned an empty response.")
        return text
