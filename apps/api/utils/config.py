"""配置管理:从环境变量加载所有配置"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

try:
    from pydantic import Field
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ImportError:
    # Python 3.9 兼容回退
    from pydantic import BaseSettings, Field
    SettingsConfigDict = None


class Settings(BaseSettings):
    """全局配置对象,从 .env 加载"""

    if SettingsConfigDict is not None:
        model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            extra="ignore",
        )

    # App
    app_name: str = "Ripple"
    app_env: str = "development"
    app_port: int = 8000
    app_host: str = "0.0.0.0"

    # Security
    secret_key: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    # Database
    database_url: str = "postgresql+asyncpg://ripple:ripple@localhost:5432/ripple"
    sync_database_url: str = "postgresql://ripple:ripple@localhost:5432/ripple"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # MiniMax
    minimax_api_key: str = ""
    minimax_api_base: str = "https://api.minimax.chat/v1"
    minimax_default_model: str = "MiniMax-Text-01"

    # Hunyuan
    hunyuan_api_key: str = ""
    hunyuan_api_base: str = "https://api.hunyuan.cloud.tencent.com/v1"
    hunyuan_default_model: str = "hunyuan-turbos-latest"

    # Other LLM providers
    deepseek_api_key: str = ""
    doubao_api_key: str = ""
    dashscope_api_key: str = ""
    zhipu_api_key: str = ""
    moonshot_api_key: str = ""
    openai_api_key: str = ""
    anthropic_api_key: str = ""

    # Memory
    memory_root: str = "./.ripple/memory"
    skills_root: str = "./agent/skills"

    # Observability
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"
    sentry_dsn: str = ""

    # Rate limit / Budget
    default_rate_limit_per_minute: int = 60
    default_daily_token_budget: int = 100000

    # Compression
    effective_context_window: int = 128000
    autocompact_buffer_tokens: int = 13000
    manual_compact_buffer_tokens: int = 3000
    max_consecutive_autocompact_failures: int = 3

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:5173,http://localhost:8501"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def memory_root_path(self) -> Path:
        p = Path(self.memory_root).expanduser().resolve()
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def skills_root_path(self) -> Path:
        p = Path(self.skills_root).expanduser().resolve()
        return p


@lru_cache()
def get_settings() -> Settings:
    """单例配置对象"""
    return Settings()


settings = get_settings()
