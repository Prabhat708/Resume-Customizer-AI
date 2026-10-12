"""
app/config.py — Application configuration loaded from environment variables.
No secrets are exposed through any API endpoint or log output.
"""
from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application metadata
    app_version: str = "0.1.0"

    # AI provider — key is never returned by any endpoint
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-2.5-flash", alias="GEMINI_MODEL")

    # File upload and parsing limits
    max_file_size_mb: int = Field(default=5, alias="MAX_FILE_SIZE_MB")
    max_pages: int = Field(default=10, alias="MAX_PAGES")
    min_extracted_chars: int = Field(default=50, alias="MIN_EXTRACTED_CHARS")
    min_extracted_words: int = Field(default=10, alias="MIN_EXTRACTED_WORDS")

    # CORS — comma-separated list of allowed origins
    cors_origins_raw: str = Field(default="http://localhost:3000", alias="CORS_ORIGINS")

    @property
    def cors_origins(self) -> List[str]:
        return [o.strip() for o in self.cors_origins_raw.split(",") if o.strip()]

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024

    @property
    def gemini_configured(self) -> bool:
        """Returns True if GEMINI_MODEL env var is set and non-empty."""
        return bool(self.gemini_model and self.gemini_model.strip())


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached settings singleton. Use as a FastAPI dependency."""
    return Settings()
