"""Local Ollama provider."""

from __future__ import annotations

import httpx

from services.ai.llm_provider import LLMError, LLMProvider


class OllamaProvider(LLMProvider):
    name = "ollama"

    def __init__(self, base_url: str, model: str, timeout: int = 120) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def generate(self, system: str, prompt: str) -> str:
        url = f"{self.base_url}/api/generate"
        body = {
            "model": self.model,
            "system": system,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.2, "num_predict": 500},
        }
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, json=body)
        except httpx.HTTPError as exc:
            raise LLMError(f"Ollama is not reachable at {self.base_url}.") from exc

        if response.status_code != 200:
            raise LLMError(f"Ollama returned HTTP {response.status_code}.")
        try:
            text = (response.json().get("response") or "").strip()
        except ValueError as exc:
            raise LLMError("Ollama returned an invalid response.") from exc
        if not text:
            raise LLMError("Ollama returned an empty response.")
        return text
