"""Auto-Grounder — FastAPI application entry point.

Run with:
    uvicorn app.main:app --reload --port 8001
"""

from __future__ import annotations

import logging

from fastapi import FastAPI

from app.api.routes import router
from app.config import settings

# ── Logging setup ────────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s  %(name)-30s  %(levelname)-7s  %(message)s",
)

# ── Application instance ────────────────────────────────────────────────
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Self-healing output pipeline that verifies LLM responses via "
        "TruthGuard-AI and auto-corrects hallucinations through an "
        "iterative verify → correct → re-verify loop."
    ),
)

# ── Routes ───────────────────────────────────────────────────────────────
app.include_router(router)


# ── Health check ──────────────────────────────────────────────────────────
@app.get("/health", summary="Health check")
def health() -> dict[str, str]:
    """Lightweight liveness probe."""
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version,
    }
