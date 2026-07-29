"""Auto-Grounder — FastAPI application entry point.

Run with:
    uvicorn app.main:app --reload --port 8001
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

from app.api.routes import router
from app.config import settings

# ── Logging setup ────────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s  %(name)-30s  %(levelname)-7s  %(message)s",
)

logger = logging.getLogger(__name__)
_AUTH_EXEMPT_PATHS = {"/health", "/api/v1/health", "/docs", "/openapi.json", "/redoc"}


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Enforce X-API-Key when GROUNDER_API_KEY is set.

    Empty key (default) = dev mode, no auth enforced.
    """

    async def dispatch(self, request: Request, call_next):
        configured_key = settings.api_key.get_secret_value()
        if not configured_key or request.url.path in _AUTH_EXEMPT_PATHS:
            return await call_next(request)
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

# ── Rate limiter (S9) ────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── Security middleware ───────────────────────────────────────────────────
app.add_middleware(APIKeyMiddleware)

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
