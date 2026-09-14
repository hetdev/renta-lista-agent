from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    aws_region: str = "us-east-1"
    aws_profile: str = "rentalista"
    bedrock_model_id: str = "amazon.nova-micro-v1:0"
    demo_mode: bool = True
    default_locale: Literal["es", "en"] = "en"
    browser_session_timeout_seconds: int = 1800
    browser_viewport_width: int = 1280
    browser_viewport_height: int = 800
    max_upload_bytes: int = 5_242_880
    max_files_per_case: int = 10
    max_jobs_per_case: int = 12
    max_daily_cases: int = 200
    max_daily_jobs: int = 300
    max_browser_sessions: int = 2
    tax_year: Literal[2025] = 2025
    rule_version: str = "ag2025-0.1.0"


@lru_cache
def get_settings() -> Settings:
    return Settings()
