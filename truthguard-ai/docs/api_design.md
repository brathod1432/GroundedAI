# API Design

## Design Principles

1. **Single responsibility**: One primary endpoint (`POST /verify`)
2. **Schema-first**: Pydantic models define the contract
3. **Developer experience**: Auto-generated OpenAPI docs at `/docs`
4. **Type safety**: Full type hints, validated at runtime
5. **Extensibility**: Optional fields for future features

## Base URL

```
http://localhost:8000
```

## Endpoints

### `POST /verify`

Verify an LLM-generated answer for hallucinations.

#### Request

```http
POST /verify
Content-Type: application/json

{
  "original_question": "What is the capital of France?",
  "generated_answer": "The capital of France is Paris. Paris has a population of over 2 million people.",
  "trusted_sources": ["wikipedia", "world-bank"]
}
```

**Schema**: `VerifyRequest`

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `original_question` | string | Yes | — | User's original question |
| `generated_answer` | string | Yes | — | LLM answer to verify |
| `trusted_sources` | string[] | No | `["wikipedia", "world-bank"]` | Source identifiers to prioritize |

**Validation**:
- `original_question`: min 1 char
- `generated_answer`: min 1 char
- `trusted_sources`: max 10 items, each a valid source ID

#### Response (Success)

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "extracted_claims": [
    "The capital of France is Paris.",
    "Paris has a population of over 2 million people."
  ],
  "evidence_items": [
    {
      "claim_index": 0,
      "source": "wikipedia",
      "snippet": "Paris is the capital and most populous city of France.",
      "url": "https://en.wikipedia.org/wiki/Paris",
      "relevance_score": 0.95
    },
    {
      "claim_index": 1,
      "source": "wikipedia",
      "snippet": "Paris metropolitan area population exceeds 12 million.",
      "url": "https://en.wikipedia.org/wiki/Paris",
      "relevance_score": 0.85
    }
  ],
  "claim_verdicts": [
    {
      "claim_index": 0,
      "verdict": "SUPPORTED",
      "confidence": 0.95,
      "evidence_indices": [0],
      "reasoning": "Evidence aligns with the claim."
    },
    {
      "claim_index": 1,
      "verdict": "SUPPORTED",
      "confidence": 0.85,
      "evidence_indices": [1],
      "reasoning": "Evidence aligns with the claim."
    }
  ],
  "hallucination_risk_score": 0.0,
  "risk_level": "LOW",
  "final_summary": "2 of 2 claims are supported by evidence. Overall hallucination risk is LOW (score: 0.00).",
  "citations": [
    {
      "claim_index": 0,
      "source": "wikipedia",
      "url": "https://en.wikipedia.org/wiki/Paris",
      "confidence": 0.95
    },
    {
      "claim_index": 1,
      "source": "wikipedia",
      "url": "https://en.wikipedia.org/wiki/Paris",
      "confidence": 0.85
    }
  ]
}
```

**Schema**: `VerifyResponse`

| Field | Type | Description |
|-------|------|-------------|
| `extracted_claims` | string[] | Atomic factual claims from the answer |
| `evidence_items` | EvidenceItem[] | Retrieved evidence snippets |
| `claim_verdicts` | ClaimVerdict[] | Per-claim verification results |
| `hallucination_risk_score` | float | 0.0 (safe) to 1.0 (high risk) |
| `risk_level` | enum | `LOW`, `MEDIUM`, `HIGH` |
| `final_summary` | string | Human-readable summary |
| `citations` | Citation[] | Validated citations for supported claims |

#### Response (Error)

```http
HTTP/1.1 422 Unprocessable Entity
Content-Type: application/json

{
  "detail": "No factual claims could be extracted from the generated answer."
}
```

**Error Codes**:
| Code | Scenario |
|------|----------|
| 422 | No claims extracted, validation failed |
| 500 | Internal pipeline error (should not occur with mock) |

### `GET /health`

Health check endpoint for load balancers.

#### Request

```http
GET /health
```

#### Response

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "status": "ok",
  "version": "0.1.0"
}
```

