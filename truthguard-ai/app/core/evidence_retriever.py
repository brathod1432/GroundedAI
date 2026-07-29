"""Evidence retrieval module.

Takes extracted claims and searches for supporting or contradicting
evidence using the configured search client. Each claim gets up to
``settings.evidence_per_claim`` result items.

Async variant:  ``retrieve_evidence_async`` runs all claim queries in
parallel using ``asyncio.gather`` with ``asyncio.to_thread`` so the
event loop is never blocked by synchronous search-client IO.
"""

from __future__ import annotations

import asyncio
import logging

from app.config import settings
from app.schemas import EvidenceItem
from app.services.search_client import BaseSearchClient, get_search_client

logger = logging.getLogger(__name__)


def _build_evidence_items(
    claim_index: int, raw_results: list[dict]
) -> list[EvidenceItem]:
    """Convert raw search results to EvidenceItem objects for one claim."""
    return [
        EvidenceItem(
            claim_index=claim_index,
            source=raw.get("source", "unknown"),
            snippet=raw.get("snippet", ""),
            url=raw.get("url", ""),
            relevance_score=raw.get("relevance_score", 0.0),
        )
        for raw in raw_results
    ]


def retrieve_candidate_evidence(
    claims: list[str],
    trusted_sources: list[str] | None = None,
    search_client: BaseSearchClient | None = None,
) -> list[EvidenceItem]:
    """Retrieve evidence items for each claim (synchronous, serial).

    Kept for backward-compatibility with non-async callers such as tests.
    For production use, prefer ``retrieve_evidence_async``.

    Args:
        claims: Ordered list of factual claims (from claim_extractor).
        trusted_sources: Source identifiers to prefer. When ``None``,
            falls back to ``settings.default_trusted_sources``.
        search_client: Optional override for the search client
            (useful in tests). When ``None``, the factory is used.

    Returns:
        Flat list of EvidenceItem objects keyed by ``claim_index``.
    """
    client = search_client or get_search_client()
    sources = trusted_sources or settings.default_trusted_sources

    all_evidence: list[EvidenceItem] = []

    for claim_index, claim in enumerate(claims):
        query = f"{' '.join(sources)} {claim}"
        raw_results = client.search(query, max_results=settings.evidence_per_claim)
        all_evidence.extend(_build_evidence_items(claim_index, raw_results))

    logger.debug(
        "Retrieved %d evidence items for %d claims (serial).", len(all_evidence), len(claims)
    )
    return all_evidence


async def retrieve_evidence_async(
    claims: list[str],
    trusted_sources: list[str] | None = None,
    search_client: BaseSearchClient | None = None,
) -> list[EvidenceItem]:
    """Retrieve evidence for all claims in parallel (async).

    Uses ``asyncio.gather`` + ``asyncio.to_thread`` to run all search
    queries concurrently without blocking the FastAPI event loop.
    With real search APIs (Tavily, SerpAPI), N claims → ~1 round-trip
    instead of N serial round-trips.

    Args:
        claims: Ordered list of factual claims.
        trusted_sources: Source identifiers to prefer.
        search_client: Optional override (useful in tests).

    Returns:
        Flat list of EvidenceItem objects keyed by ``claim_index``.
        Order is non-deterministic across claims but stable within each claim.
    """
    client = search_client or get_search_client()
    sources = trusted_sources or settings.default_trusted_sources

    async def fetch_for_claim(claim_index: int, claim: str) -> list[EvidenceItem]:
        query = f"{' '.join(sources)} {claim}"
        # Run the synchronous search client in a thread pool so the event
        # loop is never blocked during network IO.
        raw_results = await asyncio.to_thread(
            client.search, query, settings.evidence_per_claim
        )
        return _build_evidence_items(claim_index, raw_results)

    tasks = [fetch_for_claim(i, c) for i, c in enumerate(claims)]
    results_per_claim = await asyncio.gather(*tasks)

    all_evidence = [item for claim_items in results_per_claim for item in claim_items]
    logger.debug(
        "Retrieved %d evidence items for %d claims (async parallel).",
        len(all_evidence), len(claims),
    )
    return all_evidence


def retrieve_evidence(
    claims: list[str],
    trusted_sources: list[str] | None = None,
    search_client: BaseSearchClient | None = None,
) -> list[EvidenceItem]:
    """Backward-compatible public name used by sync callers."""
    return retrieve_candidate_evidence(claims, trusted_sources, search_client)
