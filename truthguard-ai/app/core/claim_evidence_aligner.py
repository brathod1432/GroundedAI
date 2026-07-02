"""Claim-Evidence alignment module.

Aligns claims with their supporting/contradicting evidence by computing
semantic alignment scores. This stage bridges retrieval and verification
by identifying which evidence snippets are most relevant to each claim.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from app.schemas import EvidenceItem

logger = logging.getLogger(__name__)

# Alignment thresholds
_ALIGNMENT_THRESHOLD = 0.25  # Minimum alignment score to consider relevant
_CONTRADICTION_THRESHOLD = 0.15  # Threshold for contradiction signals


@dataclass
class AlignmentResult:
    """Result of claim-evidence alignment."""
    claim_index: int
    supporting_evidence: list[EvidenceItem]
    contradicting_evidence: list[EvidenceItem]
    neutral_evidence: list[EvidenceItem]


def align_claims_with_evidence(
    claims: list[str],
    evidence_items: list[EvidenceItem],
) -> list[EvidenceItem]:
    """Align evidence to claims and filter by relevance.

    For each claim, categorizes evidence as:
    - Supporting: High alignment with claim keywords, no contradiction signals
    - Contradicting: Contains contradiction signals with partial alignment
    - Neutral: Low alignment, no clear signal

    Only supporting and contradicting evidence are passed to verification.

    Args:
        claims: List of extracted claims.
        evidence_items: Ranked evidence items.

    Returns:
        Filtered evidence items (supporting + contradicting only).
    """
    if not evidence_items:
        return []

    # Group by claim_index
    by_claim: dict[int, list[EvidenceItem]] = {}
    for ev in evidence_items:
        by_claim.setdefault(ev.claim_index, []).append(ev)

    aligned: list[EvidenceItem] = []

    for claim_idx, items in by_claim.items():
        claim_text = claims[claim_idx] if claim_idx < len(claims) else ""
        claim_keywords = set(claim_text.lower().split()) if claim_text else set()

        for ev in items:
            alignment = _compute_alignment(ev, claim_keywords)
            contradiction = _detect_contradiction(ev, claim_keywords)

            # Tag evidence with alignment info (stored in relevance_score temporarily)
            # Supporting: high alignment, no contradiction
            # Contradicting: has contradiction signals
            if alignment >= _ALIGNMENT_THRESHOLD and not contradiction:
                aligned.append(ev)
            elif contradiction and alignment >= _CONTRADICTION_THRESHOLD:
                aligned.append(ev)
            # Neutral evidence is dropped

    logger.debug(
        "Aligned %d evidence items for %d claims (from %d total).",
        len(aligned), len(by_claim), len(evidence_items)
    )
    return aligned


def _compute_alignment(evidence: EvidenceItem, claim_keywords: set[str]) -> float:
    """Compute alignment score between evidence and claim."""
    if not claim_keywords:
        return 0.0

    snippet_words = set(evidence.snippet.lower().split())
    overlap = claim_keywords & snippet_words

    # Jaccard-like similarity
    union = claim_keywords | snippet_words
    if not union:
        return 0.0

    return len(overlap) / len(union)


def _detect_contradiction(evidence: EvidenceItem, claim_keywords: set[str]) -> bool:
    """Detect if evidence contradicts the claim."""
    contradiction_signals = {
        "false", "incorrect", "wrong", "not", "never", "no",
        "denied", "debunked", "refuted", "disproven", "contradicts",
        "disagrees", "opposite", "inaccurate", "misleading", "myth"
    }

    snippet_lower = evidence.snippet.lower()
    snippet_words = set(snippet_lower.split())

    # Check for contradiction keywords with some claim keyword overlap
    has_claim_overlap = len(claim_keywords & snippet_words) > 0
    has_contradiction = any(sig in snippet_lower for sig in contradiction_signals)

    return has_claim_overlap and has_contradiction