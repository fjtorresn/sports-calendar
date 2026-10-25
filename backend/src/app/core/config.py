"""Application settings.

Values are read from environment variables (and from a ``.env`` file in development).
Secrets have no defaults: if one is missing the app fails at startup instead of
silently connecting to something unexpected.
"""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # The .env lives at the monorepo root; the current directory is checked too.
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: Literal["development", "test", "production"] = "development"
    database_url: str
    redis_url: str


@lru_cache
def get_settings() -> Settings:
    """Return the settings, read once per process."""
    return Settings()
