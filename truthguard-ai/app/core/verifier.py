"""Claim verification module.

Compares extracted claims against retrieved evidence and assigns
a verdict to each claim. The current implementation uses keyword
overlap as a proxy for semantic similarity — good enough to
exercise the pipeline, and easy to replace with an LLM-based
approach later.
"""

from __future__ import annotations

import logging

from app.core.numerical_checker import check_numerical_conflict
from app.schemas import ClaimVerdict, EvidenceItem, Verdict
from app.services.similarity import best_similarity, keyword_overlap_ratio
from app.utils.text_utils import extract_keywords

logger = logging.getLogger(__name__)

# Thresholds for keyword-overlap ratios that determine the verdict.
# These are tunable constants — in a real system they'd be calibrated
# against a labelled evaluation set.
_SUPPORTED_THRESHOLD = 0.30   # ≥30% keyword overlap → SUPPORTED

# Only strong debunking signals trigger CONTRADICTED in the verifier.
# Weak negations ('not', 'no', 'never') are excluded here to prevent
# false positives — they are handled with context by claim_evidence_aligner.
_CONTRADICTED_KEYWORDS = {
    "debunked", "refuted", "disproven", "contradicts", "inaccurate",
    "misleading", "myth", "fabricated", "denied", "false", "incorrect",
}


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
    evidence_by_claim: dict[int, list[tuple[int, EvidenceItem]]] = {}
    for ev_idx, ev in enumerate(evidence_items):
        evidence_by_claim.setdefault(ev.claim_index, []).append((ev_idx, ev))

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

        best_similarity_score = 0.0
        best_evidence_indices: list[int] = []
        best_ev_for_reasoning: EvidenceItem | None = None
        has_contradiction = False

        for ev_idx, ev in claim_evidence:
            # Use TF-IDF cosine similarity (much better than raw Jaccard overlap)
            sim = best_similarity(claim, ev.snippet)

            if sim > best_similarity_score:
                best_similarity_score = sim
                best_evidence_indices = [ev_idx]
                best_ev_for_reasoning = ev

            # Check for contradiction signals in the evidence snippet.
            # Also check keyword overlap to avoid false positives.
            ev_lower = ev.snippet.lower()
            ev_keywords = set(extract_keywords(ev.snippet))
            has_shared_keywords = bool(claim_keywords & ev_keywords)
            if has_shared_keywords and any(kw in ev_lower for kw in _CONTRADICTED_KEYWORDS):
                has_contradiction = True

        # Determine verdict.
        if has_contradiction:
            verdict = Verdict.CONTRADICTED
            confidence = round(min(best_similarity_score + 0.2, 1.0), 2)
            # Build specific reasoning referencing the evidence source
            if best_ev_for_reasoning:
                snippet_preview = best_ev_for_reasoning.snippet[:100]
                reasoning = (
                    f"Evidence from '{best_ev_for_reasoning.source}' contains contradiction "
                    f"signals: \"{snippet_preview}…\""
                )
            else:
                reasoning = "Evidence contains contradiction signals alongside topic overlap."
        elif best_similarity_score >= _SUPPORTED_THRESHOLD:
            verdict = Verdict.SUPPORTED
            confidence = round(best_similarity_score, 2)
            # Build specific reasoning referencing the supporting evidence
            if best_ev_for_reasoning:
                snippet_preview = best_ev_for_reasoning.snippet[:100]
                reasoning = (
                    f"Supported by '{best_ev_for_reasoning.source}' (similarity "
                    f"{best_similarity_score:.2f}): \"{snippet_preview}…\""
                )
            else:
                reasoning = "Evidence aligns with the claim."
        else:
            verdict = Verdict.NOT_ENOUGH_EVIDENCE
            confidence = round(best_similarity_score, 2)
            reasoning = (
                f"Insufficient evidence (best similarity {best_similarity_score:.2f}, "
                f"threshold {_SUPPORTED_THRESHOLD:.2f}). The claim could not be confirmed "
                "or contradicted by the available evidence."
            )

        # Post-check: upgrade SUPPORTED to CONTRADICTED if numeric values conflict
        if verdict == Verdict.SUPPORTED and best_ev_for_reasoning is not None:
            num_check = check_numerical_conflict(claim, best_ev_for_reasoning.snippet)
            if num_check.has_numeric_conflict:
                verdict = Verdict.CONTRADICTED
                confidence = round(min(best_similarity_score + 0.1, 1.0), 2)
                reasoning = (
                    f"Topic-level evidence found but numeric conflict detected: "
                    f"{num_check.conflict_detail}"
                )

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
