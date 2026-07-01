# TruthGuardAI

**LLM Hallucination Reduction & Grounded Verification Framework**

<p align="center">
  <em>Detect. Verify. Ground.</em>
</p>

---

## What Is TruthGuardAI?

TruthGuardAI is a production-style backend framework that detects and reduces hallucinations in LLM-generated responses. Given a question and a generated answer, it extracts factual claims, retrieves evidence from trusted sources, compares claims against evidence, assigns verification verdicts, and returns a human-readable grounded report with citations and confidence scores.

This is **not** a wrapper around an LLM. It is a **verification layer** that sits between generation and the end user — a critical piece of production AI infrastructure that most teams overlook until hallucinations cause real damage.

---

## Why Hallucination Reduction Matters

Large language models generate fluent, confident text — but they routinely fabricate facts, misattribute citations, and invent statistics. In production systems serving healthcare, finance, legal, and enterprise knowledge workers, a single hallucinated claim can:

- **Erode user trust** — one visible mistake and users question every answer
- **Cause compliance violations** — incorrect regulatory or legal information carries real liability
- **Cascade into bad decisions** — downstream systems that consume LLM output propagate errors automatically
- **Undermine product credibility** — public-facing AI assistants with hallucinations become PR incidents

TruthGuardAI treats hallucination reduction as an **engineering problem**, not a prompt-engineering hack. It provides a structured, auditable, testable pipeline that makes every LLM answer accountable to evidence.

---

## System Architecture

```
User Question + Generated Answer
        │
        ▼
┌──────────────────┐
│  Claim Extractor  │  → Splits answer into discrete factual claims
└────────┬─────────┘
         │
         ▼
┌──────────────────────┐
│  Evidence Retriever  │  → Fetches supporting/contradicting evidence
└────────┬─────────────┘
         │
         ▼
┌──────────────────────┐
│  Citation Checker    │  → Validates citation integrity and source quality
└────────┬─────────────┘
         │
         ▼
┌──────────────────────┐
│  Verifier            │  → Compares claims vs. evidence → verdict per claim
└────────┬─────────────┘
         │
         ▼
┌──────────────────────┐
│  Scoring Engine      │  → Aggregates verdicts → hallucination risk score
└────────┬─────────────┘
         │
         ▼
┌──────────────────────┐
│  Report Builder      │  → Assembles final grounded report
└──────────────────────┘
         │
         ▼
Verified Response with Citations + Confidence Scores
```

### Design Principles

- **Modular pipeline** — each stage is a separate module, independently testable and replaceable
- **Deterministic first** — mock logic works without API keys; real APIs slot in behind clean interfaces
- **Verdict-driven** — every claim gets a clear label: `SUPPORTED`, `CONTRADICTED`, or `NOT_ENOUGH_EVIDENCE`
- **Risk-quantified** — an aggregate `hallucination_risk_score` and risk level (`LOW` / `MEDIUM` / `HIGH`) summarises output quality
- **Citation-grounded** — every supported claim links back to retrieved evidence with a confidence score

---

## Features

| Feature | Description |
|---|---|
| **Claim Extraction** | Splits LLM answers into atomic factual claims |
| **Evidence Retrieval** | Searches trusted sources for supporting/contradicting evidence |
| **Citation Validation** | Checks whether cited sources actually support the claims they are attached to |
| **Claim Verification** | Assigns `SUPPORTED` / `CONTRADICTED` / `NOT_ENOUGH_EVIDENCE` per claim |
| **Hallucination Risk Scoring** | Produces a 0–1 risk score and `LOW` / `MEDIUM` / `HIGH` risk level |
| **Verification Reports** | Human-readable final summary with per-claim verdicts, citations, and confidence |
| **REST API** | FastAPI endpoint for integration into existing pipelines |
| **Pluggable Backends** | Swap mock LLM/search for real OpenAI, Tavily, Wikipedia, etc. |

---

## Tech Stack

| Layer | Technology |
|---|---|
| API Framework | FastAPI |
| Data Validation | Pydantic v2 |
| Testing | pytest |
| LLM Client | Pluggable (mock by default, OpenAI-ready) |
| Search Client | Pluggable (mock by default, Tavily/SearchAPI-ready) |
| Configuration | python-dotenv + pydantic-settings |
| ASGI Server | Uvicorn |

---

## Getting Started

### Prerequisites

- Python 3.11+
- pip

### Install Dependencies

```bash
cd truthguard-ai
pip install -r requirements.txt
```

### Run the API

```bash
uvicorn app.main:app --reload
```

The API will be available at **http://localhost:8000**. Interactive docs at **http://localhost:8000/docs**.

### Run Tests

```bash
pytest
```

### Environment Variables

