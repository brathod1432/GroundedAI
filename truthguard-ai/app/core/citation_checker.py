"""Citation checker module.

Validates that the evidence items cited for each claim are
meaningfully connected to the claim text. In this version we use
simple keyword overlap to gauge whether a citation genuinely
supports a claim or is just loosely associated.

This module is intentionally separate from the verifier —
citation checking is about source *quality* and *relevance*,
whereas verification is about claim *truthfulness*.
"""

from __future__ import annotations

import logging

from app.schemas import Citation, EvidenceItem
from app.utils.text_utils import extract_keywords

logger = logging.getLogger(__name__)

# Minimum keyword-overlap ratio for a citation to be considered valid.
_MIN_OVERLAP_RATIO = 0.2


def check_citations(
    claims: list[str],
    evidence_items: list[EvidenceItem],
) -> list[Citation]:
    """Validate citations and return only those that genuinely relate to their claims.

    For each evidence item, we check that the evidence snippet shares
    enough content keywords with the claim it is attached to. Evidence
    items that fail this check are excluded from the citation list.

    Args:
        claims: Ordered list of extracted claims.
        evidence_items: Evidence items (each keyed by ``claim_index``).

    Returns:
        Filtered list of Citation objects for claims that have
        at least one valid, relevant piece of evidence.
    """
    # Pre-compute keywords for each claim once.
    claim_keywords: list[set[str]] = [set(extract_keywords(c)) for c in claims]

    citations: list[Citation] = []

    for ev in evidence_items:
        if ev.claim_index >= len(claims):
            logger.warning("Evidence item references claim_index %d but only %d claims exist.", ev.claim_index, len(claims))
            continue

        ckw = claim_keywords[ev.claim_index]
        if not ckw:
            # No extractable keywords — skip citation validation for this claim.
            continue

        ev_keywords = set(extract_keywords(ev.snippet))
        overlap = ckw & ev_keywords
        ratio = len(overlap) / len(ckw) if ckw else 0.0

        if ratio >= _MIN_OVERLAP_RATIO:
            citations.append(
                Citation(
                    claim_index=ev.claim_index,
                    source=ev.source,
                    url=ev.url,
                    confidence=round(ev.relevance_score, 2),
                )
            )

    logger.debug("Validated %d citations from %d evidence items.", len(citations), len(evidence_items))
    return citations
