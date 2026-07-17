"""Hallucination risk evaluator - evaluates predicted risk levels against expected."""
from __future__ import annotations

from typing import Tuple

from truthbench.schemas import EvaluationCase, PredictedResult, PredictedVerdict, RiskLevel, Verdict


RISK_SCORE_MAP = {
    RiskLevel.LOW: 0.15,
    RiskLevel.MEDIUM: 0.50,
    RiskLevel.HIGH: 0.85,
}


def evaluate_hallucination_risk(
    expected: EvaluationCase,
    predicted: PredictedResult
) -> Tuple[bool, float, list[str]]:
    """
    Evaluate if predicted hallucination risk matches expected.

    Returns:
        (risk_level_match, risk_score_difference, issues)
    """
    issues = []

    # Check risk level match
    risk_match = expected.expected_risk_level == predicted.risk_level

    if not risk_match:
        issues.append(
            f"Risk level mismatch: expected {expected.expected_risk_level.value}, "
            f"got {predicted.risk_level.value}"
        )

    # Check risk score calibration
    expected_score = RISK_SCORE_MAP.get(expected.expected_risk_level, 0.5)
    score_diff = abs(predicted.hallucination_risk_score - expected_score)

    if score_diff > 0.3:
        issues.append(
            f"Risk score poorly calibrated: expected ~{expected_score:.2f}, "
            f"got {predicted.hallucination_risk_score:.2f} (diff: {score_diff:.2f})"
        )

    return risk_match, score_diff, issues


def hallucination_rate(verdicts) -> float:
    """
    Calculate hallucination rate from a list of predicted verdicts or a PredictedResult.

    Returns fraction of claims that are CONTRADICTED or NOT_ENOUGH_EVIDENCE.
    """
    # Handle both list of PredictedVerdict and PredictedResult
    if hasattr(verdicts, 'predicted_verdicts'):
        verdicts = verdicts.predicted_verdicts
    
    if not verdicts:
        return 0.0

    hallucinated = sum(
        1 for v in verdicts
        if v.verdict in (Verdict.CONTRADICTED, Verdict.NOT_ENOUGH_EVIDENCE)
    )
    return hallucinated / len(verdicts)