Copy `.env.example` to `.env` and fill in real API keys when ready:

```bash
cp .env.example .env
```

The project runs fully with mock logic — no API keys are required for the first version.

---

## API Reference

### `POST /verify`

Verify an LLM-generated answer against trusted evidence sources.

**Request Body:**

```json
{
  "original_question": "What is the population of France?",
  "generated_answer": "France has a population of approximately 67 million people as of 2023. The capital city is Paris, which has about 2.1 million residents within city limits.",
  "trusted_sources": ["wikipedia", "world-bank"]
}
```

**Response:**

```json
{
  "extracted_claims": [
    "France has a population of approximately 67 million people as of 2023.",
    "The capital city is Paris.",
    "Paris has about 2.1 million residents within city limits."
  ],
  "evidence_items": [
    {
      "claim_index": 0,
      "source": "wikipedia",
      "snippet": "France's population was estimated at 68 million in 2023.",
      "url": "https://en.wikipedia.org/wiki/France",
      "relevance_score": 0.92
    }
  ],
  "claim_verdicts": [
    {
      "claim_index": 0,
      "verdict": "SUPPORTED",
      "confidence": 0.92,
      "evidence_indices": [0],
      "reasoning": "Evidence aligns with the claim."
    }
  ],
  "hallucination_risk_score": 0.17,
  "risk_level": "LOW",
  "final_summary": "2 of 3 claims are supported by evidence. 1 claim lacks sufficient evidence. No claims were contradicted.",
  "citations": [
    {
      "claim_index": 0,
      "source": "wikipedia",
      "url": "https://en.wikipedia.org/wiki/France",
      "confidence": 0.92
    }
  ]
}
```

See `examples/sample_input.json` and `examples/sample_output.json` for complete examples.

---

## Verdict Labels

| Verdict | Meaning |
|---|---|
| `SUPPORTED` | Evidence corroborates the claim |
| `CONTRADICTED` | Evidence directly contradicts the claim |
| `NOT_ENOUGH_EVIDENCE` | No sufficient evidence found to confirm or deny |

## Risk Levels

| Level | Score Range |
|---|---|
| `LOW` | 0.0 – 0.33 |
| `MEDIUM` | 0.34 – 0.66 |
| `HIGH` | 0.67 – 1.0 |

---

## Project Structure

```
truthguard-ai/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Settings & environment variables
│   ├── schemas.py           # Pydantic request/response models
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py        # API route definitions
│   ├── core/
│   │   ├── __init__.py
│   │   ├── claim_extractor.py   # Claim extraction logic
│   │   ├── evidence_retriever.py # Evidence retrieval logic
│   │   ├── verifier.py          # Claim verification logic
│   │   ├── citation_checker.py  # Citation validation logic
│   │   └── report_builder.py    # Final report assembly
│   ├── services/
│   │   ├── __init__.py
│   │   ├── llm_client.py    # LLM API client (mock/real)
│   │   ├── search_client.py # Search API client (mock/real)
│   │   └── scoring.py       # Risk scoring calculations
│   └── utils/
│       ├── __init__.py
│       └── text_utils.py    # Text processing utilities
├── tests/
│   ├── __init__.py
│   ├── test_claim_extractor.py
│   ├── test_verifier.py
│   └── test_report_builder.py
├── docs/
│   ├── architecture.md
│   ├── hallucination_reduction_strategy.md
│   ├── api_design.md
│   ├── evaluation_plan.md
│   └── roadmap.md
├── examples/
│   ├── sample_input.json
│   └── sample_output.json
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
└── pyproject.toml
```

---

## Roadmap

See [docs/roadmap.md](docs/roadmap.md) for the full roadmap. Key milestones:

- **v0.1** — Pipeline skeleton with mock logic (current)
- **v0.2** — Real LLM integration (OpenAI / Anthropic) for claim extraction
- **v0.3** — Real search integration (Tavily, Wikipedia API, SerpAPI)
- **v0.4** — Citation validation with URL verification
- **v0.5** — Batch verification endpoint
- **v0.6** — Confidence calibration with human-labeled evaluation set
- **v1.0** — Production release with monitoring and deployment guides

---

## Resume / CV Value

This project demonstrates:

- **Production AI system design** — modular pipeline, clean interfaces, dependency injection
- **Hallucination reduction expertise** — claim extraction, evidence retrieval, verification reasoning
- **Backend architecture** — FastAPI, Pydantic, environment-driven config, testable modules
- **RAG grounding** — connecting retrieval results to verification decisions
- **Testable AI engineering** — unit tests, deterministic mock logic, clear interfaces
- **Professional documentation** — architecture docs, strategy docs, API design, evaluation plan

---

## License

MIT
