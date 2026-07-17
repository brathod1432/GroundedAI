"""Prompt Shield - FastAPI application entry point."""
from __future__ import annotations

from fastapi import FastAPI

from app.api.routes import router
from app.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "LLM Security Proxy that intercepts prompts to detect prompt injection, "
        "scrub PII, and filter toxic content before forwarding to LLM providers."
    ),
)

app.include_router(router)
