"""Application configuration from environment."""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """App settings. Load from env and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    database_url: str = "sqlite:///./orchestrator.db"
    # For PostgreSQL: postgresql+psycopg2://user:pass@localhost:5432/orchestrator

    # Server
    app_name: str = "Data Pipeline Orchestrator"
    debug: bool = False

    # Retention (global default; overridable per DAG in DB)
    retention_days_default: int = 90

    # Auth: if set, all API endpoints require X-Api-Key header
    api_key: Optional[str] = None

    # Scheduler poll interval in seconds
    scheduler_interval_seconds: int = 60


@lru_cache
def get_settings() -> Settings:
    return Settings()
