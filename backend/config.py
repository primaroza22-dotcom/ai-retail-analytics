"""Application settings loaded from environment variables.

Secrets are read from the environment (or a local ``.env`` file) and are never
hard-coded. Production uses PostgreSQL via ``DATABASE_URL``; tests override the
URL with SQLite.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the FastAPI backend."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "AI Retail Analytics"
    app_env: str = "development"
    app_debug: bool = True
    app_version: str = "0.1.0"

    api_host: str = "127.0.0.1"
    api_port: int = 8000

    log_level: str = "INFO"

    # PostgreSQL in production; SQLite is used only for tests.
    database_url: str = "sqlite:///./data/arap.db"
    database_pool_size: int = 5
    database_pool_max_overflow: int = 10
    database_pool_timeout: int = 30

    # Allowed frontend origins for CORS (development default only).
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # Real-time WebSocket keepalive interval (seconds).
    websocket_heartbeat_interval: float = 30.0

    # Business timezone for daily analytics/forecasting aggregation.
    analytics_timezone: str = "UTC"


@lru_cache
def get_settings() -> Settings:
    """Return the cached application settings."""
    return Settings()
