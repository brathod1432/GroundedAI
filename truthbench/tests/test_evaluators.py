"""Tests for evaluator modules."""
from __future__ import annotations

from truthbench.evaluators.claim_accuracy_evaluator import (
    claim_accuracy_simple,
    evaluate_claim_accuracy,
)
from truthbench.evaluators.citation_quality_evaluator import (
    citation_coverage_score,
    evaluate_citation_quality,
)
from truthbench.evaluators.hallucination_risk_evaluator import (
    evaluate_hallucination_risk,
    hallucination_rate,
)
from truthbench.evaluators.verdict_consistency_evaluator import (
    evaluate_verdict_consistency,
    verdict_accuracy,
)
from truthbench.schemas import (
    EvaluationCase,
    ExpectedClaim,
    ExpectedVerdict,
    PredictedClaim,
    PredictedResult,
    PredictedVerdict,
    RiskLevel,
    Verdict,
)


def create_test_case() -> EvaluationCase:
    """Create a test evaluation case."""
    return EvaluationCase(
        id="test_case",
        original_question="Test question?",
        generated_answer="Test answer with claims.",
        expected_claims=[
            ExpectedClaim(text="Claim 1: The sky is blue.", claim_type="factual"),
            ExpectedClaim(text="Claim 2: Water boils at 100°C.", claim_type="factual"),
        ],
        expected_verdicts=[
            ExpectedVerdict(claim_text="Claim 1: The sky is blue.", verdict=Verdict.SUPPORTED, confidence=0.9),
            ExpectedVerdict(claim_text="Claim 2: Water boils at 100°C.", verdict=Verdict.SUPPORTED, confidence=0.95),
        ],
        trusted_reference_evidence=["https://example.com"],
        expected_risk_level=RiskLevel.LOW,
    )


def create_perfect_prediction() -> PredictedResult:
    """Create a perfect prediction matching the test case."""
    return PredictedResult(
        case_id="test_case",
        extracted_claims=[
            PredictedClaim(text="Claim 1: The sky is blue.", claim_type="factual"),
            PredictedClaim(text="Claim 2: Water boils at 100°C.", claim_type="factual"),
        ],
        predicted_verdicts=[
            PredictedVerdict(claim_text="Claim 1: The sky is blue.", verdict=Verdict.SUPPORTED, evidence_indices=[0]),
            PredictedVerdict(claim_text="Claim 2: Water boils at 100°C.", verdict=Verdict.SUPPORTED, evidence_indices=[1]),
        ],
        hallucination_risk_score=0.1,
        risk_level=RiskLevel.LOW,
        citations=["source1", "source2"],
    )


def create_imperfect_prediction() -> PredictedResult:
    """Create an imperfect prediction with errors."""
    return PredictedResult(
        case_id="test_case",
        extracted_claims=[
            PredictedClaim(text="Claim 1: The sky is blue.", claim_type="factual"),
            PredictedClaim(text="Extra claim not expected.", claim_type="factual"),
        ],
        predicted_verdicts=[
            PredictedVerdict(claim_text="Claim 1: The sky is blue.", verdict=Verdict.SUPPORTED, evidence_indices=[0]),
            PredictedVerdict(claim_text="Claim 2: Water boils at 100°C.", verdict=Verdict.CONTRADICTED, evidence_indices=[]),
            PredictedVerdict(claim_text="Extra claim not expected.", verdict=Verdict.NOT_ENOUGH_EVIDENCE, evidence_indices=[]),
        ],
        hallucination_risk_score=0.7,
        risk_level=RiskLevel.HIGH,
        citations=["source1"],
    )


class TestClaimAccuracyEvaluator:
    def test_perfect_match(self):
        case = create_test_case()
        pred = create_perfect_prediction()
        acc, prec, rec, f1, issues = evaluate_claim_accuracy(case, pred)

        assert acc == 1.0
        assert prec == 1.0
        assert rec == 1.0
        assert f1 == 1.0
        assert len(issues) == 0

    def test_missed_claim(self):
        case = create_test_case()
        pred = create_imperfect_prediction()
        acc, prec, rec, f1, issues = evaluate_claim_accuracy(case, pred)

        assert acc < 1.0  # missed one expected claim
        assert any("missed" in issue.lower() for issue in issues)

    def test_extra_claim(self):
        case = create_test_case()
        pred = create_imperfect_prediction()
        acc, prec, rec, f1, issues = evaluate_claim_accuracy(case, pred)

        assert any("extra" in issue.lower() for issue in issues)

    def test_simple_accuracy(self):
        case = create_test_case()
        pred = create_perfect_prediction()
        assert claim_accuracy_simple(case, pred) == 1.0


