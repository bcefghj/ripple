"""Ripple 5.0 configuration — loads .env and syncs to os.environ."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"
SKILLS_DIR = OUTPUT_DIR / "skills"
CONTENT_DIR = OUTPUT_DIR / "content"
IMAGES_DIR = OUTPUT_DIR / "images"
DB_PATH = PROJECT_ROOT / "ripple.db"

load_dotenv(PROJECT_ROOT / ".env", override=False)


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
    minimax_search_host: str = "https://api.minimaxi.com"

    serper_api_key: str = ""
    exa_api_key: str = ""
    tavily_api_key: str = ""
    brave_api_key: str = ""
    you_api_key: str = ""
    jina_api_key: str = ""

    hunyuan_api_key: str = ""
    hunyuan_api_base: str = "https://api.hunyuan.cloud.tencent.com/v1"
    hunyuan_model: str = "hunyuan-turbos-latest"

    qwen_api_key: str = ""
    qwen_api_base: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    qwen_model: str = "qwen-plus"

    dailyhot_api_base: str = "https://hot.imsyy.top"
    searxng_url: str = ""


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
