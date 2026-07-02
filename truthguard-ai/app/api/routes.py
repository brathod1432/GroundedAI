"""API route definitions for TruthGuardAI.

All HTTP endpoints are defined here. Business logic lives in
the core/ and services/ modules — routes are a thin orchestration
layer that wires the pipeline together.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.core.claim_extractor import extract_claims
from app.core.citation_checker import check_citations
from app.core.evidence_retriever import retrieve_evidence
from app.core.evidence_ranker import rank_evidence
from app.core.claim_evidence_aligner import align_claims_with_evidence
from app.core.report_builder import build_report
from app.core.verifier import verify_claims
from app.schemas import VerifyRequest, VerifyResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/verify",
    response_model=VerifyResponse,
    summary="Verify an LLM-generated answer for hallucinations",
    description=(
        "Takes a user question and an LLM-generated answer, then runs the "
        "full verification pipeline: claim extraction → evidence retrieval → "
        "evidence ranking → claim-evidence alignment → "
        "citation checking → claim verification → risk scoring → report."
    ),
)
def verify(request: VerifyRequest) -> VerifyResponse:
    """Run the hallucination-verification pipeline on a generated answer.

    This endpoint is the main entry point for TruthGuardAI. It
    orchestrates the full pipeline and returns a structured report.

    Raises:
        HTTPException 422: If the input fails Pydantic validation (handled by FastAPI).
    """
    logger.info(
        "Verification request received — question: '%s…'",
        request.original_question[:60],
    )

    # 1. Claim extraction
    claims = extract_claims(request.generated_answer)
    if not claims:
        logger.warning("No claims extracted from the generated answer.")
        raise HTTPException(
            status_code=422,
            detail="No factual claims could be extracted from the generated answer.",
        )

    # 2. Evidence retrieval
    evidence_items = retrieve_evidence(
        claims=claims,
        trusted_sources=request.trusted_sources,
    )

    # 3. Evidence ranking
    ranked_evidence = rank_evidence(evidence_items, claims)

    # 4. Claim-evidence alignment
    aligned_evidence = align_claims_with_evidence(claims, ranked_evidence)

    # 5. Citation checking (validate citations for supported claims)
    citations = check_citations(
        claims=claims,
        evidence_items=aligned_evidence,
    )

    # 6. Claim verification
    verdicts = verify_claims(
        claims=claims,
        evidence_items=aligned_evidence,
    )

    # 7. Report assembly (includes scoring)
    report = build_report(
        extracted_claims=claims,
        evidence_items=aligned_evidence,
        claim_verdicts=verdicts,
        citations=citations,
    )

    logger.info(
        "Verification complete — %d claims, risk=%.2f (%s).",
        len(claims), report.hallucination_risk_score, report.risk_level.value,
    )
    return report
