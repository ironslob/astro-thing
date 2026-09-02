from __future__ import annotations

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def sqlalchemy_database_url(url: str) -> str:
    """Accept postgres:// and postgresql:// URLs from hosts like Railway."""
    if url.startswith("postgres://"):
        url = "postgresql://" + url.removeprefix("postgres://")
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url.removeprefix("postgresql://")
    return url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"
    log_level: str = "INFO"
    secret_key: str = "dev-secret-key-change-me"
    scoring_version: str = "1.0.0"

    database_url: str = "sqlite+pysqlite:///./astro_window.db"

    @field_validator("database_url")
    @classmethod
    def use_psycopg_driver(cls, value: str) -> str:
        return sqlalchemy_database_url(value)

    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_from: str = "Astro Window <noreply@local.test>"
    frontend_base_url: str = "http://localhost:8080"
    session_cookie_name: str = "astro_session"
    session_cookie_secure: bool = False

    weather_provider: str = "open-meteo"
    open_meteo_base_url: str = "https://api.open-meteo.com"
    open_meteo_geocoding_base_url: str = "https://geocoding-api.open-meteo.com"
    postcodes_io_base_url: str = "https://api.postcodes.io"
    weather_cache_ttl_seconds: int = 1800
    weather_stale_ttl_seconds: int = 7200
    weather_request_timeout_seconds: float = 10.0
    geocoding_request_timeout_seconds: float = 8.0
    geocoding_cache_ttl_seconds: int = 86400

    forecast_rate_limit_per_minute: int = 60
    geocoding_rate_limit_per_minute: int = 30

    timezone_default: str = "Europe/London"

    openngc_ngc_url: str = (
        "https://raw.githubusercontent.com/mattiaverga/OpenNGC/master/database_files/NGC.csv"
    )
    openngc_addendum_url: str = (
        "https://raw.githubusercontent.com/mattiaverga/OpenNGC/master/database_files/addendum.csv"
    )


settings = Settings()
