"""Pydantic models for request and response schemas.

These models define the contract between the API layer and the
verification pipeline. Every field is typed and documented so the
FastAPI auto-generated docs are useful out of the box.
"""

from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, Field


# ── Enums ────────────────────────────────────────────────────────────────

class Verdict(str, Enum):
    """Possible verification verdicts for a single claim."""
    SUPPORTED = "SUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    NOT_ENOUGH_EVIDENCE = "NOT_ENOUGH_EVIDENCE"


class RiskLevel(str, Enum):
    """Aggregate hallucination risk level."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


# ── Request models ───────────────────────────────────────────────────────

class VerifyRequest(BaseModel):
    """Input payload for the /verify endpoint.

    Attributes:
        original_question: The user's original question or prompt.
        generated_answer: The LLM-generated answer to verify.
        trusted_sources: Optional list of source identifiers to
            prioritise during evidence retrieval. Falls back to
            ``settings.default_trusted_sources`` when omitted.
    """
    original_question: str = Field(
        ..., min_length=1, description="The user's original question or prompt."
    )
    generated_answer: str = Field(
        ..., min_length=1, description="The LLM-generated answer to verify."
    )
    trusted_sources: list[str] | None = Field(
        default=None,
        description="Optional list of trusted source identifiers (e.g. 'wikipedia').",
    )


# ── Response sub-models ──────────────────────────────────────────────────

class EvidenceItem(BaseModel):
    """A single piece of retrieved evidence linked to a claim."""
    claim_index: int = Field(..., description="Index of the claim this evidence relates to.")
    source: str = Field(..., description="Source identifier (e.g. 'wikipedia').")
    snippet: str = Field(..., description="Short text snippet from the source.")
    url: str = Field(default="", description="URL of the source page, if available.")
    relevance_score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="How relevant this evidence is to the claim."
    )


class ClaimVerdict(BaseModel):
    """Verification result for a single extracted claim."""
    claim_index: int = Field(..., description="Index of the claim this verdict refers to.")
    verdict: Verdict = Field(..., description="SUPPORTED, CONTRADICTED, or NOT_ENOUGH_EVIDENCE.")
    confidence: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Confidence in the verdict (0–1)."
    )
    evidence_indices: list[int] = Field(
        default_factory=list, description="Indices into evidence_items used for this verdict."
    )
    reasoning: str = Field(default="", description="Short human-readable explanation.")


class Citation(BaseModel):
    """A citation linking a claim to its supporting source."""
    claim_index: int = Field(..., description="Index of the claim this citation supports.")
    source: str = Field(..., description="Source identifier.")
    url: str = Field(default="", description="URL of the cited source.")
    confidence: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Confidence that this source supports the claim."
    )


# ── Top-level response ───────────────────────────────────────────────────

class VerifyResponse(BaseModel):
    """Full verification report returned by the /verify endpoint.

    This is the single source of truth for what the API returns.
    """
    extracted_claims: list[str] = Field(
        ..., description="Atomic factual claims extracted from the generated answer."
    )
    evidence_items: list[EvidenceItem] = Field(
        default_factory=list, description="Evidence snippets retrieved during verification."
    )
    claim_verdicts: list[ClaimVerdict] = Field(
        default_factory=list, description="Per-claim verification verdicts."
    )
    hallucination_risk_score: float = Field(
        ..., ge=0.0, le=1.0, description="Aggregate risk score (0 = safe, 1 = high risk)."
    )
    risk_level: RiskLevel = Field(
        ..., description="Categorical risk level derived from the risk score."
    )
    final_summary: str = Field(
        ..., description="Human-readable paragraph summarising the verification outcome."
    )
    citations: list[Citation] = Field(
        default_factory=list, description="Structured citations for supported claims."
    )
