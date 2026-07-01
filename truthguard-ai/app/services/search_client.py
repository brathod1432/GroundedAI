"""Search / evidence-source client abstraction for TruthGuardAI.

Same pattern as llm_client.py: abstract interface, mock implementation,
and a factory driven by settings.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod

from app.config import settings

logger = logging.getLogger(__name__)


# ── Abstract interface ──────────────────────────────────────────────────

class BaseSearchClient(ABC):
    """Interface every search backend must implement."""

    @abstractmethod
    def search(self, query: str, max_results: int = 3) -> list[dict]:
        """Return a list of evidence dicts for the given *query*.

        Each dict should contain at minimum: ``source``, ``snippet``,
        ``url``, and ``relevance_score``.
        """


# ── Mock implementation ────────────────────────────────────────────────

# A small static "knowledge base" the mock can match against.
_MOCK_KB: list[dict] = [
    {
        "source": "wikipedia",
        "snippet": "France's population was estimated at 68 million in 2023.",
        "url": "https://en.wikipedia.org/wiki/France",
        "keywords": ["france", "population", "estimated", "million"],
    },
    {
        "source": "wikipedia",
        "snippet": "Paris is the capital and most populous city of France.",
        "url": "https://en.wikipedia.org/wiki/Paris",
        "keywords": ["paris", "capital", "france", "populous"],
    },
    {
        "source": "world-bank",
        "snippet": "World Bank data shows France GDP at approximately $3 trillion.",
        "url": "https://data.worldbank.org/country/france",
        "keywords": ["france", "world", "bank", "trillion"],
    },
]


class MockSearchClient(BaseSearchClient):
    """Returns mock evidence by matching query keywords against a static KB."""

    def search(self, query: str, max_results: int = 3) -> list[dict]:
        query_words = set(query.lower().split())
        results: list[dict] = []
        for entry in _MOCK_KB:
            overlap = query_words & set(entry["keywords"])
            if overlap:
                results.append({
                    "source": entry["source"],
                    "snippet": entry["snippet"],
                    "url": entry["url"],
                    "relevance_score": min(len(overlap) / 3.0, 1.0),
                })
        return results[:max_results]


# ── Tavily placeholder ──────────────────────────────────────────────────

class TavilySearchClient(BaseSearchClient):
    """Tavily-backed client. Requires ``tavily_api_key`` in settings."""

    def __init__(self) -> None:
        if not settings.tavily_api_key:
            raise ValueError("TAVILY_API_KEY must be set to use the Tavily search client.")

    def search(self, query: str, max_results: int = 3) -> list[dict]:
        # TODO: implement with ``tavily-python`` SDK
        raise NotImplementedError("Tavily integration pending — see roadmap v0.3")


# ── Factory ──────────────────────────────────────────────────────────────

def get_search_client() -> BaseSearchClient:
    """Return the configured search client instance."""
    providers = {
        "mock": MockSearchClient,
        "tavily": TavilySearchClient,
    }
    cls = providers.get(settings.search_provider)
    if cls is None:
        raise ValueError(
            f"Unknown search provider '{settings.search_provider}'. "
            f"Available: {list(providers.keys())}"
        )
    return cls()
