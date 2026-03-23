from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT_DIR / ".env.bot.secret"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    bot_token: str | None = None
    lms_api_base_url: str = "http://localhost:42002"
    lms_api_key: str | None = None
    llm_api_key: str | None = None
    llm_api_base_url: str = "http://localhost:42005/v1"
    llm_api_model: str | None = None


def load_settings() -> Settings:
    return Settings()
