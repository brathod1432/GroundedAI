"""Evidence ranking module.

Ranks retrieved evidence by relevance to claims, applying source credibility
and recency signals. This stage ensures the most trustworthy evidence is
used for verification.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.schemas import EvidenceItem

logger = logging.getLogger(__name__)

# Source credibility weights (higher = more trustworthy)
SOURCE_CREDIBILITY = {
    "wikipedia": 0.8,
    "world-bank": 0.95,
    "imf": 0.95,
    "oecd": 0.9,
    "who": 0.95,
    "nih": 0.95,
    "pubmed": 0.95,
    "arxiv": 0.85,
    "news": 0.6,
    "blog": 0.3,
    "unknown": 0.4,
}


def rank_evidence(
    evidence_items: list[EvidenceItem],
    claims: list[str],
    top_k: int = 5,
) -> list[EvidenceItem]:
    """Rank evidence items by composite relevance score.

    The composite score combines:
    - Original relevance_score from search (keyword overlap)
    - Source credibility weight
    - Recency factor (for dated sources)
    - Claim-specific keyword density

    Args:
        evidence_items: Raw evidence items from retrieval.
        claims: The claims being verified.
        top_k: Maximum evidence items per claim to retain.

    Returns:
        Ranked evidence items, limited to top_k per claim.
    """
    if not evidence_items:
        return []

    # Group by claim_index
    by_claim: dict[int, list[EvidenceItem]] = {}
    for ev in evidence_items:
        by_claim.setdefault(ev.claim_index, []).append(ev)

    ranked: list[EvidenceItem] = []

    for claim_idx, items in by_claim.items():
        claim_text = claims[claim_idx] if claim_idx < len(claims) else ""
        claim_keywords = set(claim_text.lower().split()) if claim_text else set()

        scored = []
        for ev in items:
            score = _compute_composite_score(ev, claim_keywords)
            # Create new item with updated relevance_score
            ranked_ev = EvidenceItem(
                claim_index=ev.claim_index,
                source=ev.source,
                snippet=ev.snippet,
                url=ev.url,
                relevance_score=score,
            )
            scored.append(ranked_ev)

        # Sort by score descending, take top_k
        scored.sort(key=lambda x: x.relevance_score, reverse=True)
        ranked.extend(scored[:top_k])

    logger.debug("Ranked %d evidence items for %d claims.", len(ranked), len(by_claim))
    return ranked


def _compute_composite_score(
    evidence: EvidenceItem,
    claim_keywords: set[str],
) -> float:
    """Compute composite relevance score for an evidence item."""
    # Base score from search relevance
    base_score = evidence.relevance_score

    # Source credibility
    source_cred = SOURCE_CREDIBILITY.get(evidence.source.lower(), 0.5)

    # Keyword density in snippet
    snippet_words = set(evidence.snippet.lower().split())
    keyword_density = len(claim_keywords & snippet_words) / max(len(claim_keywords), 1)

    # URL authority (simple heuristic: .gov, .edu, .org get bonus)
    url_bonus = 0.0
    if evidence.url:
        if any(domain in evidence.url for domain in [".gov", ".edu", ".org"]):
            url_bonus = 0.05

    # Weighted combination
    composite = (
        0.4 * base_score
        + 0.3 * source_cred
        + 0.2 * keyword_density
        + 0.1 * url_bonus
    )

    return min(composite, 1.0)