"""TruthGuardAI — FastAPI application entry point.

Run with:
    uvicorn app.main:app --reload
"""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.api.feedback import feedback_router
from app.api.routes import router
from app.config import settings

# ── Logging setup ────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s  %(name)-30s  %(levelname)-7s  %(message)s",
)

logger = logging.getLogger(__name__)

# Paths that are always accessible without an API key (monitoring probes).
_AUTH_EXEMPT_PATHS = {"/health", "/api/v1/health", "/docs", "/openapi.json", "/redoc"}


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Enforce X-API-Key authentication when a key is configured.

    When ``settings.api_key`` is empty (default), all requests are allowed
    so the service works out of the box without configuration. Set the
    ``TRUTHGUARD_API_KEY`` environment variable in production to activate
    authentication on all non-exempt endpoints.
    """

    async def dispatch(self, request: Request, call_next):
        configured_key = settings.api_key.get_secret_value()
        # Dev mode: no key configured → skip auth
        if not configured_key:
            return await call_next(request)
        # Exempt paths: health, docs
        if request.url.path in _AUTH_EXEMPT_PATHS:
            return await call_next(request)
        # Check header
        provided_key = request.headers.get("X-API-Key", "")
        if provided_key != configured_key:
            logger.warning(
                "Unauthorized request to %s — invalid or missing X-API-Key",
                request.url.path,
            )
            return JSONResponse(
                status_code=403,
                content={"detail": "Invalid or missing X-API-Key header."},
            )
        return await call_next(request)


# ── Rate limiter (S9) ────────────────────────────────────────────────────
# In-memory limiter — no Redis required. Replace get_remote_address with a
# custom key function (e.g., X-API-Key) in multi-tenant production deployments.
limiter = Limiter(key_func=get_remote_address)

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

# Attach limiter and its 429 exception handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── Security middleware ───────────────────────────────────────────────────
app.add_middleware(APIKeyMiddleware)

# ── Routes ───────────────────────────────────────────────────────────────
# Primary versioned prefix — all new integrations should use /api/v1/
app.include_router(router, prefix="/api/v1")
app.include_router(feedback_router, prefix="/api/v1")

# Backward-compat aliases at root for existing integrations (deprecated)
app.include_router(router)
app.include_router(feedback_router)


# ── Health check ──────────────────────────────────────────────────────────
@app.get("/health", summary="Health check")
@app.get("/api/v1/health", summary="Health check (v1)", include_in_schema=False)
def health() -> dict[str, str]:
    """Lightweight liveness probe — always accessible without API key."""
    return {"status": "ok", "version": settings.app_version}
