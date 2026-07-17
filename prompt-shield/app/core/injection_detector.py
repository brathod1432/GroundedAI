"""Prompt injection and jailbreak detection engine."""
from __future__ import annotations

import re
from dataclasses import dataclass

# Each pattern has a name, regex, and weight (contribution to risk score)
_INJECTION_RULES: list[tuple[str, re.Pattern[str], float]] = [
    (
        "ignore_previous_instructions",
        re.compile(r"ignore\s+(?:all\s+)?(?:previous|prior|above|earlier)\s+(?:instructions|prompts|rules|context)", re.IGNORECASE),
        0.95,
    ),
    (
        "disregard_instructions",
        re.compile(r"disregard\s+(?:all\s+)?(?:above|previous|prior|your)\s+(?:instructions|rules|guidelines)", re.IGNORECASE),
        0.95,
    ),
    (
        "role_override_dan",
        re.compile(r"you\s+are\s+now\s+(?:DAN|jailbroken|unrestricted|unfiltered)", re.IGNORECASE),
        0.90,
    ),
    (
        "pretend_no_restrictions",
        re.compile(r"pretend\s+(?:you\s+)?(?:are|have)\s+no\s+(?:restrictions|rules|limits|guidelines|ethics|filters)", re.IGNORECASE),
        0.90,
    ),
    (
        "bypass_safety",
        re.compile(r"bypass\s+(?:safety|content|ethical|security)\s+(?:filters?|guidelines?|checks?|controls?)", re.IGNORECASE),
        0.90,
    ),
    (
        "do_anything_now",
        re.compile(r"(?:do\s+anything\s+now|DAN\s+mode|developer\s+mode\s+enabled)", re.IGNORECASE),
        0.85,
    ),
    (
        "system_prompt_override",
        re.compile(r"(?:^|\n)\s*(?:system\s*:|SYSTEM\s*:|###\s*(?:system|instruction|override)\s*:)", re.IGNORECASE),
        0.80,
    ),
    (
        "delimiter_injection",
        re.compile(r"(?:```\s*system|<\|(?:im_start|system)\|>|</?system>)", re.IGNORECASE),
        0.80,
    ),
    (
        "instruction_leak_request",
        re.compile(r"(?:reveal|show|print|output|repeat|display)\s+(?:your\s+)?(?:system\s+)?(?:prompt|instructions|rules)", re.IGNORECASE),
        0.70,
    ),
    (
        "roleplay_unrestricted",
        re.compile(r"(?:act|behave|respond)\s+(?:as\s+(?:if|though)\s+)?(?:you\s+)?(?:have\s+)?(?:no|without)\s+(?:restrictions|limits|rules|filters)", re.IGNORECASE),
        0.75,
    ),
    (
        "base64_injection",
        re.compile(r"(?:decode|interpret|execute|follow)\s+(?:this\s+)?(?:base64|encoded|b64)", re.IGNORECASE),
        0.70,
    ),
    (
        "do_not_follow_rules",
        re.compile(r"do\s+not\s+follow\s+(?:any\s+)?(?:rules|guidelines|instructions|policies)", re.IGNORECASE),
        0.85,
    ),
]


@dataclass
class InjectionAnalysis:
    """Result of injection detection."""
    is_injection: bool
    risk_score: float
    matched_patterns: list[str]


@dataclass
class _MatchDetail:
    rule_name: str
    matched_text: str
    weight: float


def detect_injection(text: str, threshold: float = 0.7) -> InjectionAnalysis:
    """Analyze text for prompt injection patterns.

    The risk score is the maximum weight among all matched patterns.
    A text is classified as injection if risk_score >= threshold.
    """
    if not text or not text.strip():
        return InjectionAnalysis(is_injection=False, risk_score=0.0, matched_patterns=[])

    matched: list[_MatchDetail] = []
    for rule_name, pattern, weight in _INJECTION_RULES:
        if pattern.search(text):
            matched.append(_MatchDetail(rule_name=rule_name, matched_text=pattern.pattern, weight=weight))

    if not matched:
        return InjectionAnalysis(is_injection=False, risk_score=0.0, matched_patterns=[])

    risk_score = max(m.weight for m in matched)
    # Boost score slightly when multiple patterns match (capped at 1.0)
    if len(matched) > 1:
        risk_score = min(risk_score + 0.05 * (len(matched) - 1), 1.0)

    return InjectionAnalysis(
        is_injection=risk_score >= threshold,
        risk_score=round(risk_score, 2),
        matched_patterns=[m.rule_name for m in matched],
    )
