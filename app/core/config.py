"""Application settings loaded from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime application settings."""

    model_config = SettingsConfigDict(env_prefix="CACHE_", env_file=".env", extra="ignore")

    database_url: str = (
        "postgresql+psycopg://cache_user:cache_user_dev@localhost:5432/cache_db"
    )


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings instance."""
    return Settings()
