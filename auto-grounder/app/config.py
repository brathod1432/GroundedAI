"""Application configuration loaded from environment variables.

Uses pydantic-settings so values can come from .env files, OS env vars,
or sensible defaults.  No real API keys are required — the mock backends
work without them.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central configuration for Auto-Grounder.

    Every setting has a default so the application runs out of the box
    with mock backends.  Override via environment variables (prefixed
    with ``GROUNDER_``) or a ``.env`` file.
    """

    # ── API ──────────────────────────────────────────────────────────────
    app_name: str = "Auto-Grounder"
    app_version: str = "0.1.0"

    # ── TruthGuard-AI connection ─────────────────────────────────────────
    truthguard_url: str = "http://127.0.0.1:8000"

    # ── LLM backend ─────────────────────────────────────────────────────
    llm_provider: str = "mock"  # "mock" | "openai"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # ── Grounding loop ───────────────────────────────────────────────────
    max_grounding_iterations: int = 3
    acceptable_risk_level: str = "LOW"  # stop iterating when risk ≤ this

    # ── Logging ──────────────────────────────────────────────────────────
    log_level: str = "INFO"

    model_config = {
        "env_prefix": "GROUNDER_",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


# Singleton used across modules.
settings = Settings()
