# ABOUTME: Centralized configuration management using Pydantic BaseSettings
# ABOUTME: Loads environment variables with type validation and defaults

from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings with environment variable loading and validation."""

    # Database Configuration
    POSTGRES_DB: str = "portfolio"
    POSTGRES_USER: str = "trader"
    POSTGRES_PASSWORD: str
    DATABASE_URL: str

    # Redis Configuration
    REDIS_URL: str = "redis://redis:6379"

    # Anthropic Claude Configuration
    ANTHROPIC_API_KEY: str
    ANTHROPIC_MODEL: str = "claude-sonnet-4-5-20250929"  # Latest Sonnet
    ANTHROPIC_MAX_TOKENS: int = 4096
    ANTHROPIC_TEMPERATURE: float = 0.3  # Lower for more factual analysis
    ANTHROPIC_TIMEOUT: int = 30  # seconds
    ANTHROPIC_MAX_RETRIES: int = 3
    ANTHROPIC_RATE_LIMIT: int = 50  # requests per minute

    # Alpha Vantage Configuration (Optional)
    ALPHA_VANTAGE_API_KEY: Optional[str] = None
    ALPHA_VANTAGE_RATE_LIMIT_PER_MINUTE: int = 5
    ALPHA_VANTAGE_RATE_LIMIT_PER_DAY: int = 100

    model_config = ConfigDict(
        env_file="../.env",  # .env is in project root, one level up from backend
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


def get_settings() -> Settings:
    """
    Get settings instance.

    Use this function instead of importing a global settings object
    to avoid initialization errors in tests.
    """
    return Settings()
