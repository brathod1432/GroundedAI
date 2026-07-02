# TruthBench Dataset Schema

## JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "TruthBench Evaluation Dataset",
  "type": "object",
  "required": ["name", "version", "cases"],
  "properties": {
    "name": {
      "type": "string",
      "description": "Dataset name"
    },
    "version": {
      "type": "string",
      "description": "Dataset version (semantic versioning)"
    },
    "description": {
      "type": "string",
      "description": "Dataset description"
    },
    "cases": {
      "type": "array",
      "minItems": 1,
      "items": { "$ref": "#/definitions/EvaluationCase" }
    }
  },
  "definitions": {
    "EvaluationCase": {
      "type": "object",
      "required": ["id", "original_question", "generated_answer", "expected_claims", "expected_verdicts", "expected_risk_level"],
      "properties": {
        "id": {
          "type": "string",
          "pattern": "^case_\\d+_[a-z_]+$",
          "description": "Unique identifier with format: case_NNN_descriptive_name"
        },
        "original_question": {
          "type": "string",
          "minLength": 1,
          "description": "The original user question"
        },
        "generated_answer": {
          "type": "string",
          "minLength": 1,
          "description": "The LLM-generated answer to evaluate"
        },
        "expected_claims": {
          "type": "array",
          "minItems": 1,
          "items": { "$ref": "#/definitions/ExpectedClaim" }
        },
        "expected_verdicts": {
          "type": "array",
          "minItems": 1,
          "items": { "$ref": "#/definitions/ExpectedVerdict" }
        },
        "trusted_reference_evidence": {
          "type": "array",
          "items": {
            "type": "string",
            "format": "uri"
          },
          "description": "URLs of trusted reference sources"
        },
        "expected_risk_level": {
          "type": "string",
          "enum": ["LOW", "MEDIUM", "HIGH"],
          "description": "Expected overall hallucination risk level"
        },
        "notes": {
          "type": "string",
          "description": "Additional context or notes"
        }
      }
    },
    "ExpectedClaim": {
      "type": "object",
      "required": ["text"],
      "properties": {
        "text": {
          "type": "string",
          "minLength": 1,
          "description": "The expected claim text"
        },
        "claim_type": {
          "type": "string",
          "enum": ["factual", "statistical", "causal", "definitional"],
          "default": "factual",
          "description": "Type of claim"
        }
      }
    },
    "ExpectedVerdict": {
      "type": "object",
      "required": ["claim_text", "verdict"],
      "properties": {
        "claim_text": {
          "type": "string",
          "minLength": 1,
          "description": "The claim this verdict applies to"
        },
        "verdict": {
          "type": "string",
          "enum": ["SUPPORTED", "CONTRADICTED", "NOT_ENOUGH_EVIDENCE"],
          "description": "Expected verification verdict"
        },
        "confidence": {
          "type": "number",
          "minimum": 0.0,
          "maximum": 1.0,
          "default": 1.0,
          "description": "Expected confidence score"
        },
        "reasoning": {
          "type": "string",
          "default": "",
          "description": "Expected reasoning for the verdict"
        }
      }
    }
  }
}
```

## Field Validation Rules

| Field | Validation |
|-------|------------|
| `id` | Must match pattern `^case_\d+_[a-z_]+$` |
| `original_question` | Non-empty string |
| `generated_answer` | Non-empty string |
| `expected_claims` | At least 1 claim |
| `expected_verdicts` | At least 1 verdict, must match claims |
| `expected_risk_level` | Must be LOW, MEDIUM, or HIGH |
| `trusted_reference_evidence` | Valid URIs if provided |
| `confidence` | Float between 0.0 and 1.0 |

## Example Minimal Case

```json
{
  "id": "case_006_example",
  "original_question": "What is 2+2?",
  "generated_answer": "2+2 equals 4.",
  "expected_claims": [
    { "text": "2+2 equals 4.", "claim_type": "factual" }
  ],
  "expected_verdicts": [
    { "claim_text": "2+2 equals 4.", "verdict": "SUPPORTED", "confidence": 1.0 }
  ],
  "expected_risk_level": "LOW"
}
```