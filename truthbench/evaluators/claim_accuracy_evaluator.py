"""Claim accuracy evaluator - evaluates whether extracted claims match expected claims."""
from __future__ import annotations

from typing import List, Tuple

from truthbench.schemas import EvaluationCase, PredictedResult, PredictedClaim


def evaluate_claim_accuracy(
    expected: EvaluationCase,
    predicted: PredictedResult
) -> Tuple[float, float, float, float, List[str]]:
    """
    Evaluate claim extraction accuracy.

    Matches predicted claims to expected claims by text similarity.
    Computes precision, recall, F1 for claim extraction.

    Returns:
        (accuracy, precision, recall, f1, issues)
    """
    issues = []

    expected_texts = [c.text.lower().strip() for c in expected.expected_claims]
    predicted_texts = [c.text.lower().strip() for c in predicted.extracted_claims]

    if not expected_texts and not predicted_texts:
        return 1.0, 1.0, 1.0, 1.0, ["No claims to evaluate"]

    # Simple matching: exact or substring match
    matched_predicted = set()
    matched_expected = set()
    true_positives = 0

    for i, pred_text in enumerate(predicted_texts):
        best_match_idx = -1
        best_score = 0.0

        for j, exp_text in enumerate(expected_texts):
            if j in matched_expected:
                continue

            # Check if one contains the other (fuzzy match)
            if pred_text in exp_text or exp_text in pred_text:
                score = len(set(pred_text.split()) & set(exp_text.split())) / max(len(pred_text.split()), 1)
                if score > best_score:
                    best_score = score
                    best_match_idx = j

        if best_match_idx >= 0 and best_score > 0.5:
            true_positives += 1
            matched_predicted.add(i)
            matched_expected.add(best_match_idx)

    false_positives = len(predicted_texts) - len(matched_predicted)
    false_negatives = len(expected_texts) - len(matched_expected)

    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    # Simple accuracy: TP / total expected
    accuracy = true_positives / len(expected_texts) if expected_texts else 0.0

    if false_positives > 0:
        issues.append(f"{false_positives} extra claims extracted (not in expected)")
    if false_negatives > 0:
        issues.append(f"{false_negatives} expected claims missed")

    return accuracy, precision, recall, f1, issues


def claim_accuracy_simple(
    expected: EvaluationCase,
    predicted: PredictedResult
) -> float:
    """Simple accuracy: fraction of expected claims found in predictions."""
    expected_texts = [c.text.lower().strip() for c in expected.expected_claims]
    predicted_texts = [c.text.lower().strip() for c in predicted.extracted_claims]

    if not expected_texts:
        return 1.0

    found = 0
    for exp in expected_texts:
        if any(exp in pred or pred in exp for pred in predicted_texts):
            found += 1

    return found / len(expected_texts)