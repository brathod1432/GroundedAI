from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    """Risk level classification for prompt analysis."""

    SAFE = "SAFE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    BLOCKED = "BLOCKED"


class PIIEntity(BaseModel):
    """A detected PII entity."""

    pii_type: str = Field(
        ..., description="Type: email, phone, ssn, credit_card, api_key, ip_address"
    )
    original: str = Field(..., description="Original PII value found")
    placeholder: str = Field(..., description="Placeholder used in sanitized text")
    start: int = Field(..., ge=0)
    end: int = Field(..., ge=0)


class InjectionResult(BaseModel):
    """Result of prompt injection analysis."""

    is_injection: bool = Field(default=False)
    risk_score: float = Field(default=0.0, ge=0.0, le=1.0)
    matched_patterns: list[str] = Field(default_factory=list)
    risk_level: RiskLevel = Field(default=RiskLevel.SAFE)


class ToxicityResult(BaseModel):
    """Result of toxicity analysis."""

    is_toxic: bool = Field(default=False)
    toxicity_score: float = Field(default=0.0, ge=0.0, le=1.0)
    flagged_categories: list[str] = Field(default_factory=list)
    risk_level: RiskLevel = Field(default=RiskLevel.SAFE)


class ShieldRequest(BaseModel):
    """Request to shield/proxy an LLM prompt."""

    prompt: str = Field(
        ..., min_length=1, max_length=50000, description="The user prompt to analyze and sanitize"
    )
    system_prompt: str | None = Field(
        default=None, max_length=10000, description="Optional system prompt"
    )
    forward_to_llm: bool = Field(
        default=False, description="If True, forward sanitized prompt to LLM and return response"
    )


class ShieldAnalysis(BaseModel):
    """Analysis results from the shield pipeline."""

    pii_detected: list[PIIEntity] = Field(default_factory=list)
    pii_count: int = Field(default=0)
    injection_result: InjectionResult = Field(default_factory=InjectionResult)
    toxicity_result: ToxicityResult = Field(default_factory=ToxicityResult)
    overall_risk: RiskLevel = Field(default=RiskLevel.SAFE)
    blocked: bool = Field(default=False)
    block_reason: str | None = Field(default=None)


class ShieldResponse(BaseModel):
    """Response from the shield pipeline."""

    sanitized_prompt: str = Field(..., description="The prompt with PII redacted")
    analysis: ShieldAnalysis
    llm_response: str | None = Field(
        default=None, description="LLM response if forward_to_llm was True"
    )
    original_prompt_length: int = Field(default=0)
    sanitized_prompt_length: int = Field(default=0)
