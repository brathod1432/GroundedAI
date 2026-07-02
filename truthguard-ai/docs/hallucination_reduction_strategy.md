# Hallucination Reduction Strategy

## The Problem

Large Language Models (LLMs) generate fluent, confident text but routinely:
- **Fabricate facts** (invent statistics, dates, names)
- **Misattribute citations** (cite real sources for false claims)
- **Invent references** (hallucinate URLs, papers, authors)
- **Confabulate reasoning** (plausible-sounding but incorrect logic)

These "hallucinations" are dangerous in production systems serving healthcare, finance, legal, and enterprise users.

## Our Approach: Verification as Engineering

TruthGuardAI treats hallucination reduction as a **structured engineering pipeline**, not a prompt-engineering hack. We decompose the problem into discrete, testable stages:

```
Question + Answer → Claims → Evidence → Verification → Risk Score → Report
```

## Stage-by-Stage Strategy

### 1. Claim Extraction: Atomic Decomposition

**Goal**: Break generated text into minimal verifiable units.

**Why it matters**: You can't verify "The system works well" but you can verify "Response time is < 200ms".

**Implementation**:
- Sentence-level splitting on `.`, `!`, `?`
- Heuristic filtering: remove opinions, hedging, fragments
- Output: list of atomic factual assertions

**Future improvement**: LLM-based extractor with structured output (claim type, confidence, entities)

### 2. Evidence Retrieval: Grounded Search

**Goal**: Find authoritative sources for each claim.

**Why it matters**: Verification is only as good as the evidence base.

**Implementation**:
- Abstract `BaseSearchClient` interface
- Mock KB for development (deterministic, no API keys)
- Production backends: Tavily, Wikipedia API, SerpAPI, custom
- Per-claim queries with source hints
- Top-k results per claim (default 3)

**Future improvement**: Multi-hop retrieval, source credibility weighting, temporal awareness

### 3. Citation Validation: Relevance Checking

**Goal**: Ensure cited evidence actually relates to the claim.

**Why it matters**: LLMs often cite relevant-looking but unrelated sources.

**Implementation**:
- Keyword overlap between claim and evidence snippet
- Threshold: 20% token overlap (`_MIN_OVERLAP_RATIO`)
- Separate from truth verification — focuses on *relevance*

**Future improvement**: Semantic similarity (embeddings), citation format validation

### 4. Claim Verification: Evidence Comparison

**Goal**: Determine if evidence supports, contradicts, or is insufficient for each claim.

**Why it matters**: Binary supported/unsupported is insufficient; we need nuance.

**Implementation**:
- **SUPPORTED**: ≥30% keyword overlap (`_SUPPORTED_THRESHOLD`)
- **CONTRADICTED**: Partial overlap + contradiction signals ("false", "not", "debunked")
- **NOT_ENOUGH_EVIDENCE**: No evidence or overlap <30%
- Confidence scores per verdict
- Human-readable reasoning

**Future improvement**: LLM-based verifier with chain-of-thought, numerical claim checking, temporal reasoning

### 5. Risk Scoring: Quantified Aggregation

**Goal**: Produce a single actionable risk metric from per-claim verdicts.

**Why it matters**: Teams need a simple "gate" for automated pipelines.

**Implementation**:
- Weighted average: `CONTRADICTED=1.0`, `NOT_ENOUGH_EVIDENCE=0.5`, `SUPPORTED=0.0`
- Score range: 0.0 (safe) to 1.0 (dangerous)
- Categorical levels: LOW (≤0.33), MEDIUM (0.34-0.66), HIGH (≥0.67)
- Human-readable summary generation

**Future improvement**: Calibrated thresholds, claim-importance weighting, uncertainty quantification

### 6. Report Generation: Actionable Output

**Goal**: Deliver structured, human-readable verification results.

**Why it matters**: Raw verdicts don't help non-technical stakeholders.

**Implementation**:
- `VerifyResponse` schema with all pipeline artifacts
- Per-claim verdicts with evidence links
- Aggregate risk score + level
- Natural language summary
- Structured citations with confidence

## Design Principles

### 1. Deterministic First
Mock implementations work without API keys. Deterministic behavior enables:
- Reliable unit tests
- CI/CD integration
- Reproducible debugging

### 2. Modular Pipeline
Each stage is a pure function with typed inputs/outputs:
- Independent testing
- Easy replacement (e.g., swap mock → real search)
- Clear data contracts via Pydantic

### 3. Verdict-Driven, Not Binary
Three verdicts capture real-world nuance:
- `SUPPORTED` = high confidence truth
- `CONTRADICTED` = high confidence falsehood
- `NOT_ENOUGH_EVIDENCE` = unknown (epistemic humility)

### 4. Risk-Quantified
Aggregate score enables:
- Automated gating (block HIGH risk responses)
- Monitoring dashboards
- A/B testing of LLM prompts/models

### 5. Citation-Grounded
Every supported claim links to evidence:
- Audit trail for compliance
- User-facing source display
- Confidence per citation

## Limitations & Honest Assessment

| Limitation | Mitigation |
|------------|------------|
| Keyword overlap ≠ semantic equivalence | Future: embedding-based similarity |
| Mock KB covers only 3 topics | Future: real search APIs |
| No numerical/date reasoning | Future: specialized extractors |
| Single-pass (no self-correction) | Future: iterative refinement |
| English only | Future: multilingual support |

## Evaluation Strategy

We measure effectiveness via **TruthBench** (separate package):
- Ground-truth datasets with expected claims/verdicts
- Metrics: claim extraction F1, verdict accuracy, hallucination rate, citation coverage
- Regression detection in CI/CD

## Production Deployment Considerations

1. **Latency**: Pipeline adds ~500-2000ms (mock). Real APIs will be slower.
2. **Cost**: Search + LLM APIs per request. Cache frequent queries.
3. **Monitoring**: Track risk score distributions, verdict rates, latency percentiles.
4. **Fallback**: On pipeline failure, default to HIGH risk / manual review.
5. **Human-in-the-loop**: Flag MEDIUM/HIGH for expert review workflows.