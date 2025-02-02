"""Configuration Module.

This module handles all configuration settings for the application.
It uses pydantic-settings to validate environment variables and
provides type-safe access to configuration values.
"""

from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    app_name: str = "My FastAPI App"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    allowed_hosts: str = "*"  # Changed to str with default

    @field_validator("allowed_hosts")
    @classmethod
    def parse_allowed_hosts(cls, v: str) -> list[str]:
        """Parse allowed hosts env variable."""
        if v == "*":
            return ["*"]
        return [host.strip() for host in v.split(",")]

    class Config:
        """Pydantic model config."""

        env_file = ".env"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    """Create and cache application settings."""
    return Settings()


settings = get_settings()
