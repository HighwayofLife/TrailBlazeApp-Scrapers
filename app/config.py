"""Configuration module for the TrailBlazeApp-Scrapers project."""

import logging
from typing import Dict, Any
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Uses pydantic for validation and environment variable loading.
    Settings are loaded from environment variables or .env file.
    """

    # Database settings
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "trailblaze"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = ""  # Default empty string, should be set in environment or .env

    # Cache settings
    CACHE_TTL: int = 86400  # 24 hours
    CACHE_MAX_SIZE: int = 128

    # Logging settings
    LOG_LEVEL: str = "INFO"

    # AERC specific settings
    AERC_BASE_URL: str = "https://aerc.org/wp-admin/admin-ajax.php"
    AERC_CALENDAR_URL: str = "https://aerc.org/calendar"

    model_config = {
        "env_file": ".env",
        "extra": "ignore"  # Allow extra fields to be ignored
    }


@lru_cache()
def get_settings() -> Settings:
    """
    Get application settings singleton.

    Returns:
        Settings: Application settings instance
    """
    return Settings()


def get_db_config() -> Dict[str, Any]:
    """
    Get database configuration dictionary.

    Returns:
        Dict[str, Any]: Database configuration parameters
    """
    settings = get_settings()
    return {
        "host": settings.DB_HOST,
        "port": settings.DB_PORT,
        "database": settings.DB_NAME,
        "user": settings.DB_USER,
        "password": settings.DB_PASSWORD
    }


def get_log_level() -> int:
    """
    Get log level as integer value.

    Returns:
        int: Logging level (e.g., logging.INFO)
    """
    settings = get_settings()
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    return level_map.get(settings.LOG_LEVEL.upper(), logging.INFO)
