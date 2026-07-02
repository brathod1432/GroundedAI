"""Evidence retrieval module.

Takes extracted claims and searches for supporting or contradicting
evidence using the configured search client. Each claim gets up to
``settings.evidence_per_claim`` result items.
"""

from __future__ import annotations

import logging

from app.config import settings
from app.schemas import EvidenceItem
from app.services.search_client import BaseSearchClient, get_search_client

logger = logging.getLogger(__name__)


def retrieve_candidate_evidence(
    claims: list[str],
    trusted_sources: list[str] | None = None,
    search_client: BaseSearchClient | None = None,
) -> list[EvidenceItem]:
    """Retrieve evidence items for each claim.

    For every claim we issue a search query and collect up to
    ``evidence_per_claim`` results. The claim index is embedded
    in each EvidenceItem so downstream modules know which claim
    the evidence relates to.

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
    global_idx = 0  # running index across all evidence items

    for claim_index, claim in enumerate(claims):
        # Prefix the search query with source hints so the mock (or
        # a real search API) can prioritise requested sources.
        query = f"{' '.join(sources)} {claim}"
        raw_results = client.search(query, max_results=settings.evidence_per_claim)

        for raw in raw_results:
            all_evidence.append(
                EvidenceItem(
                    claim_index=claim_index,
                    source=raw.get("source", "unknown"),
                    snippet=raw.get("snippet", ""),
                    url=raw.get("url", ""),
                    relevance_score=raw.get("relevance_score", 0.0),
                )
            )
            global_idx += 1

    logger.debug(
        "Retrieved %d evidence items for %d claims.", len(all_evidence), len(claims)
    )
    return all_evidence
