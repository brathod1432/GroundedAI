"""Smoke tests for the FastAPI application entry point."""

from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint() -> None:
    """The app should import cleanly and expose the health endpoint."""
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
