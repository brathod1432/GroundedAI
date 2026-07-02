# TruthBench: Evaluation Toolkit for Hallucination-Reduction Systems

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## What is TruthBench?

TruthBench is a comprehensive evaluation and benchmarking toolkit designed to measure the effectiveness of hallucination-reduction systems like TruthGuardAI. While TruthGuardAI **verifies** claims and detects hallucinations, TruthBench **evaluates** how well those verification systems actually work.

Think of it as the "test suite" for your hallucination detection pipeline.

---

## Why Hallucination Evaluation Matters

LLM hallucination reduction systems make critical decisions:
- Is this claim supported by evidence?
- Should this citation be trusted?
- What's the overall risk level of this response?

Without systematic evaluation, you cannot:
- Compare different verification approaches
- Detect regressions when updating your pipeline
- Prove your system works to stakeholders
- Identify specific failure modes to improve

TruthBench provides standardized metrics, datasets, and reporting to close this gap.

---

## Connection to TruthGuardAI

| Component | TruthGuardAI | TruthBench |
|-----------|--------------|------------|
| **Role** | Production verification system | Evaluation & benchmarking toolkit |
| **Input** | User question + LLM answer | Evaluation dataset with ground truth |
| **Output** | Verification report with verdicts | Aggregate metrics + failure analysis |
| **Use Case** | Runtime hallucination detection | Development, testing, CI/CD, research |

TruthBench can evaluate **any** hallucination-reduction system that produces:
- Extracted claims
- Per-claim verdicts (SUPPORTED/CONTRADICTED/NOT_ENOUGH_EVIDENCE)
- Hallucination risk score (0-1)
- Risk level (LOW/MEDIUM/HIGH)
- Citations

---

## Dataset Format

TruthBench uses a structured JSON dataset with ground-truth annotations:

```json
{
  "name": "TruthBench Evaluation Dataset",
  "version": "0.1.0",
  "cases": [
    {
      "id": "case_001_fully_supported",
      "original_question": "What is the capital of France?",
      "generated_answer": "The capital of France is Paris. Population: 2.1M.",
      "expected_claims": [
        {"text": "The capital of France is Paris.", "claim_type": "factual"},
        {"text": "Population: 2.1M.", "claim_type": "statistical"}
      ],
      "expected_verdicts": [
        {"claim_text": "The capital of France is Paris.", "verdict": "SUPPORTED", "confidence": 1.0},
        {"claim_text": "Population: 2.1M.", "verdict": "SUPPORTED", "confidence": 0.9}
      ],
      "trusted_reference_evidence": ["https://en.wikipedia.org/wiki/Paris"],
      "expected_risk_level": "LOW",
      "notes": "Fully supported answer"
    }
  ]
}
```

### Verdict Labels
- **SUPPORTED**: Claim is factually correct with strong evidence
- **CONTRADICTED**: Claim is factually incorrect, contradicted by evidence
- **NOT_ENOUGH_EVIDENCE**: Claim cannot be verified/refuted with available sources

### Risk Levels
- **LOW**: All claims supported, high confidence
- **MEDIUM**: Mix of supported and unverified claims
- **HIGH**: Any contradicted claim or multiple unverified claims

See [datasets/README.md](datasets/README.md) and [datasets/dataset_schema.md](datasets/dataset_schema.md) for full documentation.

---

## Metrics Explained

| Metric | Formula | Interpretation |
|--------|---------|----------------|
| **Claim Extraction Accuracy** | TP / Expected Claims | How well the system finds the right claims |
| **Verdict Accuracy** | Correct Verdicts / Total Overlapping Claims | Overall verdict correctness |
| **Verdict Precision (macro)** | Avg per-class precision | Avoids false positive verdicts |
| **Verdict Recall (macro)** | Avg per-class recall | Avoids missing true verdicts |
| **Verdict F1 (macro)** | Harmonic mean of P/R | Balanced verdict quality |
| **Hallucination Rate** | (CONTRADICTED + NOT_ENOUGH_EVIDENCE) / Total Claims | Fraction of unverified/refuted claims |
| **Citation Coverage** | Cited Supported Claims / Total Supported Claims | Fraction of supported claims with citations |
| **Risk Level Match Rate** | Exact Risk Level Matches / Total Cases | Risk calibration quality |

