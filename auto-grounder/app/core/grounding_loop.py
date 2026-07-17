"""Core grounding loop — verify → correct → re-verify.

This module contains the main iterative pipeline that:
1. Verifies an answer via TruthGuard-AI.
2. If the risk is too high, builds a corrective prompt and re-generates.
3. Repeats until the answer is grounded or max iterations are reached.
"""

from __future__ import annotations

import logging
from typing import Any

from app.config import settings
from app.core.corrective_prompt import build_corrective_prompt
from app.schemas import GroundingIteration, GroundResponse
from app.services.llm_client import get_llm_client
from app.services.truthguard_client import get_truthguard_client

logger = logging.getLogger(__name__)

# Risk levels ordered from low to high for comparison.
_RISK_ORDER: dict[str, int] = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}


def _risk_is_acceptable(risk_level: str) -> bool:
    """Return ``True`` if *risk_level* is at or below the configured threshold."""
    threshold = settings.acceptable_risk_level.upper()
    return _RISK_ORDER.get(risk_level.upper(), 99) <= _RISK_ORDER.get(threshold, 0)


def _extract_failed_claims(
    verification: dict[str, Any],
) -> tuple[list[str], list[str]]:
    """Extract contradicted and unsupported claim texts from a verification response."""
    claims: list[str] = verification.get("extracted_claims", [])
    verdicts: list[dict[str, Any]] = verification.get("claim_verdicts", [])

    contradicted: list[str] = []
    unsupported: list[str] = []

    for v in verdicts:
        idx = v.get("claim_index", -1)
        verdict = v.get("verdict", "")
        claim_text = claims[idx] if 0 <= idx < len(claims) else f"Claim {idx}"

        if verdict == "CONTRADICTED":
            contradicted.append(claim_text)
        elif verdict == "NOT_ENOUGH_EVIDENCE":
            unsupported.append(claim_text)

    return contradicted, unsupported


def _extract_evidence(verification: dict[str, Any]) -> list[dict[str, Any]]:
    """Pull the evidence items out of a verification response."""
    return verification.get("evidence_items", [])


# ── Public API ───────────────────────────────────────────────────────────


def run_grounding_loop(
    question: str,
    initial_answer: str,
    trusted_sources: list[str] | None = None,
    max_iterations: int | None = None,
) -> GroundResponse:
    """Execute the iterative verify → correct → re-verify loop.

    Parameters
    ----------
    question:
        The original user question.
    initial_answer:
        The LLM-generated answer to ground.
    trusted_sources:
        Optional source identifiers forwarded to TruthGuard.
    max_iterations:
        Maximum correction iterations.  Falls back to the configured
        ``settings.max_grounding_iterations``.

    Returns
    -------
    GroundResponse
        The final (possibly corrected) answer together with iteration
        metadata.
    """
    max_iter = max_iterations or settings.max_grounding_iterations
    tg_client = get_truthguard_client()
    llm_client = get_llm_client()

    current_answer = initial_answer
    iterations: list[GroundingIteration] = []

    for i in range(1, max_iter + 1):
        logger.info("Grounding iteration %d / %d", i, max_iter)

        # ── Step 1: Verify ───────────────────────────────────────────
        verification = tg_client.verify(
            question=question,
            answer=current_answer,
            trusted_sources=trusted_sources,
        )

        risk_score: float = verification.get("hallucination_risk_score", 1.0)
        risk_level: str = verification.get("risk_level", "HIGH")
        contradicted, unsupported = _extract_failed_claims(verification)

        # ── Step 2: Check if acceptable ──────────────────────────────
        if _risk_is_acceptable(risk_level):
            iteration = GroundingIteration(
                iteration=i,
                answer=current_answer,
                risk_score=risk_score,
                risk_level=risk_level,
                contradicted_claims=contradicted,
                unsupported_claims=unsupported,
                action_taken="verified",
            )
            iterations.append(iteration)
            logger.info(
                "Answer grounded on iteration %d (risk=%s, score=%.2f)",
                i, risk_level, risk_score,
            )
            return GroundResponse(
                final_answer=current_answer,
                grounded=True,
                risk_score=risk_score,
                risk_level=risk_level,
                total_iterations=i,
                iterations=iterations,
                summary=(
                    f"Answer grounded successfully after {i} iteration(s). "
                    f"Final risk: {risk_level} ({risk_score:.2f})."
                ),
            )

        # ── Step 3: Last iteration — cannot correct further ──────────
        if i == max_iter:
            iteration = GroundingIteration(
                iteration=i,
                answer=current_answer,
                risk_score=risk_score,
                risk_level=risk_level,
                contradicted_claims=contradicted,
                unsupported_claims=unsupported,
                action_taken="max_retries_reached",
            )
            iterations.append(iteration)
            logger.warning(
                "Max iterations (%d) reached — answer NOT grounded "
                "(risk=%s, score=%.2f).",
                max_iter, risk_level, risk_score,
            )
            return GroundResponse(
                final_answer=current_answer,
                grounded=False,
                risk_score=risk_score,
                risk_level=risk_level,
                total_iterations=i,
                iterations=iterations,
                summary=(
                    f"Max iterations ({max_iter}) reached. "
                    f"Answer could not be grounded. "
                    f"Final risk: {risk_level} ({risk_score:.2f})."
                ),
            )

        # ── Step 4: Correct ──────────────────────────────────────────
        evidence = _extract_evidence(verification)
        prompt = build_corrective_prompt(
            question=question,
            failed_answer=current_answer,
            evidence=evidence,
            contradicted_claims=contradicted,
            unsupported_claims=unsupported,
        )

        iteration = GroundingIteration(
            iteration=i,
            answer=current_answer,
            risk_score=risk_score,
            risk_level=risk_level,
            contradicted_claims=contradicted,
            unsupported_claims=unsupported,
            action_taken="corrected",
        )
        iterations.append(iteration)

        current_answer = llm_client.complete(prompt)
        logger.info("Corrected answer generated (length=%d)", len(current_answer))

    # Fallback (should not be reached due to loop logic).
    return GroundResponse(  # pragma: no cover
        final_answer=current_answer,
        grounded=False,
        risk_score=1.0,
        risk_level="HIGH",
        total_iterations=max_iter,
        iterations=iterations,
        summary="Grounding loop exited unexpectedly.",
    )
