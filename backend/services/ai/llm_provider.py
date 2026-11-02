"""LLM provider interface and factory."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.config import settings


class LLMError(Exception):
    """Raised when the configured LLM provider cannot produce an answer."""


class LLMProvider(ABC):
    name: str = "provider"
    model: str = ""

    @abstractmethod
    def generate(self, system: str, prompt: str) -> str:
        """Return generated text, raising LLMError on failure."""

    def label(self) -> str:
        return f"{self.name}:{self.model}" if self.model else self.name


def get_provider() -> LLMProvider | None:
    """Build the configured provider, or None when AI is disabled/misconfigured."""
    provider = (settings.ai_provider or "none").strip().lower()
    if provider in {"", "none", "off", "disabled"}:
        return None
    if provider == "ollama":
        from services.ai.ollama_provider import OllamaProvider

        return OllamaProvider(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
            timeout=settings.ai_timeout_seconds,
        )
    if provider in {"openrouter", "open-router", "open_router"}:
        if not settings.openrouter_api_key.strip():
            return None
        from services.ai.openrouter_provider import OpenRouterProvider

        return OpenRouterProvider(
            api_key=settings.openrouter_api_key.strip(),
            model=settings.openrouter_model,
            base_url=settings.openrouter_base_url,
            site_url=settings.openrouter_site_url.strip(),
            app_name=settings.app_name,
            timeout=settings.ai_timeout_seconds,
        )
    if provider == "cloud":
        if not settings.cloud_llm_api_key:
            return None
        from services.ai.cloud_provider import CloudProvider

        return CloudProvider(
            base_url=settings.cloud_llm_base_url,
            api_key=settings.cloud_llm_api_key,
            model=settings.cloud_llm_model,
            timeout=settings.ai_timeout_seconds,
        )
    return None
