"""Application configuration loaded from environment variables.

Uses pydantic-settings so values can come from .env files, OS env vars,
or sensible defaults. No real API keys are required — the mock backends
work without them.
"""

from pydantic import SecretStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central configuration for TruthGuardAI.

    Every setting has a default so the application runs out of the box
    with mock backends. Override via environment variables or a .env file.
    """

    # ── API ──────────────────────────────────────────────────────────────
    app_name: str = "TruthGuardAI"
    app_version: str = "0.1.0"
    debug: bool = False

    # ── API authentication (empty = no auth required, dev-mode default) ─
    # Set TRUTHGUARD_API_KEY to require X-API-Key header on all endpoints.
    api_key: SecretStr = SecretStr("")

    # ── LLM backend ─────────────────────────────────────────────────────
    llm_provider: str = "mock"  # "mock" | "openai" | "anthropic"
    openai_api_key: SecretStr = SecretStr("")   # was str; SecretStr prevents logging
    openai_model: str = "gpt-4o-mini"
    anthropic_api_key: SecretStr = SecretStr("")
    anthropic_model: str = "claude-sonnet-4-20250514"

    # ── Search / evidence backend ───────────────────────────────────────
    search_provider: str = "mock"  # "mock" | "tavily" | "serpapi"
    tavily_api_key: SecretStr = SecretStr("")
    serpapi_api_key: SecretStr = SecretStr("")

    # ── Verification defaults ────────────────────────────────────────────
    default_trusted_sources: list[str] = ["wikipedia", "world-bank"]
    max_claims_per_answer: int = 20
    evidence_per_claim: int = 3

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


# Singleton used across modules.
settings = Settings()
