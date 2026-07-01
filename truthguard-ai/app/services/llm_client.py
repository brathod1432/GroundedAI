"""LLM client abstraction for TruthGuardAI.

Provides a thin interface so the rest of the pipeline never
imports OpenAI / Anthropic SDKs directly. The mock client returns
deterministic outputs suitable for development and testing.
"""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod

from app.config import settings

logger = logging.getLogger(__name__)


# ── Abstract interface ──────────────────────────────────────────────────

class BaseLLMClient(ABC):
    """Interface that every LLM backend must implement."""

    @abstractmethod
    def complete(self, system_prompt: str, user_prompt: str) -> str:
        """Return a text completion for the given prompts."""


# ── Mock implementation ────────────────────────────────────────────────

class MockLLMClient(BaseLLMClient):
    """Deterministic mock that echoes structured JSON-like responses.

    In production this would call OpenAI, Anthropic, or a local model.
    The mock is intentionally simple — it does *not* produce real
    intelligence, but it exercises the pipeline end-to-end.
    """

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        logger.debug("MockLLMClient called — returning placeholder completion.")
        # Return the user prompt wrapped as a simple JSON structure
        # so downstream parsing code has something to chew on.
        return json.dumps({
            "prompt": user_prompt[:200],
            "status": "mock_completion",
        })


# ── OpenAI placeholder ──────────────────────────────────────────────────

class OpenAILLMClient(BaseLLMClient):
    """OpenAI-backed client. Requires ``openai_api_key`` in settings.

    This is a *skeleton* — fill in with real API calls when ready.
    """

    def __init__(self) -> None:
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY must be set to use the OpenAI LLM client.")

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        # TODO: implement with ``openai.ChatCompletion.create``
        raise NotImplementedError("OpenAI integration pending — see roadmap v0.2")


# ── Factory ──────────────────────────────────────────────────────────────

def get_llm_client() -> BaseLLMClient:
    """Return the configured LLM client instance.

    Selection is driven by ``settings.llm_provider``. Unknown providers
    raise a ValueError so misconfiguration surfaces early.
    """
    providers = {
        "mock": MockLLMClient,
        "openai": OpenAILLMClient,
    }
    cls = providers.get(settings.llm_provider)
    if cls is None:
        raise ValueError(
            f"Unknown LLM provider '{settings.llm_provider}'. "
            f"Available: {list(providers.keys())}"
        )
    return cls()
