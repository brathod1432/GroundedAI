# Auto-Grounder — Self-Healing Output Pipeline

> **Part of [GroundedAI](../README.md)** — an end-to-end platform for building trustworthy AI applications.

Auto-Grounder is an automated remediation pipeline that closes the loop on AI hallucinations. It transforms passive hallucination *detection* (provided by [truthguard-ai](../truthguard-ai/README.md)) into active, automated *correction* through an iterative verify → correct → re-verify loop.

---

## Architecture

```text
┌──────────────────────────────────────────────────────────────┐
│                     Auto-Grounder Service                    │
│                      (FastAPI · port 8001)                   │
│                                                              │
│  POST /ground                                                │
│   ┌─────────────────────────────────────────────────────┐    │
│   │              Grounding Loop (core)                  │    │
│   │                                                     │    │
│   │   ┌───────────┐     ┌─────────────────────────┐     │    │
│   │   │ Verify    │────►│ Risk acceptable (LOW)?  │     │    │
│   │   │ (TruthGu- │     │                         │     │    │
│   │   │  ard-AI)  │     │  YES ──► Return answer  │     │    │
│   │   └───────────┘     │  NO  ──► Correct ──┐    │     │    │
│   │        ▲            └─────────────────────┘    │     │    │
│   │        │                                       │     │    │
│   │        │  ┌────────────────────────────────┐   │     │    │
│   │        └──│ Build corrective prompt        │◄──┘     │    │
│   │           │ + Call LLM for new answer      │         │    │
│   │           └────────────────────────────────┘         │    │
│   └─────────────────────────────────────────────────────┘    │
│                                                              │
│  Services:                                                   │
│   • TruthGuardClient  → calls truthguard-ai /verify          │
│   • LLMClient         → OpenAI / Mock for correction         │
└──────────────────────────────────────────────────────────────┘
         │                              │
         ▼                              ▼
  ┌──────────────┐            ┌──────────────────┐
  │ truthguard-ai│            │   LLM Provider   │
  │  (port 8000) │            │ (OpenAI / Mock)  │
  └──────────────┘            └──────────────────┘
```

---

## How It Works

1. **Receive** a question + initial LLM answer via `POST /ground`.
2. **Verify** the answer by calling the [truthguard-ai](../truthguard-ai/README.md) `/verify` endpoint (or a mock).
3. **Evaluate risk** — if the hallucination risk level is at or below the acceptable threshold (default: `LOW`), return the answer as grounded.
4. **Extract failures** — identify contradicted and unsupported claims from the verification report.
5. **Build a corrective prompt** using the failed claims, trusted evidence, and clear rewriting instructions.
6. **Generate a corrected answer** by sending the prompt to an LLM (OpenAI or mock).
7. **Loop** — re-verify the corrected answer (go to step 2).
8. **Stop** when the answer is grounded or the maximum number of iterations is reached.

---

## Quick Start

### Prerequisites

- Python 3.11+
- (Optional) A running [truthguard-ai](../truthguard-ai/README.md) service for real verification

### Setup

```bash
# From the repository root
cd auto-grounder

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate    # Linux/macOS
# .venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment variables
cp .env.example .env
```

### Run the Service

```bash
# Start on port 8001 (default mock mode — no external dependencies)
uvicorn app.main:app --reload --port 8001
```

The API docs are available at [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs).

---

## API Endpoints

### `GET /health`

Lightweight liveness probe.

```bash
curl http://127.0.0.1:8001/health
```

```json
{
  "status": "ok",
  "service": "Auto-Grounder",
  "version": "0.1.0"
}
```

### `POST /ground`

Submit a question and an LLM-generated answer for iterative grounding.

```bash
curl -X POST http://127.0.0.1:8001/ground \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the capital of France?",
    "initial_answer": "Berlin is the capital of France and has 200 million people.",
    "trusted_sources": ["wikipedia"],
    "max_iterations": 3
  }'
```

**Response:**

```json
{
  "final_answer": "Based on the trusted evidence provided, ...",
  "grounded": true,
  "risk_score": 0.10,
  "risk_level": "LOW",
  "total_iterations": 2,
  "iterations": [
    {
      "iteration": 1,
      "answer": "Berlin is the capital of France and has 200 million people.",
      "risk_score": 0.75,
      "risk_level": "HIGH",
      "contradicted_claims": ["Berlin is the capital of France and has 200 million people"],
      "unsupported_claims": [],
      "action_taken": "corrected"
    },
    {
      "iteration": 2,
      "answer": "Based on the trusted evidence provided, ...",
      "risk_score": 0.10,
      "risk_level": "LOW",
      "contradicted_claims": [],
      "unsupported_claims": [],
      "action_taken": "verified"
    }
  ],
  "summary": "Answer grounded successfully after 2 iteration(s). Final risk: LOW (0.10)."
}
```

---

## Configuration

All settings can be overridden via environment variables (prefixed with `GROUNDER_`) or a `.env` file.

| Variable | Default | Description |
|---|---|---|
| `GROUNDER_TRUTHGUARD_URL` | `http://127.0.0.1:8000` | URL of the truthguard-ai service |
| `GROUNDER_LLM_PROVIDER` | `mock` | LLM provider: `mock` or `openai` |
| `GROUNDER_OPENAI_API_KEY` | _(empty)_ | OpenAI API key (required when provider is `openai`) |
| `GROUNDER_OPENAI_MODEL` | `gpt-4o-mini` | OpenAI model to use |
| `GROUNDER_MAX_GROUNDING_ITERATIONS` | `3` | Maximum verify–correct iterations |
| `GROUNDER_ACCEPTABLE_RISK_LEVEL` | `LOW` | Stop iterating when risk is at or below this level |
| `GROUNDER_LOG_LEVEL` | `INFO` | Python logging level |

---

## Project Structure

```
auto-grounder/
├── __init__.py
├── app/
│   ├── __init__.py
│   ├── config.py              # Pydantic-settings configuration
│   ├── main.py                # FastAPI application entry point
│   ├── schemas.py             # Request/response Pydantic models
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py          # API route definitions
│   ├── core/
│   │   ├── __init__.py
│   │   ├── corrective_prompt.py   # Corrective prompt builder
│   │   └── grounding_loop.py     # Main verify → correct → re-verify loop
│   └── services/
│       ├── __init__.py
│       ├── llm_client.py      # LLM client (Mock / OpenAI)
│       └── truthguard_client.py   # TruthGuard-AI client (Mock / HTTP)
├── tests/
│   ├── __init__.py
│   ├── test_app.py            # FastAPI endpoint tests
│   ├── test_corrective_prompt.py  # Corrective prompt tests
│   └── test_grounding_loop.py    # Grounding loop tests
├── .env.example
├── .gitignore
├── pyproject.toml
├── requirements.txt
└── README.md
```

---

## Testing

```bash
# From inside auto-grounder/
pytest

# With verbose output
pytest -v

# Run a specific test file
pytest tests/test_grounding_loop.py -v
```

All tests use mock clients by default — no external services are needed.

---

## Related Projects

| Project | Description |
|---|---|
| [truthguard-ai](../truthguard-ai/README.md) | LLM hallucination detection and verification framework |
| [prompt-shield](../prompt-shield/README.md) | PII detection and scrubbing for LLM prompts |
| [truthbench](../truthbench/) | Evaluation benchmarks for grounding quality |
| [GroundedAI (root)](../README.md) | Monorepo overview and architecture |
