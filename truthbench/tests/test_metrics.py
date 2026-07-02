"""Tests for metrics module."""
from __future__ import annotations

from truthbench.metrics import (
    accuracy_score,
    citation_coverage_score,
    f1_score,
    hallucination_rate,
    macro_f1_score,
    precision_score,
    recall_score,
    risk_level_match_rate,
)
from truthbench.schemas import PredictedVerdict, Verdict


class TestAccuracyScore:
    def test_perfect_accuracy(self):
        assert accuracy_score(["A", "B", "C"], ["A", "B", "C"]) == 1.0

    def test_zero_accuracy(self):
        assert accuracy_score(["A", "B", "C"], ["D", "E", "F"]) == 0.0

    def test_partial_accuracy(self):
        assert accuracy_score(["A", "B", "C"], ["A", "B", "D"]) == 2 / 3

    def test_empty_lists(self):
        assert accuracy_score([], []) == 0.0


class TestPrecisionRecallF1:
    def test_precision_perfect(self):
        assert precision_score(["A", "A", "B"], ["A", "A", "B"], "A") == 1.0

    def test_precision_with_false_positives(self):
        assert precision_score(["A", "B", "B"], ["A", "A", "B"], "A") == 0.5

    def test_recall_perfect(self):
        assert recall_score(["A", "A", "B"], ["A", "A", "B"], "A") == 1.0

    def test_recall_with_false_negatives(self):
        assert recall_score(["A", "A", "B"], ["A", "B", "B"], "A") == 0.5

    def test_f1_perfect(self):
        assert f1_score(["A", "A", "B"], ["A", "A", "B"], "A") == 1.0

    def test_f1_balanced(self):
        # y_true = ["A", "A", "B"], y_pred = ["A", "B", "B"]
        # For class A: TP=1, FP=0, FN=1 -> precision=1, recall=0.5, f1=2/3
        assert f1_score(["A", "A", "B"], ["A", "B", "B"], "A") == 2/3

    def test_zero_division(self):
        assert precision_score(["B", "B"], ["B", "B"], "A") == 0.0
        assert recall_score(["B", "B"], ["B", "B"], "A") == 0.0
        assert f1_score(["B", "B"], ["B", "B"], "A") == 0.0


class TestMacroF1:
    def test_macro_f1_three_classes(self):
        y_true = ["A", "A", "B", "B", "C", "C"]
        y_pred = ["A", "A", "B", "B", "C", "C"]
        assert macro_f1_score(y_true, y_pred, ["A", "B", "C"]) == 1.0

    def test_macro_f1_imperfect(self):
        y_true = ["A", "A", "B", "B"]
        y_pred = ["A", "B", "B", "A"]
        # Class A: prec=0.5, rec=0.5, f1=0.5
        # Class B: prec=0.5, rec=0.5, f1=0.5
        # macro = 0.5
        assert macro_f1_score(y_true, y_pred, ["A", "B"]) == 0.5


class TestHallucinationRate:
    def test_all_supported(self):
        verdicts = [
            PredictedVerdict(claim_text="c1", verdict=Verdict.SUPPORTED),
            PredictedVerdict(claim_text="c2", verdict=Verdict.SUPPORTED),
        ]
        assert hallucination_rate(verdicts) == 0.0

    def test_all_contradicted(self):
        verdicts = [
            PredictedVerdict(claim_text="c1", verdict=Verdict.CONTRADICTED),
            PredictedVerdict(claim_text="c2", verdict=Verdict.CONTRADICTED),
        ]
        assert hallucination_rate(verdicts) == 1.0

    def test_mixed(self):
        verdicts = [
            PredictedVerdict(claim_text="c1", verdict=Verdict.SUPPORTED),
            PredictedVerdict(claim_text="c2", verdict=Verdict.CONTRADICTED),
            PredictedVerdict(claim_text="c3", verdict=Verdict.NOT_ENOUGH_EVIDENCE),
        ]
        # 2 out of 3 are hallucinated
        assert hallucination_rate(verdicts) == 2 / 3

    def test_empty(self):
        assert hallucination_rate([]) == 0.0


class TestCitationCoverage:
    def test_full_coverage(self):
        assert citation_coverage_score(5, 5) == 1.0

    def test_partial_coverage(self):
        assert citation_coverage_score(5, 3) == 0.6

    def test_zero_supported(self):
        assert citation_coverage_score(0, 0) == 1.0

    def test_cap_at_one(self):
        assert citation_coverage_score(3, 5) == 1.0


class TestRiskLevelMatchRate:
    def test_all_match(self):
        assert risk_level_match_rate(["LOW", "MEDIUM", "HIGH"], ["LOW", "MEDIUM", "HIGH"]) == 1.0

    def test_none_match(self):
        assert risk_level_match_rate(["LOW", "MEDIUM"], ["HIGH", "LOW"]) == 0.0

    def test_partial_match(self):
        assert risk_level_match_rate(["LOW", "MEDIUM", "HIGH"], ["LOW", "LOW", "HIGH"]) == 2 / 3

    def test_empty(self):
        assert risk_level_match_rate([], []) == 0.0