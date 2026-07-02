"""TruthBench configuration settings."""
from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings


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

    # Reporting
    report_output_dir: str = "reports"
    report_format: str = "markdown"

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    def get_dataset_path(self) -> Path:
        """Return absolute path to dataset file."""
        path = Path(self.dataset_path)
        if path.is_absolute():
            return path
        return _get_package_root() / self.dataset_path

    def get_report_dir(self) -> Path:
        """Return absolute path to report output directory."""
        path = Path(self.report_output_dir)
        if path.is_absolute():
            return path
        return _get_package_root() / self.report_output_dir


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()