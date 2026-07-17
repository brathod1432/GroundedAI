"""API route definitions for Auto-Grounder.

Endpoints are a thin orchestration layer — business logic lives in
``app.core.grounding_loop``.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter

from app.config import settings
from app.core.grounding_loop import run_grounding_loop
from app.schemas import GroundRequest, GroundResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/ground",
    response_model=GroundResponse,
    summary="Ground an LLM-generated answer",
    description=(
        "Accepts a question and an LLM-generated answer, then iteratively "
        "verifies and corrects the answer until the hallucination risk is "
        "acceptable or the maximum number of iterations is reached."
    ),
)
def ground(request: GroundRequest) -> GroundResponse:
    """Run the self-healing grounding pipeline.

    Raises
    ------
    HTTPException 422
        If the input fails Pydantic validation (handled by FastAPI).
    """
    logger.info(
        "Grounding request received — question: '%s…'",
        request.question[:60],
    )

    result = run_grounding_loop(
        question=request.question,
        initial_answer=request.initial_answer,
        trusted_sources=request.trusted_sources,
        max_iterations=request.max_iterations,
    )

    logger.info(
        "Grounding complete — grounded=%s, iterations=%d, risk=%s (%.2f).",
        result.grounded,
        result.total_iterations,
        result.risk_level,
        result.risk_score,
    )
    return result
