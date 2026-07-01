"""Report builder module.

Assembles the final verification report by combining extracted claims,
evidence items, verdicts, citations, and the computed risk score into
a single VerifyResponse object. This is the last stage of the pipeline.
"""

from __future__ import annotations

import logging

from app.schemas import (
    Citation,
    ClaimVerdict,
    EvidenceItem,
    RiskLevel,
    VerifyResponse,
)
from app.services.scoring import compute_risk_score, compute_summary, score_to_risk_level

logger = logging.getLogger(__name__)


def build_report(
    extracted_claims: list[str],
    evidence_items: list[EvidenceItem],
    claim_verdicts: list[ClaimVerdict],
    citations: list[Citation],
) -> VerifyResponse:
    """Assemble the final verification response.

    This function is intentionally thin — all the heavy lifting has
    already happened in upstream modules. Its job is to compute the
    aggregate risk score / level, generate a human-readable summary,
    and pack everything into the response schema.

    Args:
        extracted_claims: Claims extracted from the generated answer.
        evidence_items: Evidence retrieved for the claims.
        claim_verdicts: Per-claim verification verdicts.
        citations: Validated citations.

    Returns:
        A fully populated VerifyResponse ready for the API layer.
    """
    risk_score = compute_risk_score(claim_verdicts)
    risk_level = score_to_risk_level(risk_score)
    summary = compute_summary(claim_verdicts, risk_score, risk_level)

    response = VerifyResponse(
        extracted_claims=extracted_claims,
        evidence_items=evidence_items,
        claim_verdicts=claim_verdicts,
        hallucination_risk_score=round(risk_score, 2),
        risk_level=risk_level,
        final_summary=summary,
        citations=citations,
    )

    logger.debug(
        "Report built: %d claims, %d evidence, risk=%.2f (%s).",
        len(extracted_claims), len(evidence_items), risk_score, risk_level.value,
    )
    return response
