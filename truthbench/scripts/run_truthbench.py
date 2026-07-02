#!/usr/bin/env python
"""TruthBench CLI - run evaluation benchmark from command line."""

from __future__ import annotations

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from truthbench.runner import run_benchmark
from truthbench.reporter import generate_markdown_report


def main():
    """Run TruthBench evaluation and print summary."""
    print("=" * 60)
    print("TruthBench Evaluation Runner")
    print("=" * 60)
    print()

    # Run benchmark
    print("Loading dataset and running evaluation...")
    aggregate = run_benchmark()

    # Print summary
    print()
    print("=" * 60)
    print("EVALUATION SUMMARY")
    print("=" * 60)
    print(f"Total Cases:          {aggregate.total_cases}")
    print(f"Passed:               {aggregate.passed_cases}")
    print(f"Failed:               {aggregate.failed_cases}")
    print()
    print(f"Claim Extraction Acc: {aggregate.mean_claim_accuracy:.2%}")
    print(f"Verdict Accuracy:     {aggregate.mean_verdict_accuracy:.2%}")
    print(f"Verdict Precision:    {aggregate.mean_verdict_precision:.2%}")
    print(f"Verdict Recall:       {aggregate.mean_verdict_recall:.2%}")
    print(f"Verdict F1 (macro):   {aggregate.mean_verdict_f1:.2%}")
    print(f"Hallucination Rate:   {aggregate.mean_hallucination_rate:.2%}")
    print(f"Citation Coverage:    {aggregate.mean_citation_coverage:.2%}")
    print(f"Risk Level Match:     {aggregate.risk_level_match_rate:.2%}")
    print()

    # Per-case
    print("-" * 60)
    print("PER-CASE RESULTS")
    print("-" * 60)
    for case in aggregate.case_results:
        status = "PASS" if not case.failed_checks else "FAIL"
        print(f"  {case.case_id}: {status} "
              f"(claim_acc={case.claim_accuracy:.0%}, "
              f"verdict_f1={case.verdict_f1:.0%}, "
              f"risk_match={'Y' if case.risk_level_match else 'N'})")
        if case.failed_checks:
            for issue in case.failed_checks:
                print(f"    - {issue}")

    print()
    print("Recommendations:")
    for i, rec in enumerate(aggregate.recommendations, 1):
        print(f"  {i}. {rec}")

    # Generate markdown report
    report_path = Path("reports/generated_evaluation_report.md")
    generate_markdown_report(
        dataset_name="TruthBench Evaluation Dataset",
        dataset_version="0.1.0",
        aggregate=aggregate,
        output_path=str(report_path),
    )
    print(f"\nMarkdown report saved to: {report_path}")

    # Exit code based on results
    if aggregate.failed_cases > 0:
        print("\n[WARNING] Some cases failed - see report for details")
        sys.exit(1)
    else:
        print("\n[OK] All cases passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()