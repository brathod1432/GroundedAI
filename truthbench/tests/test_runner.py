"""Tests for runner module."""
from __future__ import annotations

from truthbench.runner import TruthBenchRunner
from truthbench.schemas import EvaluationDataset, EvaluationCase, ExpectedClaim, ExpectedVerdict, Verdict, RiskLevel


def test_load_dataset():
    """Test loading the sample dataset."""
    runner = TruthBenchRunner("datasets/sample_eval_dataset.json")
    dataset = runner.load_dataset()

    assert isinstance(dataset, EvaluationDataset)
    assert len(dataset.cases) == 5
    assert dataset.cases[0].id == "case_001_fully_supported"
    assert dataset.cases[-1].id == "case_005_weak_citations"


def test_generate_mock_predictions():
    """Test mock prediction generation."""
    runner = TruthBenchRunner("datasets/sample_eval_dataset.json")
    runner.load_dataset()
    predictions = runner.generate_mock_predictions()

    assert len(predictions) == 5
    for pred in predictions:
        assert pred.case_id in [c.id for c in runner.dataset.cases]
        assert len(pred.extracted_claims) > 0
        assert len(pred.predicted_verdicts) > 0
        assert 0.0 <= pred.hallucination_risk_score <= 1.0
        assert pred.risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH]


def test_run_evaluation():
    """Test running evaluation with mock predictions."""
    runner = TruthBenchRunner("datasets/sample_eval_dataset.json")
    runner.load_dataset()
    predictions = runner.generate_mock_predictions()
    results = runner.run_evaluation(predictions)

    assert results.total_cases == 5
    assert results.total_claims_evaluated > 0
    assert 0.0 <= results.mean_claim_accuracy <= 1.0
    assert 0.0 <= results.mean_verdict_accuracy <= 1.0
    assert 0.0 <= results.mean_verdict_f1 <= 1.0
    assert 0.0 <= results.mean_hallucination_rate <= 1.0
    assert 0.0 <= results.mean_citation_coverage <= 1.0
    assert 0.0 <= results.risk_level_match_rate <= 1.0
    assert results.passed_cases + results.failed_cases == 5
    assert len(results.case_results) == 5
    assert len(results.recommendations) > 0


def test_aggregate_results():
    """Test result aggregation logic."""
    runner = TruthBenchRunner("datasets/sample_eval_dataset.json")
    runner.load_dataset()
    predictions = runner.generate_mock_predictions()
    results = runner.run_evaluation(predictions)

    # Check that aggregate metrics are means of case results
    case_accs = [c.claim_accuracy for c in results.case_results]
    expected_mean = sum(case_accs) / len(case_accs)
    assert abs(results.mean_claim_accuracy - expected_mean) < 0.01

    case_f1s = [c.verdict_f1 for c in results.case_results]
    expected_mean_f1 = sum(case_f1s) / len(case_f1s)
    assert abs(results.mean_verdict_f1 - expected_mean_f1) < 0.01


def test_recommendations_generated():
    """Test that recommendations are generated."""
    runner = TruthBenchRunner("datasets/sample_eval_dataset.json")
    runner.load_dataset()
    predictions = runner.generate_mock_predictions()
    results = runner.run_evaluation(predictions)

    assert len(results.recommendations) > 0
    for rec in results.recommendations:
        assert isinstance(rec, str)
        assert len(rec) > 0