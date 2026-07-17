"""Smoke tests for the FastAPI application entry point."""

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
