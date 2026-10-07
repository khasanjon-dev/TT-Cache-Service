"""Application settings loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime application settings."""

    model_config = SettingsConfigDict(env_prefix="CACHE_", env_file=".env", extra="ignore")
