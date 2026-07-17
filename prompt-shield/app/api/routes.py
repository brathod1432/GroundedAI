"""API routes for Prompt Shield."""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from app.config import get_settings
from app.core.injection_detector import detect_injection
from app.core.pii_detector import detect_pii
from app.core.pii_scrubber import scrub_pii, restore_pii
from app.core.toxicity_filter import detect_toxicity
from app.schemas import (
    InjectionResult,
    PIIEntity,
    RiskLevel,
    ShieldAnalysis,
    ShieldRequest,
    ShieldResponse,
    ToxicityResult,
)
from app.services.llm_proxy import get_llm_proxy

logger = logging.getLogger(__name__)

router = APIRouter()


def _risk_from_score(score: float) -> RiskLevel:
    """Map a 0-1 score to a RiskLevel enum."""
    if score >= 0.9:
        return RiskLevel.BLOCKED
    if score >= 0.7:
        return RiskLevel.HIGH
    if score >= 0.4:
        return RiskLevel.MEDIUM
    if score >= 0.1:
        return RiskLevel.LOW
    return RiskLevel.SAFE


def _overall_risk(injection: RiskLevel, toxicity: RiskLevel) -> RiskLevel:
    """Return the worst risk level among the two analyses."""
    order = [RiskLevel.SAFE, RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.BLOCKED]
    return max(injection, toxicity, key=lambda r: order.index(r))


@router.get("/health")
def health() -> dict[str, str]:
    """Health check endpoint."""
    settings = get_settings()
    return {"status": "ok", "service": settings.app_name, "version": settings.app_version}


@router.post("/shield", response_model=ShieldResponse)
def shield(request: ShieldRequest) -> ShieldResponse:
    """
    Analyze and sanitize a user prompt.

    Pipeline:
    1. Toxicity check - block harmful content
    2. Injection detection - block jailbreak attempts
    3. PII scrubbing - redact sensitive data
    4. (Optional) Forward sanitized prompt to LLM
    5. (If forwarded) PII re-injection into response
    """
    settings = get_settings()
    prompt = request.prompt

    # --- Step 1: Toxicity check ---
    tox_analysis = detect_toxicity(prompt, threshold=settings.toxicity_threshold) if settings.toxicity_filtering_enabled else None
    toxicity_result = ToxicityResult(
        is_toxic=tox_analysis.is_toxic if tox_analysis else False,
        toxicity_score=tox_analysis.toxicity_score if tox_analysis else 0.0,
        flagged_categories=tox_analysis.flagged_categories if tox_analysis else [],
        risk_level=_risk_from_score(tox_analysis.toxicity_score) if tox_analysis else RiskLevel.SAFE,
    )

    if toxicity_result.is_toxic:
        logger.warning("Prompt blocked: toxicity score %.2f, categories %s", toxicity_result.toxicity_score, toxicity_result.flagged_categories)
        return ShieldResponse(
            sanitized_prompt="",
            analysis=ShieldAnalysis(
                toxicity_result=toxicity_result,
                overall_risk=RiskLevel.BLOCKED,
                blocked=True,
                block_reason=f"Toxic content detected: {', '.join(toxicity_result.flagged_categories)}",
            ),
            original_prompt_length=len(prompt),
            sanitized_prompt_length=0,
        )

    # --- Step 2: Injection detection ---
    inj_analysis = detect_injection(prompt, threshold=settings.injection_threshold) if settings.injection_detection_enabled else None
    injection_result = InjectionResult(
        is_injection=inj_analysis.is_injection if inj_analysis else False,
        risk_score=inj_analysis.risk_score if inj_analysis else 0.0,
        matched_patterns=inj_analysis.matched_patterns if inj_analysis else [],
        risk_level=_risk_from_score(inj_analysis.risk_score) if inj_analysis else RiskLevel.SAFE,
    )

    if injection_result.is_injection:
        logger.warning("Prompt blocked: injection score %.2f, patterns %s", injection_result.risk_score, injection_result.matched_patterns)
        return ShieldResponse(
            sanitized_prompt="",
            analysis=ShieldAnalysis(
                injection_result=injection_result,
                toxicity_result=toxicity_result,
                overall_risk=RiskLevel.BLOCKED,
                blocked=True,
                block_reason=f"Prompt injection detected: {', '.join(injection_result.matched_patterns)}",
            ),
            original_prompt_length=len(prompt),
            sanitized_prompt_length=0,
        )

    # --- Step 3: PII scrubbing ---
    if settings.pii_detection_enabled:
        scrub_result = scrub_pii(prompt)
        sanitized_prompt = scrub_result.sanitized_text
        pii_entities = [
            PIIEntity(
                pii_type=m.pii_type,
                original=m.value,
                placeholder=ph,
                start=m.start,
                end=m.end,
            )
            for (m, ph) in zip(scrub_result.matches, sorted(scrub_result.pii_mapping.keys()))
        ]
        pii_mapping = scrub_result.pii_mapping
    else:
        sanitized_prompt = prompt
        pii_entities = []
        pii_mapping = {}

    overall = _overall_risk(injection_result.risk_level, toxicity_result.risk_level)

    analysis = ShieldAnalysis(
        pii_detected=pii_entities,
        pii_count=len(pii_entities),
        injection_result=injection_result,
        toxicity_result=toxicity_result,
        overall_risk=overall,
        blocked=False,
    )

    # --- Step 4: Optional LLM forwarding ---
    llm_response = None
    if request.forward_to_llm:
        proxy = get_llm_proxy()
        raw_response = proxy.complete(sanitized_prompt, system_prompt=request.system_prompt)
        # Step 5: Re-inject PII into response
        llm_response = restore_pii(raw_response, pii_mapping)

    return ShieldResponse(
        sanitized_prompt=sanitized_prompt,
        analysis=analysis,
        llm_response=llm_response,
        original_prompt_length=len(prompt),
        sanitized_prompt_length=len(sanitized_prompt),
    )
