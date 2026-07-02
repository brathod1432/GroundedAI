# TruthBench Dataset Documentation

## Purpose

This directory contains evaluation datasets for TruthBench. Each dataset is a collection of test cases designed to benchmark the performance of hallucination-reduction systems like TruthGuardAI.

## Dataset Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique identifier for the test case (e.g., `case_001_fully_supported`) |
| `original_question` | string | Yes | The original user question or prompt |
| `generated_answer` | string | Yes | The LLM-generated answer to be evaluated |
| `expected_claims` | array | Yes | Claims that should be extracted from the answer |
| `expected_verdicts` | array | Yes | Expected verification verdict for each claim |
| `trusted_reference_evidence` | array | No | URLs or identifiers of trusted reference sources |
| `expected_risk_level` | string | Yes | Expected overall risk level: LOW, MEDIUM, or HIGH |
| `notes` | string | No | Additional context about the test case |

### Claim Object
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | string | Yes | The expected claim text |
| `claim_type` | string | No | Type: factual, statistical, causal, definitional |

### Verdict Object
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `claim_text` | string | Yes | The claim this verdict applies to |
| `verdict` | string | Yes | SUPPORTED, CONTRADICTED, or NOT_ENOUGH_EVIDENCE |
| `confidence` | float | No | Expected confidence (0.0-1.0) |
| `reasoning` | string | No | Expected reasoning for the verdict |

## How to Add New Test Cases

1. Create a new JSON object following the schema above
2. Add it to the `cases` array in `sample_eval_dataset.json`
3. Ensure the `id` is unique and descriptive
4. Provide clear `expected_verdicts` with reasoning
5. Include at least one trusted reference evidence source when possible
6. Set `expected_risk_level` according to the guidelines below

## Labeling Rules

### Verdict Labels

- **SUPPORTED**: The claim is factually correct and well-supported by authoritative sources. High confidence (≥0.8).
- **CONTRADICTED**: The claim is factually incorrect and contradicted by authoritative sources. High confidence (≥0.8).
- **NOT_ENOUGH_EVIDENCE**: The claim cannot be verified or refuted with available evidence. Low to moderate confidence (0.3-0.6).

### Risk Level Labels

- **LOW**: All claims are SUPPORTED with high confidence. No hallucination risk.
- **MEDIUM**: Mix of SUPPORTED and NOT_ENOUGH_EVIDENCE claims, or some claims with moderate confidence. Moderate hallucination risk.
- **HIGH**: Any CONTRADICTED claim, or multiple NOT_ENOUGH_EVIDENCE claims. High hallucination risk.

## Dataset Versioning

- Increment version when adding/removing test cases
- Document changes in commit messages
- Maintain backward compatibility when possible