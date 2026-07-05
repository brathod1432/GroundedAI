# Evaluation Plan

Truth Guard is evaluated with Truth Bench, the sibling benchmarking package in this repository. The current dataset is small and is best treated as a smoke benchmark, not as production evidence of model quality.

## Goals

1. Measure whether claim extraction finds the expected factual claims.
2. Measure whether verdicts match labeled ground truth.
3. Check whether risk levels match expected hallucination risk.
4. Track citation coverage for supported claims.
5. Catch regressions as the verification pipeline changes.

## Dataset

Primary dataset:

```text
truthbench/datasets/sample_eval_dataset.json
```

The sample dataset contains five cases:

| Case ID | Description | Expected Risk |
| --- | --- | --- |
| `case_001_fully_supported` | All claims verified | LOW |
| `case_002_one_unsupported_claim` | One unverified claim | MEDIUM |
| `case_003_contradicted_claim` | Factually false claim | HIGH |
| `case_004_mixed_supported_unsupported` | Mix of verified and unverified claims | MEDIUM |
| `case_005_weak_citations` | Correct but weakly cited answer | LOW |

## Metrics

Truth Bench reports:

- Claim extraction accuracy
- Verdict accuracy
- Macro verdict precision
- Macro verdict recall
- Macro verdict F1
- Hallucination rate
- Citation coverage
- Risk-level match rate

## Run Evaluation

From the repository root:

```bash
python -m truthbench.scripts.run_truthbench
```

The command writes:

```text
truthbench/reports/generated_evaluation_report.md
```

It exits with status `1` when any benchmark case fails. The current mock benchmark has one expected failing case caused by over-extraction.

Generate the fixed sample report:

```bash
python -m truthbench.scripts.generate_sample_report
```

## Suggested Gates

For future CI usage, treat these thresholds as starting points:

| Metric | Warning | Blocking |
| --- | --- | --- |
| Verdict Macro F1 | < 0.80 | < 0.70 |
| Claim Extraction F1 | < 0.80 | < 0.70 |
| Risk Level Match | < 0.90 | < 0.80 |
| Citation Coverage | < 0.90 | < 0.80 |

## Limitations

- The current sample has only five cases.
- Truth Bench currently uses mock predictions unless an adapter is added.
- Statistical confidence intervals need a much larger dataset.
- Production monitoring and A/B testing are roadmap items, not implemented behavior.

## Related Documents

- [Truth Bench README](../../truthbench/README.md)
- [Dataset Schema](../../truthbench/datasets/dataset_schema.md)
- [Architecture](architecture.md)
- [Roadmap](roadmap.md)
