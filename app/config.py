"""Configuration module for the TrailBlazeApp-Scrapers project."""

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
    DB_PASSWORD: str

    # Cache settings
    CACHE_TTL: int = 86400  # 24 hours
    CACHE_MAX_SIZE: int = 128

    # AERC specific settings
    AERC_BASE_URL: str = "https://aerc.org/wp-admin/admin-ajax.php"
    AERC_CALENDAR_URL: str = "https://aerc.org/calendar"

    class Config:
        """Pydantic config class."""
        env_file = ".env"


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
