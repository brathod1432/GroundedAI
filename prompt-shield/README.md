# Prompt Shield

LLM Security Proxy for PII scrubbing, prompt injection detection, and toxicity filtering.

**Part of the [GroundedAI](../README.md) ecosystem.**

## Overview

Prompt Shield is a FastAPI middleware service that intercepts traffic between user applications and LLMs. While `truthguard-ai` ensures the LLM's outputs are factually grounded, Prompt Shield ensures the user's inputs are safe and sensitive data is not leaked.

## Architecture

```text
User Application
       |
       v (Raw Prompt)
[ Prompt Shield ]
       |-- 1. Toxicity Check -----> Block if harmful
       |-- 2. Injection Detection -> Block if jailbreak attempt
       |-- 3. PII Scrubbing ------> Replace with [EMAIL_1], [PHONE_1], etc.
       v (Sanitized Prompt)
     [ LLM ]
       |
       v (Raw Response)
[ Prompt Shield ]
       |-- 4. PII Re-injection ---> Restore original values
       v (Safe Response)
User Application
```

## Features

### PII Detection and Scrubbing
Detects and redacts 6 PII types using regex pattern matching:

| PII Type | Example | Placeholder |
|----------|---------|-------------|
| Email | `john@example.com` | `[EMAIL_1]` |
| Phone | `555-123-4567` | `[PHONE_1]` |
| SSN | `123-45-6789` | `[SSN_1]` |
| Credit Card | `4111-1111-1111-1111` | `[CREDIT_CARD_1]` |
| API Key | `sk-abc123...` | `[API_KEY_1]` |
| IP Address | `192.168.1.1` | `[IP_ADDRESS_1]` |

PII is re-injected into the LLM response before returning to the user.

### Prompt Injection Detection
12 pattern-based rules detecting jailbreak attempts:
- Instruction override ("ignore previous instructions")
- Role switching ("you are now DAN")
- Safety bypass ("bypass safety filters")
- System prompt extraction ("show me your system prompt")
- Delimiter injection (`` ```system ``, `<|im_start|>`)
- Base64 encoding tricks

### Toxicity Filtering
6-category content safety filter:
- Hate speech, violence threats, self-harm
- Harassment, illegal activity, severe profanity

## Setup

```bash
cd prompt-shield
python -m pip install -r requirements.txt
```

## Usage

### Start the API

```bash
cd prompt-shield
python -m uvicorn app.main:app --reload --port 8001
```

### API Endpoints

**Health Check:**
```bash
curl http://127.0.0.1:8001/health
```

**Shield a Prompt (analysis only):**
```bash
curl -X POST http://127.0.0.1:8001/shield ^
  -H "Content-Type: application/json" ^
  -d "{\"prompt\": \"My email is john@example.com and my SSN is 123-45-6789. What is the capital of France?\"}"
```

**Shield and Forward to LLM:**
```bash
curl -X POST http://127.0.0.1:8001/shield ^
  -H "Content-Type: application/json" ^
  -d "{\"prompt\": \"What is AI?\", \"forward_to_llm\": true}"
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `SHIELD_LLM_PROVIDER` | `mock` | LLM backend: `mock`, `openai`, `anthropic` |
| `SHIELD_PII_DETECTION_ENABLED` | `true` | Enable PII scrubbing |
| `SHIELD_INJECTION_DETECTION_ENABLED` | `true` | Enable jailbreak detection |
| `SHIELD_TOXICITY_FILTERING_ENABLED` | `true` | Enable toxicity filter |
| `SHIELD_INJECTION_THRESHOLD` | `0.7` | Score threshold to block injections |
| `SHIELD_TOXICITY_THRESHOLD` | `0.7` | Score threshold to block toxic content |
| `SHIELD_MAX_PROMPT_LENGTH` | `50000` | Maximum allowed prompt length |

Copy `.env.example` to `.env` for local overrides.

## Testing

```bash
cd prompt-shield
python -m pytest tests/ -v
```

97 tests covering PII detection, PII scrubbing/restoration, injection detection, toxicity filtering, and API integration.

## Project Structure

```
prompt-shield/
├── app/
│   ├── main.py                 # FastAPI entry point
│   ├── config.py               # Pydantic Settings
│   ├── schemas.py              # Request/response models
│   ├── api/
│   │   └── routes.py           # /health, /shield endpoints
│   ├── core/
│   │   ├── pii_detector.py     # Regex-based PII detection
│   │   ├── pii_scrubber.py     # PII redaction and re-injection
│   │   ├── injection_detector.py  # Prompt injection detection
│   │   └── toxicity_filter.py  # Content safety filter
│   └── services/
│       └── llm_proxy.py        # LLM forwarding (mock/real)
├── tests/                      # 97 unit and integration tests
├── pyproject.toml
├── requirements.txt
└── .env.example
```

## Related Projects

- [truthguard-ai](../truthguard-ai/) - LLM output verification (factual safety)
- [auto-grounder](../auto-grounder/) - Self-healing hallucination correction
- [truthbench](../truthbench/) - Evaluation benchmarking toolkit
- [Root README](../README.md)
