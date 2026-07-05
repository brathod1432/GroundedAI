# Truth Guard

Truth Guard is a FastAPI service for verifying LLM-generated answers against evidence. Given a user question and generated answer, it extracts factual claims, retrieves candidate evidence, ranks and aligns evidence, assigns claim-level verdicts, checks citations, and returns a structured hallucination-risk report.

The current implementation is local-first and mock-backed by default. It does not require API keys to run.

## Main Files

| Path | Purpose |
| --- | --- |
| `app/main.py` | FastAPI application entry point. Keep this file. |
| `app/config.py` | Environment-driven settings. |
| `app/schemas.py` | Pydantic request and response models. |
| `app/api/routes.py` | HTTP route definitions, including `POST /verify`. |
| `app/core/claim_extractor.py` | Rule-based factual claim extraction. |
| `app/core/evidence_retriever.py` | Retrieves evidence with the configured search client. |
| `app/core/evidence_ranker.py` | Ranks retrieved evidence. |
| `app/core/claim_evidence_aligner.py` | Links claims to evidence. |
| `app/core/citation_checker.py` | Builds citations for supported claims. |
| `app/core/verifier.py` | Assigns `SUPPORTED`, `CONTRADICTED`, or `NOT_ENOUGH_EVIDENCE`. |
| `app/core/report_builder.py` | Assembles the final response. |
| `app/services/search_client.py` | Mock search backend and placeholder Tavily backend. |
| `app/services/llm_client.py` | Mock LLM backend and placeholder OpenAI backend. |
| `app/services/scoring.py` | Risk scoring and summary helpers. |
| `examples/` | Sample request and response JSON files. |
| `tests/` | Unit and smoke tests. |

## Setup

From the repository root:

```bash
python -m pip install -r truthguard-ai/requirements.txt
```

## Configuration

Truth Guard runs with mock providers by default. To customize settings, copy `truthguard-ai/.env.example` to `truthguard-ai/.env`.

| Variable | Default | Purpose |
| --- | --- | --- |
| `APP_NAME` | `TruthGuardAI` | FastAPI app title. |
| `APP_VERSION` | `0.1.0` | Version returned by `/health`. |
| `DEBUG` | `false` | Enables debug logging when true. |
| `LLM_PROVIDER` | `mock` | LLM provider. `mock` works today; `openai` is a placeholder. |
| `OPENAI_API_KEY` | empty | Placeholder for future OpenAI support. |
| `SEARCH_PROVIDER` | `mock` | Search provider. `mock` works today; `tavily` is a placeholder. |
| `TAVILY_API_KEY` | empty | Placeholder for future Tavily support. |
| `DEFAULT_TRUSTED_SOURCES` | `["wikipedia","world-bank"]` | Source hints when a request omits trusted sources. |
| `MAX_CLAIMS_PER_ANSWER` | `20` | Maximum extracted claims per answer. |
| `EVIDENCE_PER_CLAIM` | `3` | Maximum evidence items per claim. |

Do not commit real local `.env` files or credentials.

## How To Run

Start the API from inside the project folder:

```bash
cd truthguard-ai
python -m uvicorn app.main:app --reload
```

Open the interactive API docs at `http://127.0.0.1:8000/docs`.

Health check:

```bash
curl http://127.0.0.1:8000/health
```

## Verify An Answer

Example request:

```bash
curl -X POST http://127.0.0.1:8000/verify ^
  -H "Content-Type: application/json" ^
  -d "{\"original_question\":\"What is the population of France?\",\"generated_answer\":\"France has a population of approximately 68 million people in 2023. Paris is the capital of France.\",\"trusted_sources\":[\"wikipedia\",\"world-bank\"]}"
```

PowerShell can send the sample file:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/verify `
  -ContentType "application/json" `
  -InFile .\examples\sample_input.json
```

## Inputs And Outputs

`POST /verify` accepts:

```json
{
  "original_question": "What is the population of France?",
  "generated_answer": "France has a population of approximately 68 million people in 2023.",
  "trusted_sources": ["wikipedia", "world-bank"]
}
```

The response includes:

- `extracted_claims`
- `evidence_items`
- `claim_verdicts`
- `hallucination_risk_score`
- `risk_level`
- `final_summary`
- `citations`

See `examples/sample_input.json` and `examples/sample_output.json` for complete examples.

## Testing

From the repository root:

```bash
python -m pytest truthguard-ai/tests -v
```

## Current Limitations

- Claim extraction is rule-based.
- Verification uses keyword overlap and contradiction keywords.
- Search and LLM clients are mock or placeholder implementations.
- Non-mock providers are not production-ready.
- Citation validation does not fetch live URLs.
- The service has no authentication, rate limiting, persistence, or deployment configuration.

## Suggested Improvements

- Implement real search and LLM clients behind the existing interfaces.
- Add FastAPI integration tests for `POST /verify`.
- Add request size limits and structured error responses.
- Add batch verification for multiple generated answers.
- Evaluate changes with Truth Bench.
- Add deployment documentation after production settings are defined.

## License

The package metadata declares MIT, but this repository does not currently include a license file.
