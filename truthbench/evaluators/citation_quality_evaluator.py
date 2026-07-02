"""Citation quality evaluator - evaluates whether each claim has citation support."""
from __future__ import annotations

from typing import List, Tuple

from truthbench.schemas import EvaluationCase, PredictedResult, Verdict


def citation_coverage_score(supported_claims: int, supported_with_citations: int) -> float:
    """
    Compute citation coverage: fraction of SUPPORTED claims that have at least one citation.

    Returns 1.0 if no supported claims (nothing to cite).
    """
    if supported_claims == 0:
        return 1.0
    return min(supported_with_citations / supported_claims, 1.0)


def evaluate_citation_quality(
    expected: EvaluationCase,
    predicted: PredictedResult
) -> Tuple[float, List[str]]:
    """
    Evaluate citation quality for a case.

    Returns:
        Tuple of (coverage_score, list_of_issues)
    """
    issues = []

    # Count supported claims in predictions
    supported_verdicts = [
        v for v in predicted.predicted_verdicts
        if v.verdict == Verdict.SUPPORTED
    ]

    supported_count = len(supported_verdicts)
    with_citations = sum(1 for v in supported_verdicts if v.evidence_indices)

    # Expected supported claims
    expected_supported = [
        v for v in expected.expected_verdicts
        if v.verdict == Verdict.SUPPORTED
    ]
    expected_supported_count = len(expected_supported)

    coverage = citation_coverage_score(supported_count, with_citations)

    if coverage < 1.0 and supported_count > 0:
        missing = supported_count - with_citations
        issues.append(f"{missing} supported claim(s) missing citations")

    if expected_supported_count > 0 and supported_count == 0:
        issues.append("No supported claims found but expected some")

    if expected_supported_count > supported_count:
        issues.append(f"Missed {expected_supported_count - supported_count} expected supported claims")

    return coverage, issues