#!/usr/bin/env python
"""Generate a sample evaluation report for documentation purposes."""

from __future__ import annotations

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from truthbench.reporter import generate_markdown_report
from truthbench.schemas import (
    AggregateEvaluationResult,
    CaseEvaluationResult,
    RiskLevel,
    Verdict,
)


def main():
    """Generate a realistic sample report for documentation."""
    # Create sample aggregate results
    case_results = [
        CaseEvaluationResult(
            case_id="case_001_fully_supported",
            claim_accuracy=1.0,
            verdict_accuracy=1.0,
            verdict_precision=1.0,
            verdict_recall=1.0,
            verdict_f1=1.0,
            hallucination_rate=0.0,
            citation_coverage=1.0,
            risk_level_match=True,
            failed_checks=[],
        ),
        CaseEvaluationResult(
            case_id="case_002_one_unsupported_claim",
            claim_accuracy=1.0,
            verdict_accuracy=0.5,
            verdict_precision=0.67,
            verdict_recall=0.5,
            verdict_f1=0.57,
            hallucination_rate=0.5,
            citation_coverage=0.5,
            risk_level_match=True,
            failed_checks=[
                "Verdict mismatch for claim: The country also exports significant amounts of chocolate"
            ],
        ),
        CaseEvaluationResult(
            case_id="case_003_contradicted_claim",
            claim_accuracy=1.0,
            verdict_accuracy=1.0,
            verdict_precision=1.0,
            verdict_recall=1.0,
            verdict_f1=1.0,
            hallucination_rate=1.0,
            citation_coverage=1.0,
            risk_level_match=True,
            failed_checks=[],
        ),
        CaseEvaluationResult(
            case_id="case_004_mixed_supported_unsupported",
            claim_accuracy=0.75,
            verdict_accuracy=0.5,
            verdict_precision=0.5,
            verdict_recall=0.5,
            verdict_f1=0.5,
            hallucination_rate=0.5,
            citation_coverage=0.5,
            risk_level_match=False,
            failed_checks=[
                "Missed 1 expected claims",
                "Risk level mismatch: expected MEDIUM, got HIGH",
                "1 supported claim(s) missing citations"
            ],
        ),
        CaseEvaluationResult(
            case_id="case_005_weak_citations",
            claim_accuracy=1.0,
            verdict_accuracy=1.0,
            verdict_precision=1.0,
            verdict_recall=1.0,
            verdict_f1=1.0,
            hallucination_rate=0.0,
            citation_coverage=0.0,
            risk_level_match=True,
            failed_checks=[
                "2 supported claim(s) missing citations"
            ],
        ),
    ]

    aggregate = AggregateEvaluationResult(
        total_cases=5,
        total_claims_evaluated=11,
        mean_claim_accuracy=0.95,
        mean_verdict_accuracy=0.80,
        mean_verdict_precision=0.73,
        mean_verdict_recall=0.70,
        mean_verdict_f1=0.71,
        mean_hallucination_rate=0.40,
        mean_citation_coverage=0.60,
        risk_level_match_rate=0.80,
        passed_cases=2,
        failed_cases=3,
        case_results=case_results,
        recommendations=[
            "Improve verdict prediction accuracy - consider better evidence retrieval or verification logic",
            "Increase citation coverage for supported claims - ensure every supported claim has at least one citation",
            "Calibrate hallucination risk scoring - predicted risk levels don't match expected",
            "Review claim extraction patterns - some factual claims are being missed",
        ],
    )

    # Generate report
    report_path = Path("reports/sample_evaluation_report.md")
    generate_markdown_report(
        dataset_name="TruthBench Evaluation Dataset",
        dataset_version="0.1.0",
        aggregate=aggregate,
        output_path=str(report_path),
    )
    print(f"Sample report generated at: {report_path}")
    print("Done!")


if __name__ == "__main__":
    main()