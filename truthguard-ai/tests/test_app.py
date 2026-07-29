"""Smoke tests for the FastAPI application entry point."""

import os

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint() -> None:
    """The app should import cleanly and expose the health endpoint."""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_verify_endpoint_basic():
    """Test the full verification pipeline with a simple factual answer."""
    response = client.post("/verify", json={
        "original_question": "What is the capital of France?",
        "generated_answer": "Paris is the capital of France. France has a population of approximately 68 million people.",
        "trusted_sources": ["wikipedia"]
    })
    assert response.status_code == 200
    data = response.json()
    assert "extracted_claims" in data
    assert "claim_verdicts" in data
    assert "hallucination_risk_score" in data
    assert "risk_level" in data
    assert "final_summary" in data
    assert "citations" in data
    assert "evidence_items" in data
    assert len(data["extracted_claims"]) > 0


def test_verify_endpoint_empty_answer():
    """Test verify with an answer that has no extractable claims."""
    response = client.post("/verify", json={
        "original_question": "What is life?",
        "generated_answer": "Hmm, well...",
        "trusted_sources": ["wikipedia"]
    })
    # Should return 422 because no claims could be extracted
    assert response.status_code == 422


def test_verify_endpoint_no_trusted_sources():
    """Test verify without specifying trusted sources (uses defaults)."""
    response = client.post("/verify", json={
        "original_question": "What is the capital of France?",
        "generated_answer": "Paris is the capital and most populous city of France."
    })
    assert response.status_code == 200
    data = response.json()
    assert len(data["extracted_claims"]) > 0


def test_verify_endpoint_missing_required_fields():
    """Test verify with missing required fields."""
    response = client.post("/verify", json={
        "original_question": "What is the capital of France?"
        # Missing generated_answer
    })
    assert response.status_code == 422


def test_verify_endpoint_risk_levels():
    """Test that risk level is properly computed."""
    response = client.post("/verify", json={
        "original_question": "What is the population of France?",
        "generated_answer": "France has a population of approximately 68 million people as of 2023.",
        "trusted_sources": ["wikipedia", "world-bank"]
    })
    assert response.status_code == 200
    data = response.json()
    assert data["risk_level"] in ["LOW", "MEDIUM", "HIGH"]
    assert 0.0 <= data["hallucination_risk_score"] <= 1.0


def test_verify_max_length_rejected():
    """Test that answers exceeding max_length are rejected."""
    response = client.post("/verify", json={
        "original_question": "What is France?",
        "generated_answer": "x" * 50001,  # over 50000 char limit
    })
    assert response.status_code == 422


def test_auth_health_always_accessible():
    """Health endpoint must always be reachable even with a key configured."""
    # Health check must not require API key — it's an exempt path
    response = client.get("/health")
    assert response.status_code == 200


def test_auth_dev_mode_no_key_required(monkeypatch):
    """When api_key is empty (default), all endpoints are accessible."""
    # Default settings have empty api_key, so no auth required
    response = client.post("/verify", json={
        "original_question": "What is the capital of France?",
        "generated_answer": "Paris is the capital of France.",
    })
    assert response.status_code == 200


def test_batch_verify_endpoint_basic():
    """Batch endpoint should verify multiple answers and return a list."""
    response = client.post("/verify/batch", json=[
        {
            "original_question": "What is the capital of France?",
            "generated_answer": "Paris is the capital of France.",
        },
        {
            "original_question": "What is the population of France?",
            "generated_answer": "France has approximately 68 million people.",
            "trusted_sources": ["wikipedia"],
        },
    ])
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    for item in data:
        assert "extracted_claims" in item
        assert "hallucination_risk_score" in item
        assert "risk_level" in item


def test_batch_verify_empty_list_returns_400():
    """Empty batch should return 400."""
    response = client.post("/verify/batch", json=[])
    assert response.status_code == 400


def test_batch_verify_too_large_returns_400():
    """Batch exceeding limit should return 400."""
    items = [
        {"original_question": "Q?", "generated_answer": "France is a country in Europe."}
        for _ in range(21)
    ]
    response = client.post("/verify/batch", json=items)
    assert response.status_code == 400
