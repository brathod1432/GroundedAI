"""LLM client abstraction for generating corrected answers.

Provides a mock implementation for development and testing, and a
real OpenAI implementation behind a common interface.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod

from app.config import settings

logger = logging.getLogger(__name__)


# ── Base class ───────────────────────────────────────────────────────────


class BaseLLMClient(ABC):
    """Abstract LLM client — subclass to add new providers."""

    @abstractmethod
    def complete(self, prompt: str) -> str:
        """Send *prompt* to the LLM and return the completion text."""


# ── Mock implementation ──────────────────────────────────────────────────


class MockLLMClient(BaseLLMClient):
    """Returns a plausible "corrected" answer without calling a real LLM.

    The corrected text is deterministic and based on keywords found in the
    prompt so that tests can assert on its content.
    """

    def complete(self, prompt: str) -> str:
        """Return a synthetic corrected answer."""
        logger.info("MockLLMClient generating corrected answer (prompt length=%d)", len(prompt))

        # Extract the original question from the prompt if present.
        question_marker = "## Original Question\n"
        question = "the question"
        if question_marker in prompt:
            start = prompt.index(question_marker) + len(question_marker)
            end = prompt.index("\n", start)
            question = prompt[start:end].strip()

        return (
            f"Based on the trusted evidence provided, here is the corrected answer "
            f"to '{question}': "
            f"The verified facts indicate that the information has been updated "
            f"to reflect only claims supported by reliable sources. "
            f"All contradicted claims have been removed and replaced with "
            f"evidence-backed statements."
        )


# ── OpenAI implementation ────────────────────────────────────────────────


class OpenAILLMClient(BaseLLMClient):
    """Calls the OpenAI Chat Completions API."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini") -> None:
        self.api_key = api_key
        self.model = model

    def complete(self, prompt: str) -> str:
        """Send *prompt* to OpenAI and return the assistant message."""
        try:
            import openai  # noqa: PLC0415
        except ImportError as exc:
            raise RuntimeError(
                "The 'openai' package is required for the OpenAI provider. "
                "Install it with: pip install openai"
            ) from exc

        client = openai.OpenAI(api_key=self.api_key)
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a factual-accuracy assistant.  Rewrite "
                        "answers using ONLY the evidence provided."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        return response.choices[0].message.content or ""


# ── Factory ──────────────────────────────────────────────────────────────


def get_llm_client() -> BaseLLMClient:
    """Return an LLM client based on the current configuration."""
    provider = settings.llm_provider.lower()

    if provider == "openai":
        if not settings.openai_api_key:
            raise ValueError(
                "GROUNDER_OPENAI_API_KEY must be set when llm_provider='openai'."
            )
        logger.info("Using OpenAI LLM client (model=%s)", settings.openai_model)
        return OpenAILLMClient(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
        )

    # Default: mock
    logger.info("Using MockLLMClient")
    return MockLLMClient()
