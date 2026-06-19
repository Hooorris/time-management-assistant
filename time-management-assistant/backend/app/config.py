from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    app_name: str = "Time Management Assistant API"
    app_env: str = "development"
    app_timezone: str = "Asia/Shanghai"
    api_prefix: str = ""
    database_url: str = ""
    database_echo: bool = False
    mcp_auth_required: bool = True
    mcp_auth_token: str = ""

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
