"""Verdict consistency evaluator - evaluates whether predicted verdicts match expected verdicts."""
from __future__ import annotations

from typing import Tuple

from truthbench.schemas import EvaluationCase, PredictedResult, Verdict


def evaluate_verdict_consistency(
    expected: EvaluationCase,
    predicted: PredictedResult
) -> Tuple[float, float, float, float, list[str]]:
    """
    Evaluate verdict prediction accuracy, precision, recall, F1.

    Matches predicted verdicts to expected verdicts by claim text.
    Computes metrics for each verdict class.

    Returns:
        (accuracy, precision, recall, f1, issues)
    """
    issues = []

    # Build mapping: claim_text -> expected_verdict
    expected_map = {
        v.claim_text.lower().strip(): v.verdict
        for v in expected.expected_verdicts
    }

    # Build mapping: claim_text -> predicted_verdict
    predicted_map = {
        v.claim_text.lower().strip(): v.verdict
        for v in predicted.predicted_verdicts
    }

    if not expected_map and not predicted_map:
        return 1.0, 1.0, 1.0, 1.0, ["No verdicts to evaluate"]

    all_claims = set(expected_map.keys()) | set(predicted_map.keys())

    # For each claim, get expected and predicted verdict
    y_true = []
    y_pred = []

    for claim in all_claims:
        true_verdict = expected_map.get(claim)
        pred_verdict = predicted_map.get(claim)

        if true_verdict and pred_verdict:
            y_true.append(true_verdict)
            y_pred.append(pred_verdict)
        elif true_verdict and not pred_verdict:
            y_true.append(true_verdict)
            y_pred.append(None)  # Missing prediction
            issues.append(f"Missing prediction for claim: {claim[:80]}...")
        elif not true_verdict and pred_verdict:
            # Extra prediction - treat as false positive
            issues.append(f"Unexpected prediction for claim: {claim[:80]}...")

    if not y_true:
        return 0.0, 0.0, 0.0, 0.0, ["No overlapping claims to evaluate"]

    # Compute metrics per class then average (macro)
    # Only include classes that appear in y_true (have support)
    present_classes = [v for v in [Verdict.SUPPORTED, Verdict.CONTRADICTED, Verdict.NOT_ENOUGH_EVIDENCE] if v in y_true]

    total_precision = 0.0
    total_recall = 0.0
    total_f1 = 0.0
    correct = 0

    for verdict in present_classes:
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == verdict and p == verdict)
        fp = sum(1 for t, p in zip(y_true, y_pred) if t != verdict and p == verdict)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t == verdict and p != verdict)

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

        total_precision += precision
        total_recall += recall
        total_f1 += f1

        correct += tp

    num_classes = len(present_classes) if present_classes else 1
    macro_precision = total_precision / num_classes
    macro_recall = total_recall / num_classes
    macro_f1 = total_f1 / num_classes
    accuracy = correct / len(y_true) if y_true else 0.0

    return accuracy, macro_precision, macro_recall, macro_f1, issues


def verdict_accuracy(
    expected: EvaluationCase,
    predicted: PredictedResult
) -> float:
    """Simple accuracy: fraction of matching verdicts for overlapping claims."""
    expected_map = {v.claim_text.lower().strip(): v.verdict for v in expected.expected_verdicts}
    predicted_map = {v.claim_text.lower().strip(): v.verdict for v in predicted.predicted_verdicts}

    overlapping = set(expected_map.keys()) & set(predicted_map.keys())
    if not overlapping:
        return 0.0

    matches = sum(1 for c in overlapping if expected_map[c] == predicted_map[c])
    return matches / len(overlapping)