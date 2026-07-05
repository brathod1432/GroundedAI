# Truth Bench

Truth Bench is a Python benchmarking toolkit for hallucination-reduction systems. It loads labeled evaluation cases, compares predicted claims and verdicts against expected results, and writes an evaluation report.

The current benchmark uses deterministic mock predictions, so it can run locally without API keys or external services.

## Main Files

| Path | Purpose |
| --- | --- |
| `runner.py` | Loads datasets, creates mock predictions, runs evaluators, and aggregates results. |
| `schemas.py` | Pydantic models for datasets, predictions, and reports. |
| `metrics.py` | Shared metric helpers for precision, recall, F1, and averages. |
| `reporter.py` | Generates Markdown and JSON evaluation reports. |
| `evaluators/` | Evaluators for claim accuracy, verdict consistency, hallucination risk, and citation quality. |
| `scripts/run_truthbench.py` | Runs the bundled sample benchmark. |
| `scripts/generate_sample_report.py` | Generates a fixed sample report. |
| `datasets/sample_eval_dataset.json` | Default dataset with five labeled cases. |
| `datasets/dataset_schema.md` | Dataset schema reference. |
| `tests/` | Unit tests for runner, metrics, and evaluators. |

## Setup

From the repository root:

```bash
python -m pip install -r truthbench/requirements.txt
```

## Configuration

Truth Bench works with defaults. To customize settings, copy `truthbench/.env.example` to `truthbench/.env`.

| Variable | Default | Purpose |
| --- | --- | --- |
| `DATASET_PATH` | `datasets/sample_eval_dataset.json` | Dataset path. Relative paths resolve from the package first. |
| `VERDICT_LABELS` | `["SUPPORTED","CONTRADICTED","NOT_ENOUGH_EVIDENCE"]` | Supported verdict labels. |
| `RISK_LEVELS` | `["LOW","MEDIUM","HIGH"]` | Supported risk levels. |
| `CONFIDENCE_THRESHOLD` | `0.7` | Threshold available to evaluators. |
| `EVALUATION_SEED` | `42` | Seed for deterministic mock predictions. |
| `REPORT_OUTPUT_DIR` | `reports` | Generated report directory. |
| `REPORT_FORMAT` | `markdown` | Preferred report format setting. |
| `LOG_LEVEL` | `INFO` | Logging verbosity. |

Do not commit real local `.env` files.

## How To Run

Run the benchmark from the repository root:

```bash
python -m truthbench.scripts.run_truthbench
```

The command prints a summary and writes:

```text
truthbench/reports/generated_evaluation_report.md
```

It exits with status `1` if any benchmark case fails. In the current mock benchmark, one case fails because the mock system intentionally extracts an extra claim.

Generate a sample report:

```bash
python -m truthbench.scripts.generate_sample_report
```

## Inputs And Outputs

Input is a JSON dataset with this top-level shape:

```json
{
  "name": "TruthBench Evaluation Dataset",
  "version": "0.1.0",
  "description": "Dataset description",
  "cases": []
}
```

Each case contains:

- `id`
- `original_question`
- `generated_answer`
- `expected_claims`
- `expected_verdicts`
- `trusted_reference_evidence`
- `expected_risk_level`
- `notes`

Output metrics include claim extraction accuracy, verdict accuracy, verdict precision, verdict recall, verdict F1, hallucination rate, citation coverage, and risk-level match rate.

## Example Output

```text
Total Cases:          5
Passed:               4
Failed:               1
Claim Extraction Acc: 100.00%
Verdict Accuracy:     100.00%
Hallucination Rate:   40.00%
Citation Coverage:    20.00%
Risk Level Match:     100.00%
```

## Testing

From the repository root:

```bash
python -m pytest truthbench/tests -v
```

## Current Limitations

- The benchmark currently uses mock predictions instead of calling a real verification system.
- The bundled dataset is intentionally small and is not a production benchmark.
- There is no CLI argument parser; dataset and report paths are configured through settings.
- Generated reports are file-based and there is no comparison dashboard.

## Suggested Improvements

- Add an adapter interface so Truth Bench can evaluate Truth Guard or another verifier directly.
- Add CLI arguments for dataset path, output path, report format, and seed.
- Expand datasets with domain-specific and adversarial examples.
- Emit JSON reports by default alongside Markdown.
- Add confidence intervals for repeated evaluation runs against non-deterministic systems.

## License

The package metadata declares MIT, but this repository does not currently include a license file.
