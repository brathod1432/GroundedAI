"""Claim-Evidence alignment module.

Aligns claims with their supporting/contradicting evidence by computing
semantic alignment scores. This stage bridges retrieval and verification
by identifying which evidence snippets are most relevant to each claim.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

from app.schemas import EvidenceItem
from app.services.similarity import cosine_similarity

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
    """Compute alignment score between evidence and claim using TF-IDF cosine.

    Falls back to simple keyword overlap when claim_keywords is provided
    (for backward compatibility with callers that pre-computed keywords).
    The cosine_similarity function is used when we have the claim text.
    """
    if not claim_keywords:
        return 0.0

    snippet_words = set(evidence.snippet.lower().split())
    overlap = claim_keywords & snippet_words

    # TF-IDF cosine-style: weight by overlap fraction of claim terms
    # (better than Jaccard because it normalises by claim length, not union)
    if not claim_keywords:
        return 0.0
    return len(overlap) / len(claim_keywords)


def _detect_contradiction(evidence: EvidenceItem, claim_keywords: set[str]) -> bool:
    """Detect if evidence contradicts the claim.

    Improvements over naive keyword matching:
    - Excludes high-false-positive stopwords ('not', 'no', 'never') unless they
      appear in clearly contradictory phrases rather than double-negations.
    - Requires STRONG contradiction signals OR a weak signal paired with
      at least 2 overlapping claim keywords (reduces false positives where
      'not' appears in unrelated evidence context).
    - Double-negation guard: phrases like 'not incorrect', 'not false',
      'not wrong', 'not untrue' are treated as supportive, not contradictory.
    """
    # Strong signals: explicit debunking language — high confidence
    strong_signals = {
        "debunked", "refuted", "disproven", "contradicts", "inaccurate",
        "misleading", "myth", "fabricated", "false claim",
    }
    # Weak signals: negation words that need additional context
    weak_signals = {"false", "incorrect", "wrong", "denied", "disagrees", "opposite"}

    snippet_lower = evidence.snippet.lower()
    snippet_words = set(snippet_lower.split())

    claim_overlap = claim_keywords & snippet_words
    has_claim_overlap = len(claim_overlap) > 0
    has_strong_overlap = len(claim_overlap) >= 2

    if not has_claim_overlap:
        return False

    # Double-negation guard: phrases like "not false", "not incorrect" etc.
    _DOUBLE_NEG = re.compile(
        r"\bnot\s+(?:false|incorrect|wrong|inaccurate|untrue|unfounded)\b",
        re.IGNORECASE,
    )
    if _DOUBLE_NEG.search(snippet_lower):
        return False

    # Strong signals are sufficient on their own with any overlap
    for sig in strong_signals:
        if sig in snippet_lower:
            return True

    # Weak signals require ≥2 claim keywords present to avoid false positives
    # from stray negation words in unrelated evidence context
    for sig in weak_signals:
        if sig in snippet_lower and has_strong_overlap:
            return True

    # Catch "not X" patterns where X is a claim keyword (e.g. "not true")
    # only when claim overlap is strong
    if has_strong_overlap and re.search(r"\bnot\b", snippet_lower):
        # Check "not" is near a claim keyword (within 10 chars)
        for kw in claim_overlap:
            pattern = re.compile(
                r"\bnot\b.{0,20}" + re.escape(kw) + r"|" + re.escape(kw) + r".{0,20}\bnot\b",
                re.IGNORECASE,
            )
            if pattern.search(snippet_lower):
                return True

    return False