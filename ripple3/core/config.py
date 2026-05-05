"""Ripple 3.0 configuration — loads .env via pydantic-settings."""

from __future__ import annotations

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"
SKILLS_DIR = OUTPUT_DIR / "skills"
CONTENT_DIR = OUTPUT_DIR / "content"
IMAGES_DIR = OUTPUT_DIR / "images"
DB_PATH = PROJECT_ROOT / "ripple.db"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    xiaomi_api_key: str = ""
    xiaomi_api_base: str = "https://token-plan-cn.xiaomimimo.com/v1"
    xiaomi_model: str = "mimo-v2.5-pro"

    minimax_api_key: str = ""
    minimax_api_base: str = "https://api.minimax.chat/v1"
    minimax_text_model: str = "MiniMax-M2.7"
    minimax_image_model: str = "image-01"


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
