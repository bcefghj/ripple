"""LLM 适配层 - 统一接口 + 流式 + 可观测

设计:
- 默认走小米 MiMo (用户首选)
- Fallback: MiniMax → Hunyuan → DeepSeek
- 真流式 acompletion(stream=True)
- 每次调用记录 tokens/latency/cost
- 可注入 user-level BYOK
"""

from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Dict, List, Optional

import httpx


@dataclass
class LLMUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: int = 0
    model: str = ""
    provider: str = ""


@dataclass
class LLMResponse:
    content: str
    usage: LLMUsage = field(default_factory=LLMUsage)
    raw: Optional[Dict[str, Any]] = None


# 默认模型配置
PROVIDERS = {
    "xiaomi": {
        "base_url": "https://token-plan-cn.xiaomimimo.com/v1",
        "default_model": "mimo-v2.5-pro",
        "env_key": "XIAOMI_API_KEY",
    },
    "minimax": {
        "base_url": "https://api.minimax.chat/v1",
        "default_model": "MiniMax-M2.7",
        "env_key": "MINIMAX_API_KEY",
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "default_model": "deepseek-chat",
        "env_key": "DEEPSEEK_API_KEY",
    },
    "hunyuan": {
        "base_url": "https://api.hunyuan.cloud.tencent.com/v1",
        "default_model": "hunyuan-pro",
        "env_key": "HUNYUAN_API_KEY",
    },
}

DEFAULT_FALLBACK = ["xiaomi", "minimax", "deepseek", "hunyuan"]


def _strip_thinking(text: str) -> str:
    """移除 <think>...</think> 标签 (MiMo / DeepSeek-R1 风格)"""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


class LLMClient:
    """统一 LLM 客户端"""

    def __init__(
        self,
        primary: str = "xiaomi",
        fallbacks: Optional[List[str]] = None,
        timeout: int = 90,
        api_keys: Optional[Dict[str, str]] = None,
    ) -> None:
        self.primary = primary
        self.fallbacks = fallbacks or [p for p in DEFAULT_FALLBACK if p != primary]
        self.timeout = timeout
        self.api_keys = api_keys or {}
        self._call_log: List[LLMUsage] = []

    def _get_key(self, provider: str) -> Optional[str]:
        if provider in self.api_keys:
            return self.api_keys[provider]
        env_key = PROVIDERS.get(provider, {}).get("env_key", "")
        return os.environ.get(env_key) if env_key else None

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        provider: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        json_mode: bool = False,
    ) -> LLMResponse:
        """非流式调用 - 带 fallback"""
        providers_to_try = [provider or self.primary] + self.fallbacks
        seen = set()
        last_error = None

        for p in providers_to_try:
            if p in seen:
                continue
            seen.add(p)
            try:
                return await self._call_one(
                    p, messages, model=model,
                    max_tokens=max_tokens, temperature=temperature,
                    json_mode=json_mode,
                )
            except Exception as e:
                last_error = e
                continue

        raise RuntimeError(f"All providers failed. Last error: {last_error}")

    async def _call_one(
        self,
        provider: str,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        json_mode: bool = False,
    ) -> LLMResponse:
        cfg = PROVIDERS.get(provider)
        if not cfg:
            raise ValueError(f"Unknown provider {provider}")

        api_key = self._get_key(provider)
        if not api_key:
            raise ValueError(f"No API key for {provider}")

        use_model = model or cfg["default_model"]
        url = f"{cfg['base_url']}/chat/completions"

        payload: Dict[str, Any] = {
            "model": use_model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        start = time.time()
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.post(url, json=payload, headers=headers)
            r.raise_for_status()
            data = r.json()

        latency_ms = int((time.time() - start) * 1000)
        content = data["choices"][0]["message"]["content"]
        content = _strip_thinking(content)

        usage_data = data.get("usage", {})
        usage = LLMUsage(
            prompt_tokens=usage_data.get("prompt_tokens", 0),
            completion_tokens=usage_data.get("completion_tokens", 0),
            total_tokens=usage_data.get("total_tokens", 0),
            latency_ms=latency_ms,
            model=use_model,
            provider=provider,
        )
        self._call_log.append(usage)

        return LLMResponse(content=content, usage=usage, raw=data)

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        provider: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7,
    ) -> AsyncIterator[str]:
        """真流式调用 - 直接 yield content delta"""
        provider = provider or self.primary
        cfg = PROVIDERS.get(provider)
        if not cfg:
            raise ValueError(f"Unknown provider {provider}")

        api_key = self._get_key(provider)
        if not api_key:
            raise ValueError(f"No API key for {provider}")

        use_model = model or cfg["default_model"]
        url = f"{cfg['base_url']}/chat/completions"

        payload = {
            "model": use_model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
        }

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream("POST", url, json=payload, headers=headers) as r:
                r.raise_for_status()
                async for line in r.aiter_lines():
                    line = line.strip()
                    if not line or line.startswith(":"):
                        continue
                    if line.startswith("data:"):
                        line = line[5:].strip()
                    if line == "[DONE]":
                        break
                    try:
                        import json as _json
                        chunk = _json.loads(line)
                        delta = chunk.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content")
                        if content:
                            yield content
                    except Exception:
                        continue

    def total_usage(self) -> Dict[str, Any]:
        return {
            "calls": len(self._call_log),
            "total_tokens": sum(u.total_tokens for u in self._call_log),
            "by_provider": {
                p: sum(u.total_tokens for u in self._call_log if u.provider == p)
                for p in set(u.provider for u in self._call_log)
            },
        }


_default_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    global _default_client
    if _default_client is None:
        _default_client = LLMClient()
    return _default_client


async def quick_chat(
    system: str,
    user: str,
    json_mode: bool = False,
    max_tokens: int = 2000,
    temperature: float = 0.7,
) -> str:
    """便捷调用"""
    client = get_llm_client()
    response = await client.chat(
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        max_tokens=max_tokens,
        temperature=temperature,
        json_mode=json_mode,
    )
    return response.content
