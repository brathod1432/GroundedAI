"""Claim verification module.

Compares extracted claims against retrieved evidence and assigns
a verdict to each claim. The current implementation uses keyword
overlap as a proxy for semantic similarity — good enough to
exercise the pipeline, and easy to replace with an LLM-based
approach later.
"""

from __future__ import annotations

import logging

from app.schemas import ClaimVerdict, EvidenceItem, Verdict
from app.utils.text_utils import extract_keywords

logger = logging.getLogger(__name__)

# Thresholds for keyword-overlap ratios that determine the verdict.
# These are tunable constants — in a real system they'd be calibrated
# against a labelled evaluation set.
_SUPPORTED_THRESHOLD = 0.30   # ≥30% keyword overlap → SUPPORTED
_CONTRADICTED_KEYWORDS = {"false", "incorrect", "wrong", "not", "never", "no", "denied", "debunked"}


def verify_claims(
    claims: list[str],
    evidence_items: list[EvidenceItem],
) -> list[ClaimVerdict]:
    """Verify each claim against its associated evidence.

    The verification strategy (v0.1):

    1. For each claim, collect all evidence items linked to it.
    2. Compute keyword overlap between the claim and each evidence snippet.
    3. If any evidence snippet has high overlap → ``SUPPORTED``.
    4. If any evidence snippet contains contradiction signals alongside
       partial overlap → ``CONTRADICTED``.
    5. Otherwise → ``NOT_ENOUGH_EVIDENCE``.

    Args:
        claims: Ordered list of extracted claims.
        evidence_items: All retrieved evidence items.

    Returns:
        List of ClaimVerdict objects — one per claim.
    """
    verdicts: list[ClaimVerdict] = []

    # Group evidence by claim index for efficient lookup.
    evidence_by_claim: dict[int, list[EvidenceItem]] = {}
    for ev in evidence_items:
        evidence_by_claim.setdefault(ev.claim_index, []).append(ev)

    for claim_index, claim in enumerate(claims):
        claim_evidence = evidence_by_claim.get(claim_index, [])
        claim_keywords = set(extract_keywords(claim))

        if not claim_keywords or not claim_evidence:
            verdicts.append(
                ClaimVerdict(
                    claim_index=claim_index,
                    verdict=Verdict.NOT_ENOUGH_EVIDENCE,
                    confidence=0.0,
                    evidence_indices=[],
                    reasoning="No evidence found or no keywords could be extracted.",
                )
            )
            continue

        best_overlap_ratio = 0.0
        best_evidence_indices: list[int] = []
        has_contradiction = False

        for ev_idx, ev in enumerate(claim_evidence):
            ev_keywords = set(extract_keywords(ev.snippet))
            overlap = claim_keywords & ev_keywords
            ratio = len(overlap) / len(claim_keywords)

            if ratio > best_overlap_ratio:
                best_overlap_ratio = ratio
                best_evidence_indices = [ev_idx]

            # Check for contradiction signals in the evidence snippet.
            ev_lower = ev.snippet.lower()
            if overlap and any(kw in ev_lower for kw in _CONTRADICTED_KEYWORDS):
                has_contradiction = True

        # Determine verdict.
        if has_contradiction:
            verdict = Verdict.CONTRADICTED
            confidence = round(min(best_overlap_ratio + 0.2, 1.0), 2)
            reasoning = "Evidence contains contradiction signals alongside partial topic overlap."
        elif best_overlap_ratio >= _SUPPORTED_THRESHOLD:
            verdict = Verdict.SUPPORTED
            confidence = round(best_overlap_ratio, 2)
            reasoning = "Evidence aligns with the claim."
        else:
            verdict = Verdict.NOT_ENOUGH_EVIDENCE
            confidence = round(best_overlap_ratio, 2)
            reasoning = "Insufficient keyword overlap to confirm or contradict the claim."

        verdicts.append(
            ClaimVerdict(
                claim_index=claim_index,
                verdict=verdict,
                confidence=confidence,
                evidence_indices=best_evidence_indices,
                reasoning=reasoning,
            )
        )

    logger.debug("Verified %d claims.", len(verdicts))
    return verdicts
