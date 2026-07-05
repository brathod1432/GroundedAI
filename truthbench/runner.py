"""TruthBench evaluation runner - orchestrates the full evaluation pipeline."""
from __future__ import annotations

import json
import random
from pathlib import Path

from truthbench.config import settings
from truthbench.evaluators.claim_accuracy_evaluator import (
    claim_accuracy_simple,
    evaluate_claim_accuracy,
)
from truthbench.evaluators.citation_quality_evaluator import (
    citation_coverage_score,
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
    AggregateEvaluationResult,
    CaseEvaluationResult,
    EvaluationCase,
    EvaluationDataset,
    PredictedClaim,
    PredictedResult,
    PredictedVerdict,
    RiskLevel,
    Verdict,
)


class TruthBenchRunner:
    """Main evaluation runner for TruthBench."""

    def __init__(self, dataset_path: str | None = None):
        self.dataset_path = settings.resolve_path(dataset_path) if dataset_path else settings.get_dataset_path()
        self.dataset: EvaluationDataset | None = None
        self._rng = random.Random(settings.evaluation_seed)

    def load_dataset(self) -> EvaluationDataset:
        """Load evaluation dataset from JSON file."""
        path = Path(self.dataset_path)
        if not path.exists():
            raise FileNotFoundError(f"Dataset not found: {self.dataset_path}")

        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        self.dataset = EvaluationDataset(**data)
        return self.dataset

    def generate_mock_predictions(self) -> list[PredictedResult]:
        """
        Generate mock predictions for testing.

        In real usage, this would be replaced by calling the system under test
        (e.g., TruthGuardAPI) for each case.
        """
        if not self.dataset:
            self.load_dataset()

        predictions = []

        for case in self.dataset.cases:
            # Simulate a system that mostly gets it right but makes some errors
            predicted = self._mock_predict(case)
            predictions.append(predicted)

        return predictions

    def _mock_predict(self, case: EvaluationCase) -> PredictedResult:
        """Generate a mock prediction for a single case."""
        # Extract claims (simulate extraction - mostly correct)
        extracted_claims = []
        for i, exp_claim in enumerate(case.expected_claims):
            extracted_claims.append(
                PredictedClaim(
                    text=exp_claim.text,
                    claim_type=exp_claim.claim_type,
                    confidence=0.95,
                )
            )

        # Ensure at least one claim is present
        if not extracted_claims:
            extracted_claims.append(PredictedClaim(text="Dummy claim", claim_type="factual", confidence=0.9))
        # Add one spurious claim for some cases (simulate over-extraction)
        if case.id == "case_002_one_unsupported_claim":
            extracted_claims.append(
                PredictedClaim(
                    text="Germany also exports significant amounts of beer.",
                    claim_type="statistical",
                    confidence=0.7,
                )
            )

        # Predict verdicts (mostly correct but with some errors)
        predicted_verdicts = []
        for exp_verdict in case.expected_verdicts:
            # Simulate correct prediction 80% of the time
            # import random
            if self._rng.random() < 0.8:
                pred_verdict = exp_verdict.verdict
                pred_confidence = exp_verdict.confidence
            else:
                # Wrong prediction
                pred_verdict = self._wrong_verdict(exp_verdict.verdict)
                pred_confidence = 0.6

            predicted_verdicts.append(
                PredictedVerdict(
                    claim_text=exp_verdict.claim_text,
                    verdict=pred_verdict,
                    confidence=pred_confidence,
                    reasoning=(
                        exp_verdict.reasoning
                        if pred_verdict == exp_verdict.verdict
                        else "Mock incorrect reasoning"
                    ),
                )
            )

        # Ensure at least one verdict is present
        if not predicted_verdicts:
            predicted_verdicts.append(PredictedVerdict(
                claim_text="Dummy claim",
                verdict=Verdict.SUPPORTED,
                confidence=1.0,
                reasoning="Dummy verdict",
            ))
        # Risk level (mostly correct)
        predicted_risk = case.expected_risk_level
        if case.id == "case_004_mixed_claims":
            predicted_risk = RiskLevel.HIGH  # Over-estimate risk

        # Hallucination risk score
        risk_scores = {"LOW": 0.1, "MEDIUM": 0.4, "HIGH": 0.7}
        risk_score = risk_scores.get(predicted_risk.value, 0.3)

        return PredictedResult(
            case_id=case.id,
            extracted_claims=extracted_claims,
            predicted_verdicts=predicted_verdicts,
            hallucination_risk_score=risk_score,
            risk_level=predicted_risk,
            citations=["wikipedia.org", "worldbank.org"] if case.expected_verdicts else [],
            processing_time_ms=self._rng.randint(500, 2000),
        )

    def _wrong_verdict(self, correct: str) -> str:
        """Return a wrong verdict for simulation."""
        options = ["SUPPORTED", "CONTRADICTED", "NOT_ENOUGH_EVIDENCE"]
        options.remove(correct)
        return self._rng.choice(options)

    def run_evaluation(
        self,
        predictions: list[PredictedResult] | None = None,
    ) -> AggregateEvaluationResult:
        """Run full evaluation on predictions."""
        if not self.dataset:
            self.load_dataset()

        if predictions is None:
            predictions = self.generate_mock_predictions()

        case_results = []

        for case in self.dataset.cases:
            pred = next((p for p in predictions if p.case_id == case.id), None)
            if not pred:
                continue

            # Run all evaluators
            claim_acc, claim_prec, claim_rec, claim_f1, claim_issues = evaluate_claim_accuracy(case, pred)
            verdict_acc, verdict_prec, verdict_rec, verdict_f1, verdict_issues = evaluate_verdict_consistency(case, pred)
            hall_rate = hallucination_rate(pred.predicted_verdicts)
            citation_cov = citation_coverage_score(
                sum(1 for v in pred.predicted_verdicts if v.verdict.value == "SUPPORTED"),
                sum(1 for v in pred.predicted_verdicts if v.verdict.value == "SUPPORTED" and v.evidence_indices)
            )
            risk_match, risk_diff, risk_issues = evaluate_hallucination_risk(case, pred)

            all_issues = claim_issues + verdict_issues + risk_issues

            case_result = CaseEvaluationResult(
                case_id=case.id,
                claim_accuracy=claim_acc,
                verdict_accuracy=verdict_acc,
                verdict_precision=verdict_prec,
                verdict_recall=verdict_rec,
                verdict_f1=verdict_f1,
                hallucination_rate=hall_rate,
                citation_coverage=citation_cov,
                risk_level_match=risk_match,
                failed_checks=all_issues,
            )
            case_results.append(case_result)

        # Aggregate
        aggregate = self._aggregate_results(case_results)
        return aggregate

    def _aggregate_results(
        self,
        case_results: list[CaseEvaluationResult],
    ) -> AggregateEvaluationResult:
        """Aggregate case-level results into overall metrics."""
        if not case_results:
            return AggregateEvaluationResult(
                total_cases=0,
                total_claims_evaluated=0,
                mean_claim_accuracy=0.0,
                mean_verdict_accuracy=0.0,
                mean_verdict_precision=0.0,
                mean_verdict_recall=0.0,
                mean_verdict_f1=0.0,
                mean_hallucination_rate=0.0,
                mean_citation_coverage=0.0,
                risk_level_match_rate=0.0,
                passed_cases=0,
                failed_cases=0,
                case_results=[],
                recommendations=[],
            )

        n = len(case_results)

        aggregate = AggregateEvaluationResult(
            total_cases=n,
            total_claims_evaluated=sum(len(c.failed_checks) + 1 for c in case_results),  # rough estimate
            mean_claim_accuracy=sum(c.claim_accuracy for c in case_results) / n,
            mean_verdict_accuracy=sum(c.verdict_accuracy for c in case_results) / n,
            mean_verdict_precision=sum(c.verdict_precision for c in case_results) / n,
            mean_verdict_recall=sum(c.verdict_recall for c in case_results) / n,
            mean_verdict_f1=sum(c.verdict_f1 for c in case_results) / n,
            mean_hallucination_rate=sum(c.hallucination_rate for c in case_results) / n,
            mean_citation_coverage=sum(c.citation_coverage for c in case_results) / n,
            risk_level_match_rate=sum(1 for c in case_results if c.risk_level_match) / n,
            passed_cases=sum(1 for c in case_results if not c.failed_checks),
            failed_cases=sum(1 for c in case_results if c.failed_checks),
            case_results=case_results,
            recommendations=self._generate_recommendations(case_results),
        )
        return aggregate

    def _generate_recommendations(self, case_results: list[CaseEvaluationResult]) -> list[str]:
        """Generate improvement recommendations based on results."""
        recs = []

        avg_claim_acc = sum(c.claim_accuracy for c in case_results) / len(case_results)
        avg_verdict_f1 = sum(c.verdict_f1 for c in case_results) / len(case_results)
        avg_citation_cov = sum(c.citation_coverage for c in case_results) / len(case_results)
        risk_match_rate = sum(1 for c in case_results if c.risk_level_match) / len(case_results)

        if avg_claim_acc < 0.8:
            recs.append("Improve claim extraction: missing expected claims or extracting spurious claims")

        if avg_verdict_f1 < 0.75:
            recs.append("Improve verdict prediction accuracy - consider better evidence retrieval or verification logic")

        if avg_citation_cov < 0.8:
            recs.append("Increase citation coverage for supported claims - ensure every supported claim has at least one citation")

        if risk_match_rate < 0.8:
            recs.append("Calibrate hallucination risk scoring - predicted risk levels don't match expected")

        # Check specific failure patterns
        claim_missed = any("missed" in issue for c in case_results for issue in c.failed_checks)
        if claim_missed:
            recs.append("Review claim extraction patterns - some factual claims are being missed")

        extra_claims = any("extra claims" in issue.lower() for c in case_results for issue in c.failed_checks)
        if extra_claims:
            recs.append("Reduce over-extraction - system is extracting non-factual statements as claims")

        return recs


def run_benchmark(dataset_path: str | None = None) -> AggregateEvaluationResult:
    """Convenience function to run the full benchmark."""
    runner = TruthBenchRunner(dataset_path)
    runner.load_dataset()
    predictions = runner.generate_mock_predictions()
    return runner.run_evaluation(predictions)
