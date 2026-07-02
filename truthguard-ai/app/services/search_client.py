"""Search / evidence-source client abstraction for TruthGuardAI.

Same pattern as llm_client.py: abstract interface, mock implementation,
and a factory driven by settings.
"""

from __future__ import annotations

import logging
import math
from abc import ABC, abstractmethod
from collections import Counter

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


# ── Mock implementation ─────────────────────────────────────────────────

# A small static "knowledge base" the mock can match against.
# In production this would be replaced by real search APIs.
_MOCK_KB: list[dict] = [
    {
        "source": "wikipedia",
        "source_credibility": 0.9,
        "snippet": "France's population was estimated at 68 million in 2023.",
        "url": "https://en.wikipedia.org/wiki/France",
        "keywords": ["france", "population", "estimated", "million", "2023"],
    },
    {
        "source": "wikipedia",
        "source_credibility": 0.9,
        "snippet": "Paris is the capital and most populous city of France.",
        "url": "https://en.wikipedia.org/wiki/Paris",
        "keywords": ["paris", "capital", "france", "populous", "city"],
    },
    {
        "source": "world-bank",
        "source_credibility": 0.95,
        "snippet": "World Bank data shows France GDP at approximately $3 trillion.",
        "url": "https://data.worldbank.org/country/france",
        "keywords": ["france", "world", "bank", "gdp", "trillion"],
    },
    {
        "source": "imf",
        "source_credibility": 0.95,
        "snippet": "IMF estimates France nominal GDP at $2.9 trillion for 2024.",
        "url": "https://www.imf.org/en/Countries/FRA",
        "keywords": ["france", "imf", "gdp", "trillion", "2024"],
    },
    {
        "source": "oecd",
        "source_credibility": 0.9,
        "snippet": "OECD reports France unemployment rate at 7.3% in 2023.",
        "url": "https://data.oecd.org/france.htm",
        "keywords": ["france", "oecd", "unemployment", "rate", "7.3%", "2023"],
    },
    {
        "source": "un",
        "source_credibility": 0.9,
        "snippet": "UN World Population Prospects: France population 68.4 million (2024).",
        "url": "https://population.un.org/wpp/",
        "keywords": ["france", "un", "population", "68.4", "million", "2024"],
    },
]


class MockSearchClient(BaseSearchClient):
    """Returns mock evidence by matching query keywords against a static KB.

    Uses TF-IDF-like scoring with source credibility weighting for more
    realistic relevance scores.
    """

    def __init__(self) -> None:
        self._kb = _MOCK_KB
        self._idf = self._compute_idf()

    def _compute_idf(self) -> dict[str, float]:
        """Compute inverse document frequency for keywords."""
        n_docs = len(self._kb)
        doc_freq: Counter[str] = Counter()
        for entry in self._kb:
            for kw in entry["keywords"]:
                doc_freq[kw] += 1
        return {
            kw: math.log(n_docs / (freq + 1)) + 1.0
            for kw, freq in doc_freq.items()
        }

    def _tokenize(self, text: str) -> list[str]:
        """Simple tokenization."""
        return text.lower().split()

    def _score_entry(self, query: str, entry: dict) -> float:
        """Compute relevance score for a KB entry."""
        query_tokens = set(self._tokenize(query))
        entry_keywords = set(entry["keywords"])

        if not query_tokens or not entry_keywords:
            return 0.0

        # TF-IDF scoring
        overlap = query_tokens & entry_keywords
        if not overlap:
            return 0.0

        tfidf_score = sum(self._idf.get(kw, 1.0) for kw in overlap)
        max_possible = sum(self._idf.get(kw, 1.0) for kw in query_tokens)
        normalized_tfidf = tfidf_score / max_possible if max_possible > 0 else 0.0

        # Source credibility weight
        credibility = entry.get("source_credibility", 0.5)

        # Combined score: 70% TF-IDF, 30% credibility
        return 0.7 * normalized_tfidf + 0.3 * credibility

    def search(self, query: str, max_results: int = 3) -> list[dict]:
        scored = []
        for entry in self._kb:
            score = self._score_entry(query, entry)
            if score > 0:
                scored.append({
                    "source": entry["source"],
                    "snippet": entry["snippet"],
                    "url": entry["url"],
                    "relevance_score": round(score, 4),
                })

        # Sort by relevance descending
        scored.sort(key=lambda x: x["relevance_score"], reverse=True)
        return scored[:max_results]


# ── Tavily client (requires API key) ────────────────────────────────────

class TavilySearchClient(BaseSearchClient):
    """Tavily-backed client. Requires ``tavily_api_key`` in settings.

    This client is a stub that clearly indicates the required configuration.
    When Tavily API key is provided, implement the search method using the
    tavily-python SDK.
    """

    def __init__(self) -> None:
        if not settings.tavily_api_key:
            raise ValueError(
                "TAVILY_API_KEY must be set in environment to use Tavily search client. "
                "Set search_provider=mock in config to use the mock client instead."
            )

    def search(self, query: str, max_results: int = 3) -> list[dict]:
        raise NotImplementedError(
            "Tavily search not implemented. Set search_provider=mock or implement "
            "the search method using the tavily-python SDK."
        )


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
