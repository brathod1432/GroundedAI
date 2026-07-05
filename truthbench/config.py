"""TruthBench configuration settings."""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


def _get_package_root() -> Path:
    """Get the truthbench package root directory."""
    return Path(__file__).parent


class Settings(BaseSettings):
    """TruthBench configuration loaded from environment variables."""

    # Dataset - resolved relative to package root
    dataset_path: str = "datasets/sample_eval_dataset.json"

    # Evaluation
    verdict_labels: list[str] = ["SUPPORTED", "CONTRADICTED", "NOT_ENOUGH_EVIDENCE"]
    risk_levels: list[str] = ["LOW", "MEDIUM", "HIGH"]
    confidence_threshold: float = 0.7
    evaluation_seed: int = 42

    # Reporting
    report_output_dir: str = "reports"
    report_format: str = "markdown"

    # Logging
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    def resolve_path(self, value: str | Path) -> Path:
        """Resolve relative paths against the package first, then the CWD."""
        path = Path(value)
        if path.is_absolute():
            return path

        package_path = _get_package_root() / path
        if package_path.exists():
            return package_path

        return path

    def get_dataset_path(self) -> Path:
        """Return absolute path to dataset file."""
        return self.resolve_path(self.dataset_path)

    def get_report_dir(self) -> Path:
        """Return absolute path to report output directory."""
        return self.resolve_path(self.report_output_dir)


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
