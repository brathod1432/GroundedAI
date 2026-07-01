"""Hallucination risk scoring logic.

Converts a list of per-claim verdicts into an aggregate risk score
and a categorical risk level. Scoring is intentionally transparent —
every component of the score can be explained.
"""

from __future__ import annotations

from app.schemas import ClaimVerdict, RiskLevel, Verdict


# Weights control how much each verdict type contributes to risk.
# CONTRADICTED claims are the biggest red flag; NOT_ENOUGH_EVIDENCE
# is a moderate concern; SUPPORTED claims reduce risk.
_VERDICT_WEIGHTS: dict[Verdict, float] = {
    Verdict.CONTRADICTED: 1.0,
    Verdict.NOT_ENOUGH_EVIDENCE: 0.5,
    Verdict.SUPPORTED: 0.0,
}


def compute_risk_score(verdicts: list[ClaimVerdict]) -> float:
    """Compute an aggregate hallucination risk score from 0.0 (safe) to 1.0 (dangerous).

    The formula is a weighted average of verdict penalties:
        score = sum(weight_i) / num_claims

    A score of 0 means every claim is supported. A score of 1 means
    every claim is contradicted.

    Args:
        verdicts: List of per-claim verification verdicts.

    Returns:
        Float in [0.0, 1.0]. Returns 0.0 for an empty verdict list
        (nothing to be suspicious about).
    """
    if not verdicts:
        return 0.0

    total_weight = sum(_VERDICT_WEIGHTS.get(v.verdict, 0.5) for v in verdicts)
    return min(total_weight / len(verdicts), 1.0)


def score_to_risk_level(score: float) -> RiskLevel:
    """Map a numeric risk score to a categorical risk level.

    Thresholds:
        0.00 – 0.33 → LOW
        0.34 – 0.66 → MEDIUM
        0.67 – 1.00 → HIGH
    """
    if score <= 0.33:
        return RiskLevel.LOW
    if score <= 0.66:
        return RiskLevel.MEDIUM
    return RiskLevel.HIGH


def compute_summary(verdicts: list[ClaimVerdict], risk_score: float, risk_level: RiskLevel) -> str:
    """Generate a human-readable one-paragraph summary of the verification result.

    This summary is what a non-technical reviewer would read to
    quickly understand the verification outcome.
    """
    supported = sum(1 for v in verdicts if v.verdict == Verdict.SUPPORTED)
    contradicted = sum(1 for v in verdicts if v.verdict == Verdict.CONTRADICTED)
    unsupported = sum(1 for v in verdicts if v.verdict == Verdict.NOT_ENOUGH_EVIDENCE)
    total = len(verdicts)

    parts: list[str] = []
    if supported:
        parts.append(f"{supported} of {total} claims are supported by evidence")
    if contradicted:
        parts.append(f"{contradicted} claim{'s' if contradicted != 1 else ''} contradict evidence")
    if unsupported:
        parts.append(f"{unsupported} claim{'s' if unsupported != 1 else ''} lack sufficient evidence")

    summary = ". ".join(parts) + "."
    summary += f" Overall hallucination risk is {risk_level.value} (score: {risk_score:.2f})."
    return summary
