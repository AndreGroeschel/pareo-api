"""Configuration Module.

This module handles all configuration settings for the application.
It uses pydantic-settings to validate environment variables and
provides type-safe access to configuration values.
"""

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support.

    All settings must be provided via environment variables.
    Missing required variables will raise a ValidationError.
    """

    # Define all required fields but without defaults
    app_name: str = Field(default=...)
    environment: str = Field(default=...)
    debug: bool = Field(default=...)
    allowed_hosts: str = Field(default=...)
    database_url: str = Field(default=...)
    openai_api_key: str = Field(default=...)
    openrouter_api_key: str = Field(default=...)
    openrouter_base_url: str = Field(default=...)
    embedding_model: str = Field(default=...)
    reasoning_model: str = Field(default=...)
    clerk_pem_public_key: str = Field(default=...)
    clerk_webhook_secret: str = Field(default=...)
    clerk_secret_key: str = Field(default=...)
    clerk_base_url: str = Field(default=...)
    stripe_secret_key: str = Field(default=...)
    stripe_webhook_secret: str = Field(default=...)

    @field_validator("allowed_hosts")
    @classmethod
    def parse_allowed_hosts(cls, v: str) -> list[str]:
        """Parse allowed hosts env variable."""
        if v == "*":
            return ["*"]
        return [host.strip() for host in v.split(",")]

    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=False, env_nested_delimiter="__", env_prefix="", extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    """Create and cache application settings."""
    try:
        return Settings()
    except Exception as e:
        raise ValueError("Missing required environment variables") from e


settings = get_settings()
