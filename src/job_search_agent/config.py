"""Typed, environment-backed local application settings."""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="JSA_",
        env_file=".env",
        extra="ignore",
    )
    database_url: str = "sqlite:///data/jobs.db"
    log_level: str = "INFO"