class TestCitationQualityEvaluator:
    def test_full_coverage(self):
        coverage = citation_coverage_score(3, 3)
        assert coverage == 1.0

    def test_partial_coverage(self):
        coverage = citation_coverage_score(3, 2)
        assert coverage == 2 / 3

    def test_zero_supported(self):
        coverage = citation_coverage_score(0, 0)
        assert coverage == 1.0

    def test_evaluate_perfect(self):
        case = create_test_case()
        pred = create_perfect_prediction()
        coverage, issues = evaluate_citation_quality(case, pred)

        assert coverage == 1.0
        assert len(issues) == 0

    def test_evaluate_missing_citations(self):
        case = create_test_case()
        pred = PredictedResult(
            case_id="test_case",
            extracted_claims=[
                PredictedClaim(text="Claim 1", claim_type="factual"),
                PredictedClaim(text="Claim 2", claim_type="factual"),
            ],
            predicted_verdicts=[
                PredictedVerdict(claim_text="Claim 1", verdict=Verdict.SUPPORTED, evidence_indices=[]),
                PredictedVerdict(claim_text="Claim 2", verdict=Verdict.SUPPORTED, evidence_indices=[0]),
            ],
            hallucination_risk_score=0.3,
            risk_level=RiskLevel.LOW,
            citations=[],
        )
        coverage, issues = evaluate_citation_quality(case, pred)

        assert coverage < 1.0
        assert any("missing" in issue.lower() for issue in issues)


class TestHallucinationRiskEvaluator:
    def test_hallucination_rate_all_supported(self):
        pred = PredictedResult(
            case_id="test",
            predicted_verdicts=[
                PredictedVerdict(claim_text="c1", verdict=Verdict.SUPPORTED),
                PredictedVerdict(claim_text="c2", verdict=Verdict.SUPPORTED),
            ],
        )
        assert hallucination_rate(pred) == 0.0

    def test_hallucination_rate_all_contradicted(self):
        pred = PredictedResult(
            case_id="test",
            predicted_verdicts=[
                PredictedVerdict(claim_text="c1", verdict=Verdict.CONTRADICTED),
                PredictedVerdict(claim_text="c2", verdict=Verdict.CONTRADICTED),
            ],
        )
        assert hallucination_rate(pred) == 1.0

    def test_hallucination_rate_mixed(self):
        pred = PredictedResult(
            case_id="test",
            predicted_verdicts=[
                PredictedVerdict(claim_text="c1", verdict=Verdict.SUPPORTED),
                PredictedVerdict(claim_text="c2", verdict=Verdict.CONTRADICTED),
                PredictedVerdict(claim_text="c3", verdict=Verdict.NOT_ENOUGH_EVIDENCE),
            ],
        )
        assert hallucination_rate(pred) == 2 / 3

    def test_evaluate_risk_level_match(self):
        case = EvaluationCase(
            id="test",
            original_question="Q",
            generated_answer="A",
            expected_claims=[],
            expected_verdicts=[],
            expected_risk_level=RiskLevel.LOW,
        )
        pred = PredictedResult(
            case_id="test",
            hallucination_risk_score=0.15,
            risk_level=RiskLevel.LOW,
        )
        match, diff, issues = evaluate_hallucination_risk(case, pred)

        assert match is True
        assert diff < 0.3
        assert len(issues) == 0

    def test_evaluate_risk_level_mismatch(self):
        case = EvaluationCase(
            id="test",
            original_question="Q",
            generated_answer="A",
            expected_claims=[],
            expected_verdicts=[],
            expected_risk_level=RiskLevel.LOW,
        )
        pred = PredictedResult(
            case_id="test",
            hallucination_risk_score=0.8,
            risk_level=RiskLevel.HIGH,
        )
        match, diff, issues = evaluate_hallucination_risk(case, pred)

        assert match is False
        assert diff > 0.3
        assert any("mismatch" in issue.lower() for issue in issues)


class TestVerdictConsistencyEvaluator:
    def test_perfect_match(self):
        case = create_test_case()
        pred = create_perfect_prediction()
        acc, prec, rec, f1, issues = evaluate_verdict_consistency(case, pred)

        assert acc == 1.0
        assert prec == 1.0
        assert rec == 1.0
        assert f1 == 1.0
        assert len(issues) == 0

    def test_wrong_verdict(self):
        case = create_test_case()
        pred = create_imperfect_prediction()
        acc, prec, rec, f1, issues = evaluate_verdict_consistency(case, pred)

        assert acc < 1.0
        assert f1 < 1.0

    def test_simple_accuracy(self):
        case = create_test_case()
        pred = create_perfect_prediction()
        assert verdict_accuracy(case, pred) == 1.0

    def test_no_overlap(self):
        case = EvaluationCase(
            id="test",
            original_question="Q",
            generated_answer="A",
            expected_claims=[],
            expected_verdicts=[ExpectedVerdict(claim_text="Expected claim", verdict=Verdict.SUPPORTED)],
            expected_risk_level=RiskLevel.LOW,
        )
        pred = PredictedResult(
            case_id="test",
            predicted_verdicts=[PredictedVerdict(claim_text="Different claim", verdict=Verdict.SUPPORTED)],
        )
        assert verdict_accuracy(case, pred) == 0.0