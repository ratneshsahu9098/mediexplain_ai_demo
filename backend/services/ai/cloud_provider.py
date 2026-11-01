"""OpenAI-compatible hosted LLM provider (e.g. Gemini's OpenAI endpoint)."""

from __future__ import annotations

import httpx

from services.ai.llm_provider import LLMError, LLMProvider


class CloudProvider(LLMProvider):
    name = "cloud"

    def __init__(self, base_url: str, api_key: str, model: str, timeout: int = 120) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

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
        headers = {"Authorization": f"Bearer {self.api_key}"}
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, json=body, headers=headers)
        except httpx.HTTPError as exc:
            raise LLMError("The cloud AI provider is not reachable.") from exc

        if response.status_code != 200:
            raise LLMError(f"Cloud AI provider returned HTTP {response.status_code}.")
        try:
            text = response.json()["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise LLMError("Cloud AI provider returned an invalid response.") from exc
        text = (text or "").strip()
        if not text:
            raise LLMError("Cloud AI provider returned an empty response.")
        return text
