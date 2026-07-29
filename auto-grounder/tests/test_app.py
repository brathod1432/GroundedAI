"""Smoke tests for the FastAPI application."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint() -> None:
    """GET /health should return 200 with the correct service name."""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "Auto-Grounder"
    assert "version" in data


def test_ground_endpoint_returns_200() -> None:
    """POST /ground with a valid payload should return 200 with expected fields."""
    response = client.post(
        "/ground",
        json={
            "question": "What is the capital of France?",
            "initial_answer": "Paris is the capital of France.",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "final_answer" in data
    assert "grounded" in data
    assert "risk_score" in data
    assert "risk_level" in data
    assert "total_iterations" in data
    assert "iterations" in data
    assert "summary" in data


def test_ground_endpoint_returns_grounded_true() -> None:
    """Using mock clients, the pipeline should eventually ground the answer."""
    response = client.post(
        "/ground",
        json={
            "question": "What is the capital of France?",
            "initial_answer": (
                "Berlin is the capital of France and it has 200 million people."
            ),
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["grounded"] is True
    assert data["risk_level"] == "LOW"
    assert data["total_iterations"] >= 1


def test_ground_endpoint_with_trusted_sources() -> None:
    """Trusted sources should be accepted without error."""
    response = client.post(
        "/ground",
        json={
            "question": "What is AI?",
            "initial_answer": "AI is Artificial Intelligence.",
            "trusted_sources": ["wikipedia", "arxiv"],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "final_answer" in data


def test_ground_endpoint_with_max_iterations() -> None:
    """The max_iterations override should be honoured."""
    response = client.post(
        "/ground",
        json={
            "question": "What is the capital of France?",
            "initial_answer": "Berlin is the capital of France.",
            "max_iterations": 1,
        },
    )
    assert response.status_code == 200
    data = response.json()
    # With max_iterations=1 and mock returning HIGH on first call,
    # the answer should NOT be grounded.
    assert data["grounded"] is False
    assert data["total_iterations"] == 1


def test_ground_endpoint_missing_required_fields() -> None:
    """Missing required fields should return 422."""
    response = client.post(
        "/ground",
        json={"question": "What is France?"},
    )
    assert response.status_code == 422


def test_ground_endpoint_empty_question() -> None:
    """An empty question should be rejected by validation."""
    response = client.post(
        "/ground",
        json={
            "question": "",
            "initial_answer": "Some answer.",
        },
    )
    assert response.status_code == 422
