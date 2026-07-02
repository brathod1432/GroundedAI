# Evaluation Plan

## Overview

TruthGuardAI's effectiveness is measured by **TruthBench** (separate package). This document defines the evaluation methodology, metrics, and acceptance criteria.

## Evaluation Goals

1. **Claim Extraction Quality**: Does the system find the right claims?
2. **Verdict Accuracy**: Are verdicts correct vs. ground truth?
3. **Risk Calibration**: Does risk score match actual hallucination rate?
4. **Citation Quality**: Are citations relevant and accurate?
5. **Regression Detection**: Catch performance degradation early

## Datasets

### Primary: TruthBench Sample Dataset (`truthbench/datasets/sample_eval_dataset.json`)

| Case ID | Description | Expected Risk |
|---------|-------------|---------------|
| `case_001_fully_supported` | All claims verified | LOW |
| `case_002_one_unsupported_claim` | One unverified claim | MEDIUM |
| `case_003_contradicted_claim` | Factually false claim | HIGH |
| `case_004_mixed_supported_unsupported` | Mix of verified/unverified | MEDIUM |
| `case_005_weak_citations` | Correct but uncited | LOW |

**Total**: 5 cases, 11 claims, 3 verdict types, 3 risk levels

### Future Datasets (Planned)

| Dataset | Domain | Size | Status |
|---------|--------|------|--------|
| Medical QA | Healthcare | 200 cases | Planned |
| Legal QA | Legal | 150 cases | Planned |
| Financial QA | Finance | 100 cases | Planned |
| Adversarial | Stress test | 50 cases | Planned |

## Metrics

### Claim Extraction Metrics

| Metric | Formula | Target |
|--------|---------|--------|
| **Accuracy** | TP / Expected Claims | ≥ 0.85 |
| **Precision** | TP / (TP + FP) | ≥ 0.80 |
| **Recall** | TP / (TP + FN) | ≥ 0.85 |
| **F1** | 2 × P × R / (P + R) | ≥ 0.82 |

### Verdict Metrics

| Metric | Formula | Target |
|--------|---------|--------|
| **Accuracy** | Correct / Total Overlapping | ≥ 0.85 |
| **Macro Precision** | Avg per-class precision | ≥ 0.80 |
| **Macro Recall** | Avg per-class recall | ≥ 0.80 |
| **Macro F1** | Harmonic mean | ≥ 0.80 |

### Risk & Hallucination Metrics

| Metric | Formula | Target |
|--------|---------|--------|
| **Hallucination Rate** | (CONTRADICTED + NOT_ENOUGH) / Total | < 0.15 on clean data |
| **Risk Level Match Rate** | Exact matches / Total Cases | ≥ 0.90 |
| **Risk Score Calibration** | MAE vs. expected | < 0.15 |

### Citation Metrics

| Metric | Formula | Target |
|--------|---------|--------|
| **Citation Coverage** | Cited Supported / Total Supported | ≥ 0.90 |

## Evaluation Procedure

### 1. Automated (CI/CD)

```bash
# Run on every PR
cd truthbench
python -m truthbench.scripts.run_truthbench
# Exit code 0 = pass, 1 = fail
```

**Gate**: PR blocked if any case fails or macro F1 < 0.70

### 2. Manual (Release)

```bash
# Full evaluation with report
cd truthbench
python -m truthbench.scripts.run_truthbench
python -m truthbench.scripts.generate_sample_report
# Review reports/generated_evaluation_report.md
```

### 3. Regression Detection Thresholds

| Metric | Warning | Blocking |
|--------|---------|----------|
| Verdict Macro F1 | < 0.80 | < 0.70 |
| Claim Extraction F1 | < 0.80 | < 0.70 |
| Risk Level Match | < 0.90 | < 0.80 |
| Citation Coverage | < 0.90 | < 0.80 |

## Test Case Design Principles

### Ground Truth Construction

