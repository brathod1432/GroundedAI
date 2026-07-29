"""Tests for the feedback endpoint."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_submit_feedback_returns_id():
    response = client.post("/feedback/", json={
        "request_id": "test-001",
        "claim_index": 0,
        "predicted_verdict": "SUPPORTED",
        "correct_verdict": "NOT_ENOUGH_EVIDENCE",
        "comment": "The evidence was about a different country.",
    })
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["id"] > 0
    assert "message" in data


def test_feedback_summary_returns_stats():
    response = client.get("/feedback/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_feedback" in data
    assert "verdict_corrections" in data
    assert isinstance(data["total_feedback"], int)
