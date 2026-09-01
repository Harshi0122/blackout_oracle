"""
Blackout Oracle - Application Configuration.

Centralized configuration for the backend.

Configuration is loaded from environment variables and the project's
.env file.

IMPORTANT:
    Never hard-code API keys, passwords, database credentials, or other
    secrets in source code.

    The .env file must NOT be committed to Git.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Blackout Oracle application settings.

    Values are loaded from environment variables and .env.
    Environment variables take precedence over .env values.
    """

    # ========================================================
    # APPLICATION
    # ========================================================

    app_name: str = Field(
        default="Blackout Oracle",
        description="Application name.",
    )

    app_version: str = Field(
        default="0.1.0",
        description="Application version.",
    )

    environment: Literal[
        "development",
        "testing",
        "staging",
        "production",
    ] = Field(
        default="development",
    )

    debug: bool = Field(
        default=True,
    )

    host: str = Field(
        default="0.0.0.0",
    )

    port: int = Field(
        default=8000,
        ge=1,
        le=65535,
    )


    # ========================================================
    # API
    # ========================================================

    api_prefix: str = Field(
        default="/api/v1",
        description="Base prefix for application API routes.",
    )

    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:5173",
        description=(
            "Comma-separated list of allowed CORS origins."
        ),
    )


    # ========================================================
    # GEMINI / GOOGLE AI
    # ========================================================

    gemini_api_key: str = Field(
        default="",
        description="Google Gemini API key.",
    )

    gemini_model: str = Field(
        default="gemini-2.5-flash",
        description="Gemini model used by the AI agent.",
    )

    gemini_temperature: float = Field(
        default=0.2,
        ge=0.0,
        le=2.0,
    )

    gemini_max_output_tokens: int = Field(
        default=4096,
        ge=1,
    )


    # ========================================================
    # DATABASE
    # ========================================================

    database_url: str = Field(
        default=(
            "postgresql+asyncpg://"
            "blackout:blackout@localhost:5432/"
            "blackout_oracle"
        ),
        description="Async PostgreSQL database URL.",
    )

    database_echo: bool = Field(
        default=False,
        description="Enable SQLAlchemy SQL logging.",
    )

    database_pool_size: int = Field(
        default=10,
        ge=1,
    )

    database_max_overflow: int = Field(
        default=20,
        ge=0,
    )


    # ========================================================
    # TIMESCALEDB / TELEMETRY
    # ========================================================

    telemetry_retention_days: int = Field(
        default=90,
        ge=1,
    )

    telemetry_stale_threshold_seconds: int = Field(
        default=300,
        ge=1,
        description=(
            "Maximum age before telemetry is considered stale."
        ),
    )

    telemetry_poll_interval_seconds: int = Field(
        default=30,
        ge=1,
        description=(
            "Development polling interval for telemetry ingestion."
        ),
    )


    # ========================================================
    # WEATHER
    # ========================================================

    weather_api_key: str = Field(
        default="",
        description="Weather provider API key.",
    )

    weather_provider: str = Field(
        default="",
        description="Weather provider identifier.",
    )

    weather_poll_interval_seconds: int = Field(
        default=300,
        ge=1,
    )


    # ========================================================
    # RISK ENGINE
    # ========================================================

    risk_engine_enabled: bool = Field(
        default=True,
    )

    risk_calculation_interval_seconds: int = Field(
        default=60,
        ge=1,
    )

    risk_high_threshold: float = Field(
        default=80.0,
        ge=0,
        le=100,
    )

    risk_critical_threshold: float = Field(
        default=95.0,
        ge=0,
        le=100,
    )


    # ========================================================
    # SIMULATION ENGINE
    # ========================================================

    simulation_enabled: bool = Field(
        default=True,
    )

    simulation_timeout_seconds: int = Field(
        default=120,
        ge=1,
    )

    simulation_max_concurrent_jobs: int = Field(
        default=2,
        ge=1,
    )


    # ========================================================
    # ALERTING
    # ========================================================

    alerts_enabled: bool = Field(
        default=True,
    )

    alert_cooldown_seconds: int = Field(
        default=300,
        ge=0,
    )


    # ========================================================
    # SECURITY
    # ========================================================

    secret_key: str = Field(
        default="development-secret-change-me",
        description=(
            "Application signing secret. "
            "Must be replaced in production."
        ),
    )

    access_token_expire_minutes: int = Field(
        default=60,
        ge=1,
    )


    # ========================================================
    # LOGGING
    # ========================================================

    log_level: str = Field(
        default="INFO",
    )

    log_json: bool = Field(
        default=False,
    )


    # ========================================================
    # MODEL / DATA SETTINGS
    # ========================================================

    model_directory: str = Field(
        default="./models",
    )

    data_directory: str = Field(
        default="./data",
    )


    # ========================================================
    # PYDANTIC SETTINGS CONFIGURATION
    # ========================================================

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ========================================================
    # HELPER PROPERTIES
    # ========================================================

    @property
    def cors_origin_list(self) -> list[str]:
        """
        Convert the comma-separated CORS string into a list.
        """

        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]

    @property
    def is_production(self) -> bool:
        """Return whether the application is running in production."""

        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """Return whether the application is running in development."""

        return self.environment == "development"


# ============================================================
# SETTINGS SINGLETON
# ============================================================


@lru_cache
def get_settings() -> Settings:
    """
    Return the cached application settings.

    Using lru_cache ensures that the .env file and environment variables
    are loaded once per process instead of creating a new Settings object
    on every request.
    """

    return Settings()


settings = get_settings()


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "Settings",
    "get_settings",
    "settings",
]