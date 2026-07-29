"""Pydantic models for request and response schemas.

These models define the contract between the API layer and the
auto-grounding pipeline.  Every field is typed and documented so
the FastAPI auto-generated docs are useful out of the box.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


# ── Request model ────────────────────────────────────────────────────────


class GroundRequest(BaseModel):
    """Input payload for the ``/ground`` endpoint.

    Attributes:
        question: The original user question / prompt.
        initial_answer: The LLM-generated answer to verify and correct.
        trusted_sources: Optional list of source identifiers to pass to
            TruthGuard for evidence retrieval.
        max_iterations: Override the configured maximum grounding
            iterations for this single request.
    """

    question: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="The original user question or prompt.",
    )
    initial_answer: str = Field(
        ...,
        min_length=1,
        max_length=50000,
        description="The LLM-generated answer to verify and correct.",
    )
    trusted_sources: list[str] | None = Field(
        default=None,
        description="Optional list of trusted source identifiers (e.g. 'wikipedia').",
    )
    max_iterations: int | None = Field(
        default=None,
        ge=1,
        description="Override the configured maximum grounding iterations.",
    )


# ── Iteration tracking ──────────────────────────────────────────────────


class GroundingIteration(BaseModel):
    """Record of a single verify → (correct) iteration."""

    iteration: int = Field(..., description="1-based iteration number.")
    answer: str = Field(..., description="The answer text used in this iteration.")
    risk_score: float = Field(
        ..., ge=0.0, le=1.0, description="Hallucination risk score (0–1)."
    )
    risk_level: str = Field(
        ..., description="Categorical risk level (LOW / MEDIUM / HIGH)."
    )
    contradicted_claims: list[str] = Field(
        default_factory=list,
        description="Claims that were contradicted by evidence.",
    )
    unsupported_claims: list[str] = Field(
        default_factory=list,
        description="Claims that lacked sufficient evidence.",
    )
    action_taken: str = Field(
        ...,
        description=(
            "Action taken after verification: 'verified', 'corrected', "
            "or 'max_retries_reached'."
        ),
    )


# ── Response model ───────────────────────────────────────────────────────


class GroundResponse(BaseModel):
    """Full result returned by the ``/ground`` endpoint."""

    final_answer: str = Field(
        ..., description="The final (possibly corrected) answer."
    )
    grounded: bool = Field(
        ...,
        description="True if the final answer passed verification at an acceptable risk level.",
    )
    risk_score: float = Field(
        ..., ge=0.0, le=1.0, description="Risk score of the final answer."
    )
    risk_level: str = Field(
        ..., description="Risk level of the final answer (LOW / MEDIUM / HIGH)."
    )
    total_iterations: int = Field(
        ..., description="Number of verify–correct iterations performed."
    )
    iterations: list[GroundingIteration] = Field(
        default_factory=list,
        description="Detailed log of every iteration.",
    )
    summary: str = Field(
        ..., description="Human-readable summary of the grounding outcome."
    )
