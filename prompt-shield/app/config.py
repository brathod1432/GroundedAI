from __future__ import annotations

import functools

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_name: str = "Prompt Shield"
    app_version: str = "0.1.0"

    # LLM provider: mock, openai, anthropic
    llm_provider: str = "mock"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # Feature toggles
    pii_detection_enabled: bool = True
    injection_detection_enabled: bool = True
    toxicity_filtering_enabled: bool = True

    # Thresholds (0.0-1.0, above this blocks the request)
    injection_threshold: float = 0.7
    toxicity_threshold: float = 0.7

    # Limits
    max_prompt_length: int = 50000

    # Logging
    log_level: str = "INFO"

    model_config = {
        "env_prefix": "SHIELD_",
        "env_file": ".env",
        "extra": "ignore",
    }


@functools.lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
