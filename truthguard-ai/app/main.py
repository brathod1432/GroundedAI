"""TruthGuardAI — FastAPI application entry point.

Run with:
    uvicorn app.main:app --reload
"""

from __future__ import annotations

import logging

from fastapi import FastAPI

from app.api.routes import router
from app.config import settings

# ── Logging setup ────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s  %(name)-30s  %(levelname)-7s  %(message)s",
)

# ── Application instance ────────────────────────────────────────────────
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "LLM Hallucination Reduction & Grounded Verification Framework. "
        "Submit a generated answer and receive a structured verification "
        "report with per-claim verdicts, citations, and a hallucination "
        "risk score."
    ),
)

# ── Routes ───────────────────────────────────────────────────────────────
app.include_router(router)


# ── Health check ──────────────────────────────────────────────────────────
@app.get("/health", summary="Health check")
def health() -> dict[str, str]:
    """Lightweight liveness probe."""
    return {"status": "ok", "version": settings.app_version}
