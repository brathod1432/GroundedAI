"""API route definitions for TruthGuardAI.

All HTTP endpoints are defined here. Business logic lives in
the core/ and services/ modules — routes are a thin orchestration
layer that wires the pipeline together.
"""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, HTTPException
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

from app.config import settings
from app.core.claim_extractor import extract_claims
from app.core.citation_checker import check_citations
from app.core.evidence_retriever import retrieve_evidence_async
from app.core.evidence_ranker import rank_evidence
from app.core.claim_evidence_aligner import align_claims_with_evidence
from app.core.report_builder import build_report
from app.core.verifier import verify_claims
from app.schemas import VerifyRequest, VerifyResponse
from app.utils.log_utils import safe_preview, content_hash

logger = logging.getLogger(__name__)

# Rate limiter — shared instance created in main.py, referenced here via decorator
limiter = Limiter(key_func=get_remote_address)

router = APIRouter()

# Maximum number of requests in a single batch call
_MAX_BATCH_SIZE = 20


async def _run_pipeline(request: VerifyRequest) -> VerifyResponse:
    """Internal async pipeline — extracted so both /verify and /verify/batch reuse it."""
    claims = extract_claims(request.generated_answer)
    if not claims:
        raise HTTPException(
            status_code=422,
            detail="No factual claims could be extracted from the generated answer.",
        )

    # Async parallel evidence retrieval (U2)
    evidence_items = await retrieve_evidence_async(
        claims=claims,
        trusted_sources=request.trusted_sources,
    )
    ranked_evidence = rank_evidence(evidence_items, claims)
    aligned_evidence = align_claims_with_evidence(claims, ranked_evidence)
    citations = check_citations(claims=claims, evidence_items=aligned_evidence)
    verdicts = verify_claims(claims=claims, evidence_items=aligned_evidence)
    return build_report(
        extracted_claims=claims,
        evidence_items=aligned_evidence,
        claim_verdicts=verdicts,
        citations=citations,
    )


@router.post(
    "/verify",
    response_model=VerifyResponse,
    summary="Verify an LLM-generated answer for hallucinations",
    description=(
        "Takes a user question and an LLM-generated answer, then runs the "
        "full verification pipeline: claim extraction → evidence retrieval (async parallel) → "
        "evidence ranking → claim-evidence alignment → "
        "citation checking → claim verification → risk scoring → report."
    ),
)
@limiter.limit("30/minute")
async def verify(request: Request, body: VerifyRequest) -> VerifyResponse:
    """Run the hallucination-verification pipeline on a generated answer.

    This endpoint is the main entry point for TruthGuardAI. It
    orchestrates the full pipeline and returns a structured report.
    Evidence retrieval runs in parallel for all claims (U2).

    Raises:
        HTTPException 422: If the input fails Pydantic validation or no claims extracted.
    """
    logger.info(
        "Verification request received — question: '%s' [%s]",
        safe_preview(body.original_question),
        content_hash(body.original_question),
    )

    report = await _run_pipeline(body)

    logger.info(
        "Verification complete — %d claims, risk=%.2f (%s).",
        len(report.extracted_claims), report.hallucination_risk_score, report.risk_level.value,
    )
    return report


@router.post(
    "/verify/batch",
    response_model=list[VerifyResponse],
    summary="Batch verify multiple LLM-generated answers",
    description=(
        f"Verify up to {_MAX_BATCH_SIZE} question-answer pairs in a single request. "
        "All items run concurrently via asyncio.gather for maximum throughput."
    ),
)
@limiter.limit("10/minute")
async def verify_batch(request: Request, batch: list[VerifyRequest]) -> list[VerifyResponse]:
    """Batch verification endpoint (U5).

    Accepts a list of VerifyRequest objects and returns a corresponding list
    of VerifyResponse objects. All requests are processed concurrently.

    Raises:
        HTTPException 400: If the batch exceeds the maximum size.
        HTTPException 422: If Pydantic validation fails on any item.
    """
    if not batch:
        raise HTTPException(status_code=400, detail="Batch cannot be empty.")
    if len(batch) > _MAX_BATCH_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Batch size {len(batch)} exceeds maximum of {_MAX_BATCH_SIZE}.",
        )

    logger.info("Batch verification request received — %d items.", len(batch))

    # Run all requests concurrently
    tasks = [_run_pipeline(req) for req in batch]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # If any individual pipeline raised, convert to a response with HIGH risk
    # rather than failing the entire batch.
    responses: list[VerifyResponse] = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.warning("Batch item %d failed: %s", i, result)
            # Re-raise to let FastAPI return 422 if validation failed
            if isinstance(result, HTTPException):
                raise result
            raise HTTPException(
                status_code=500,
                detail=f"Batch item {i} failed: {result}",
            )
        responses.append(result)

    logger.info("Batch verification complete — %d results.", len(responses))
    return responses