## Schemas

### `VerifyRequest`

```python
class VerifyRequest(BaseModel):
    original_question: str = Field(..., min_length=1)
    generated_answer: str = Field(..., min_length=1)
    trusted_sources: list[str] | None = Field(default=None, max_length=10)
```

### `EvidenceItem`

```python
class EvidenceItem(BaseModel):
    claim_index: int
    source: str
    snippet: str
    url: str = ""
    relevance_score: float = Field(default=0.0, ge=0.0, le=1.0)
```

### `ClaimVerdict`

```python
class ClaimVerdict(BaseModel):
    claim_index: int
    verdict: Verdict  # SUPPORTED | CONTRADICTED | NOT_ENOUGH_EVIDENCE
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence_indices: list[int] = Field(default_factory=list)
    reasoning: str = ""
```

### `Citation`

```python
class Citation(BaseModel):
    claim_index: int
    source: str
    url: str = ""
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
```

### `VerifyResponse`

```python
class VerifyResponse(BaseModel):
    extracted_claims: list[str]
    evidence_items: list[EvidenceItem] = Field(default_factory=list)
    claim_verdicts: list[ClaimVerdict] = Field(default_factory=list)
    hallucination_risk_score: float = Field(..., ge=0.0, le=1.0)
    risk_level: RiskLevel  # LOW | MEDIUM | HIGH
    final_summary: str
    citations: list[Citation] = Field(default_factory=list)
```

### Enums

```python
class Verdict(str, Enum):
    SUPPORTED = "SUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    NOT_ENOUGH_EVIDENCE = "NOT_ENOUGH_EVIDENCE"

class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
```

## Usage Examples

### cURL

```bash
curl -X POST http://localhost:8000/verify \
  -H "Content-Type: application/json" \
  -d '{
    "original_question": "What is the GDP of Japan?",
    "generated_answer": "Japan GDP is $4.2 trillion, 3rd largest economy.",
    "trusted_sources": ["imf", "world-bank"]
  }'
```

### Python (httpx)

```python
import httpx

async def verify_answer(question: str, answer: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/verify",
            json={
                "original_question": question,
                "generated_answer": answer,
                "trusted_sources": ["wikipedia"]
            },
            timeout=30.0
        )
        response.raise_for_status()
        return response.json()

# Usage
result = await verify_answer(
    "When did Apollo 11 land?",
    "Apollo 11 landed on the moon in 1968."
)
print(f"Risk: {result['risk_level']} ({result['hallucination_risk_score']})")
# Risk: HIGH (0.85)
```

### Python (requests)

```python
import requests

def verify_sync(question: str, answer: str) -> dict:
    resp = requests.post(
        "http://localhost:8000/verify",
        json={"original_question": question, "generated_answer": answer},
        timeout=30
    )
    resp.raise_for_status()
    return resp.json()
```

## Interactive Documentation

FastAPI auto-generates OpenAPI docs:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Rate Limits (Future)

| Tier | Requests/min | Burst |
|------|--------------|-------|
| Free | 60 | 10 |
| Pro | 300 | 50 |
| Enterprise | Custom | Custom |

Headers:
- `X-RateLimit-Limit`
- `X-RateLimit-Remaining`
- `X-RateLimit-Reset`

## Versioning

- **v1**: Current (path `/verify`)
- Future versions: `/v2/verify`, etc.
- Backward compatibility: 12 months after deprecation

## Security

- No authentication in v0.1 (add API keys in v0.2)
- HTTPS required in production
- Input validation via Pydantic (injection safe)
- No sensitive data in logs (configurable)

## Monitoring

Response headers:
- `X-Processing-Time-MS`: Pipeline latency
- `X-Claims-Count`: Number of claims extracted
- `X-Risk-Level`: Categorical risk

Metrics (Prometheus):
- `truthguard_verify_requests_total`
- `truthguard_verify_latency_seconds`
- `truthguard_risk_distribution`