1. **Source**: Authoritative references (Wikipedia, INSEE, NASA, IMF, PubMed)
2. **Claims**: Atomic, single-fact assertions
3. **Verdicts**: Clear rationale with confidence
4. **Risk Level**: Per rubric (LOW/MEDIUM/HIGH)

### Verdict Labeling Rubric

| Verdict | Criteria | Confidence |
|---------|----------|------------|
| SUPPORTED | Multiple authoritative sources agree | ≥ 0.9 |
| CONTRADICTED | Authoritative sources explicitly contradict | ≥ 0.9 |
| NOT_ENOUGH_EVIDENCE | No reliable source found or conflicting | 0.3-0.6 |

### Risk Level Rubric

| Level | Criteria |
|-------|----------|
| LOW | All claims SUPPORTED, high confidence |
| MEDIUM | Mix of SUPPORTED and NOT_ENOUGH_EVIDENCE; no CONTRADICTED |
| HIGH | Any CONTRADICTED claim; or >50% NOT_ENOUGH_EVIDENCE |

## Statistical Rigor

### Confidence Intervals

For each metric, compute 95% CI via bootstrap (1000 resamples):

```python
# Example: Verdict F1 CI
f1_scores = [case.verdict_f1 for case in case_results]
ci_low, ci_high = np.percentile(bootstrap_means, [2.5, 97.5])
```

### Significance Testing

When comparing two system versions:

- **McNemar's test** for paired verdict accuracy
- **Wilcoxon signed-rank** for F1/risk score differences
- **p < 0.05** for significance

### Sample Size

Minimum cases per evaluation:
- **Macro F1 ± 0.05**: ~100 cases (binomial proportion)
- **Risk match rate ± 0.05**: ~400 cases

Current sample (5 cases) is for **smoke testing only**.

## Continuous Evaluation

### Production Monitoring

| Metric | Alert Threshold | Window |
|--------|-----------------|--------|
| Risk score drift | > 0.10 from baseline | 24h |
| Verdict distribution shift | Chi-square p < 0.01 | 1h |
| Latency p95 | > 2× baseline | 5m |
| Error rate | > 1% | 5m |

### A/B Testing Framework

```python
# Pseudocode for A/B test
async def verify_with_variant(question, answer, variant):
    if variant == "control":
        return await pipeline_v1.verify(question, answer)
    elif variant == "treatment":
        return await pipeline_v2.verify(question, answer)

# Random assignment, track verdict_f1, risk_match_rate
```

## Evaluation Artifacts

### Generated Reports

| File | Purpose |
|------|---------|
| `reports/generated_evaluation_report.md` | Human-readable summary |
| `reports/generated_evaluation_report.json` | Machine-readable results |
| `reports/sample_evaluation_report.md` | Documentation example |

### CI/CD Integration

```yaml
# .github/workflows/eval.yml
- name: Run TruthBench
  run: |
    cd truthbench
    python -m truthbench.scripts.run_truthbench
  # Fails if exit code != 0
```

## Acceptance Criteria for v1.0

| Criterion | Threshold |
|-----------|-----------|
| Verdict Macro F1 (clean data) | ≥ 0.85 |
| Verdict Macro F1 (adversarial) | ≥ 0.70 |
| Claim Extraction F1 | ≥ 0.82 |
| Risk Level Match Rate | ≥ 0.90 |
| Citation Coverage | ≥ 0.90 |
| Hallucination Rate (clean) | ≤ 0.10 |
| Hallucination Detection Recall | ≥ 0.90 |
| False Positive Rate | ≤ 0.05 |

## Related Documents

- [TruthBench README](../truthbench/README.md) — Toolkit usage
- [Dataset Schema](../truthbench/datasets/dataset_schema.md) — Data format
- [Architecture](../docs/architecture.md) — Pipeline design
- [Roadmap](../docs/roadmap.md) — Milestone tracking