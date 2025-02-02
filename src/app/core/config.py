"""Configuration Module.

This module handles all configuration settings for the application.
It uses pydantic-settings to validate environment variables and
provides type-safe access to configuration values.
"""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support.

    Attributes:
        app_name (str): The name of the application
        environment (str): The current environment (development, staging, production)
        debug (bool): Debug mode flag

    """

    app_name: str = "My FastAPI App"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False

    class Config:
        """Pydantic model config."""

        env_file = ".env"
        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    """Create and cache application settings.

    Returns:
        Settings: Application settings instance

    """
    return Settings()


settings = get_settings()
