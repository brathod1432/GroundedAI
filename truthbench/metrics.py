"""Core metric functions for TruthBench evaluation."""
from __future__ import annotations

from truthbench.schemas import PredictedVerdict, Verdict


def accuracy_score(y_true: list[str], y_pred: list[str]) -> float:
    """Compute accuracy: correct predictions / total predictions."""
    if not y_true or not y_pred:
        return 0.0
    correct = sum(1 for t, p in zip(y_true, y_pred) if t == p)
    return correct / len(y_true)


def precision_score(y_true: list[str], y_pred: list[str], positive_class: str = "SUPPORTED") -> float:
    """Compute precision for a specific class: TP / (TP + FP)."""
    if not y_true or not y_pred:
        return 0.0
    tp = sum(1 for t, p in zip(y_true, y_pred) if t == positive_class and p == positive_class)
    fp = sum(1 for t, p in zip(y_true, y_pred) if t != positive_class and p == positive_class)
    return tp / (tp + fp) if (tp + fp) > 0 else 0.0


def recall_score(y_true: list[str], y_pred: list[str], positive_class: str = "SUPPORTED") -> float:
    """Compute recall for a specific class: TP / (TP + FN)."""
    if not y_true or not y_pred:
        return 0.0
    tp = sum(1 for t, p in zip(y_true, y_pred) if t == positive_class and p == positive_class)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == positive_class and p != positive_class)
    return tp / (tp + fn) if (tp + fn) > 0 else 0.0


def f1_score(y_true: list[str], y_pred: list[str], positive_class: str = "SUPPORTED") -> float:
    """Compute F1 score for a specific class."""
    prec = precision_score(y_true, y_pred, positive_class)
    rec = recall_score(y_true, y_pred, positive_class)
    return 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0


def macro_f1_score(y_true: list[str], y_pred: list[str], classes: list[str] | None = None) -> float:
    """Compute macro-averaged F1 across all classes."""
    if classes is None:
        classes = ["SUPPORTED", "CONTRADICTED", "NOT_ENOUGH_EVIDENCE"]
    f1s = [f1_score(y_true, y_pred, c) for c in classes]
    return sum(f1s) / len(f1s) if f1s else 0.0


def hallucination_rate(verdicts: list[PredictedVerdict]) -> float:
    """
    Compute hallucination rate: fraction of claims that are CONTRADICTED or NOT_ENOUGH_EVIDENCE.

    Higher = more hallucinations.
    """
    if not verdicts:
        return 0.0
    hallucinated = sum(1 for v in verdicts if v.verdict in (Verdict.CONTRADICTED, Verdict.NOT_ENOUGH_EVIDENCE))
    return hallucinated / len(verdicts)


def citation_coverage_score(supported_claims: int, supported_with_citations: int) -> float:
    """
    Compute citation coverage: fraction of SUPPORTED claims that have at least one citation.

    Returns 1.0 if no supported claims (nothing to cite).
    """
    if supported_claims == 0:
        return 1.0
    return min(supported_with_citations / supported_claims, 1.0)


def risk_level_match_rate(expected: list[str], predicted: list[str]) -> float:
    """Compute fraction of cases where predicted risk level matches expected."""
    if not expected or not predicted:
        return 0.0
    matches = sum(1 for e, p in zip(expected, predicted) if e == p)
    return matches / len(expected)


def claim_extraction_accuracy(expected_claims: int, extracted_claims: int, matched_claims: int) -> float:
    """
    Compute claim extraction accuracy.

    Balanced metric considering both recall (matched/expected) and precision (matched/extracted).
    """
    if expected_claims == 0 and extracted_claims == 0:
        return 1.0
    if expected_claims == 0:
        return 0.0  # extracted but nothing expected
    if extracted_claims == 0:
        return 0.0  # nothing extracted

    recall = matched_claims / expected_claims
    precision = matched_claims / extracted_claims
    return 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0