---

## Quick Start

### Installation

```bash
# From the repository root
pip install -e .[eval]
# Or directly in truthbench
cd truthbench
pip install -r requirements.txt
```

### Run Evaluation

```bash
# Run full benchmark with mock predictions
python -m truthbench.scripts.run_truthbench

# Generate sample report for documentation
python -m truthbench.scripts.generate_sample_report
```

### Run Tests

```bash
pytest truthbench/tests -v
```

---

## Example Output

```
============================================================
EVALUATION SUMMARY
============================================================
Total Cases:          5
Passed:               2
Failed:               3

Claim Extraction Acc: 95.00%
Verdict Accuracy:     80.00%
Verdict Precision:    73.33%
Verdict Recall:       70.00%
Verdict F1 (macro):   71.43%
Hallucination Rate:   40.00%
Citation Coverage:    60.00%
Risk Level Match:     80.00%

PER-CASE RESULTS
------------------------------------------------------------
  case_001_fully_supported: PASS (claim_acc=100%, verdict_f1=100%, risk_match=Y)
  case_002_one_unsupported_claim: FAIL (claim_acc=100%, verdict_f1=57%, risk_match=Y)
    - Verdict mismatch for claim: The country also exports significant amounts of chocolate
  case_003_contradicted_claim: PASS (claim_acc=100%, verdict_f1=100%, risk_match=Y)
  case_004_mixed_supported_unsupported: FAIL (claim_acc=75%, verdict_f1=50%, risk_match=N)
    - Missed 1 expected claims
    - Risk level mismatch: expected MEDIUM, got HIGH
    - 1 supported claim(s) missing citations
  case_005_weak_citations: FAIL (claim_acc=100%, verdict_f1=100%, risk_match=Y)
    - 2 supported claim(s) missing citations

Recommendations:
  1. Improve verdict prediction accuracy - consider better evidence retrieval or verification logic
  2. Increase citation coverage for supported claims - ensure every supported claim has at least one citation
  3. Calibrate hallucination risk scoring - predicted risk levels don't match expected
  4. Review claim extraction patterns - some factual claims are being missed
```

A detailed markdown report is saved to `reports/generated_evaluation_report.md`.

---

## Integrating with CI/CD

Add to your GitHub Actions workflow:

```yaml
- name: Run TruthBench Evaluation
  run: |
    cd truthbench
    python -m truthbench.scripts.run_truthbench
  # Fails if any test cases fail (exit code 1)
```

---

## Future Roadmap

- [ ] **Real system adapter** - Pluggable interface for TruthGuardAI, RAGAS, custom pipelines
- [ ] **Statistical significance testing** - Bootstrap confidence intervals for metrics
- [ ] **Larger curated datasets** - Domain-specific benchmarks (medical, legal, financial)
- [ ] **Adversarial test cases** - Targeted stress tests for known failure modes
- [ ] **Leaderboard mode** - Compare multiple systems on same dataset
- [ ] **Interactive dashboard** - Web UI for exploring results
- [ ] **Drift detection** - Monitor production system performance over time
- [ ] **Cost-aware evaluation** - Track API costs per evaluation run

---

## Resume / CV Value

TruthBench demonstrates:

| Skill Area | Evidence |
|------------|----------|
| **Evaluation Engineering** | Built complete benchmarking framework with standardized metrics |
| **ML/AI Quality Assurance** | Designed test datasets with ground truth for hallucination detection |
| **Software Architecture** | Clean separation: datasets, evaluators, metrics, runner, reporter |
| **Python Best Practices** | Pydantic models, type hints, pytest, CLI scripts, modular design |
| **Documentation** | Comprehensive docs: schema, metrics, dataset guidelines, reports |
| **CI/CD Integration** | Exit codes, JSON/Markdown reports, automation-ready |

---

## License

MIT License - see LICENSE file for details.