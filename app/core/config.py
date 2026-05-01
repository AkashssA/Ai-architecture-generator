from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI System Architecture Generator"
    app_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = False

    groq_api_key: Optional[str] = None
    groq_model: str = "llama-3.3-70b-versatile"
    groq_timeout_seconds: float = 45.0

    redis_url: Optional[str] = None
    cache_ttl_seconds: int = 3600

    api_key: Optional[str] = Field(
        default=None,
        description="Optional shared secret required via the X-API-Key header.",
    )
    rate_limit_requests: int = 20
    rate_limit_window_seconds: int = 60

    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
