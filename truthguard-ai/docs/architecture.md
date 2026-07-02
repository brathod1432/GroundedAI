# TruthGuardAI Architecture

## Overview

TruthGuardAI is a modular pipeline for LLM hallucination reduction. The architecture follows a linear pipeline pattern where each stage transforms the output of the previous stage, with clear interfaces between modules.

## System Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           TRUTHGUARD PIPELINE                                │
└─────────────────────────────────────────────────────────────────────────────┘

  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────┐
  │   INPUT      │────▶│  CLAIM       │────▶│  EVIDENCE    │────▶│ CITATION │
  │  (Question,  │     │  EXTRACTOR   │     │  RETRIEVER   │     │ CHECKER  │
  │   Answer)    │     │              │     │              │     │          │
  └──────────────┘     └──────┬───────┘     └──────┬───────┘     └────┬─────┘
                              │                    │                  │
                              ▼                    ▼                  ▼
                        [claims: str[]]      [EvidenceItem[]]    [Citation[]]
                              │                    │                  │
                              │         ┌──────────┴──────────┐      │
                              │         │                     │      │
                              ▼         ▼                     ▼      ▼
                        ┌────────────────────────────────────────────────┐
                        │              VERIFIER                          │
                        │  (claims + evidence → ClaimVerdict[])          │
                        └────────────────────┬───────────────────────────┘
                                             │
                                             ▼
                        ┌────────────────────────────────────────────────┐
                        │              SCORING ENGINE                    │
                        │  (verdicts → hallucination_risk_score, risk)  │
                        └────────────────────┬───────────────────────────┘
                                             │
                                             ▼
                        ┌────────────────────────────────────────────────┐
                        │              REPORT BUILDER                    │
                        │  (claims, evidence, verdicts, citations,      │
                        │   risk_score, risk_level) → VerifyResponse    │
                        └────────────────────┬───────────────────────────┘
                                             │
                                             ▼
                                    ┌──────────────────┐
                                    │  OUTPUT          │
                                    │  (VerifyResponse)│
                                    └──────────────────┘
```

## Module Responsibilities

### 1. Claim Extractor (`app/core/claim_extractor.py`)

**Purpose**: Decompose LLM-generated text into discrete, verifiable factual claims.

**Strategy**: Rule-based sentence splitting with heuristic filtering.

**Input**: `generated_answer: str`
**Output**: `list[str]` (extracted claims)

**Design Notes**:
- Splits on sentence boundaries (`.`, `!`, `?`)
- Filters out short fragments (<15 chars) and opinion-starters ("I think", "maybe")
- Caps at `max_claims_per_answer` (default 20)
- Pluggable: Can be replaced with LLM-based extractor

### 2. Evidence Retriever (`app/core/evidence_retriever.py`)

**Purpose**: Fetch relevant evidence for each extracted claim from configured sources.

**Strategy**: Query search client per claim, collect up to `evidence_per_claim` results.

**Input**: `claims: list[str]`, `trusted_sources: list[str] | None`
**Output**: `list[EvidenceItem]`

**Design Notes**:
- Uses `BaseSearchClient` abstraction (mock by default)
- Prefixes queries with trusted source hints
- Each evidence item tagged with `claim_index` for traceability
- Pluggable: Supports Tavily, SerpAPI, custom backends

### 3. Citation Checker (`app/core/citation_checker.py`)

**Purpose**: Validate that evidence items genuinely support their associated claims.

**Strategy**: Keyword overlap ratio between claim and evidence snippet.

**Input**: `claims: list[str]`, `evidence_items: list[EvidenceItem]`
**Output**: `list[Citation]`

**Design Notes**:
- Minimum overlap threshold: 20% (`_MIN_OVERLAP_RATIO`)
- Separate from verification: focuses on source relevance, not truthfulness
- Filters out loosely associated evidence

### 4. Verifier (`app/core/verifier.py`)

**Purpose**: Assign a verdict to each claim based on retrieved evidence.

**Strategy**: Keyword overlap with contradiction signal detection.

**Input**: `claims: list[str]`, `evidence_items: list[EvidenceItem]`
**Output**: `list[ClaimVerdict]`

**Verdict Logic**:
- **SUPPORTED**: Overlap ≥ 30% (`_SUPPORTED_THRESHOLD`)
- **CONTRADICTED**: Partial overlap + contradiction keywords ("false", "not", "debunked")
- **NOT_ENOUGH_EVIDENCE**: No evidence or overlap < 30%

**Design Notes**:
- Groups evidence by `claim_index` for efficient lookup
- Returns confidence score per verdict
- Provides human-readable reasoning

### 5. Scoring Engine (`app/services/scoring.py`)

**Purpose**: Aggregate per-claim verdicts into overall hallucination risk.

**Strategy**: Weighted average of verdict penalties.

**Input**: `verdicts: list[ClaimVerdict]`
**Output**: `risk_score: float`, `risk_level: RiskLevel`, `summary: str`

**Weights**:
- `CONTRADICTED`: 1.0 (highest risk)
- `NOT_ENOUGH_EVIDENCE`: 0.5 (moderate risk)
- `SUPPORTED`: 0.0 (no risk)

**Risk Levels**:
- `LOW`: score ≤ 0.33
- `MEDIUM`: 0.34 ≤ score ≤ 0.66
- `HIGH`: score ≥ 0.67

### 6. Report Builder (`app/core/report_builder.py`)

**Purpose**: Assemble final `VerifyResponse` from all pipeline outputs.

**Input**: All pipeline outputs
**Output**: `VerifyResponse`

**Design Notes**:
- Thin orchestration layer
- Delegates scoring to Scoring Engine
- Ensures response schema compliance

## Data Flow

```
VerifyRequest
    │
    ▼
extract_claims() → claims: list[str]
    │
    ▼
retrieve_evidence(claims) → evidence: list[EvidenceItem]
    │
    ▼
check_citations(claims, evidence) → citations: list[Citation]
    │
    ▼
verify_claims(claims, evidence) → verdicts: list[ClaimVerdict]
    │
    ▼
build_report(claims, evidence, verdicts, citations) → VerifyResponse
```

## Configuration

All configuration via `app/config.py` using `pydantic-settings`:

- Environment variables (`.env` file)
- Sensible defaults for mock operation
- No API keys required for development

## Extensibility Points

| Extension Point | Interface | Default Implementation |
|----------------|-----------|------------------------|
| LLM Client | `BaseLLMClient` | `MockLLMClient` |
| Search Client | `BaseSearchClient` | `MockSearchClient` |
| Claim Extractor | `extract_claims()` | Rule-based |
| Verifier | `verify_claims()` | Keyword overlap |
| Scorer | `compute_risk_score()` | Weighted average |

Each can be replaced independently without modifying other pipeline stages.