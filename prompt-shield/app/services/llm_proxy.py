"""LLM proxy service - forwards sanitized prompts to LLM providers."""
from __future__ import annotations

from abc import ABC, abstractmethod

from app.config import get_settings


class BaseLLMProxy(ABC):
    """Abstract base for LLM proxy backends."""

    @abstractmethod
    def complete(self, prompt: str, system_prompt: str | None = None) -> str:
        """Send a prompt to the LLM and return the response."""


class MockLLMProxy(BaseLLMProxy):
    """Mock LLM that echoes a canned response for testing."""

    def complete(self, prompt: str, system_prompt: str | None = None) -> str:
        return (
            f"[Mock LLM Response] Received prompt of {len(prompt)} characters. "
            f"This is a placeholder response from the mock LLM provider."
        )


def get_llm_proxy() -> BaseLLMProxy:
    """Factory that returns the configured LLM proxy backend."""
    settings = get_settings()
    if settings.llm_provider == "mock":
        return MockLLMProxy()
    raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}. Use 'mock' for local testing.")
