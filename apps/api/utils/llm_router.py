"""LLM Router:统一抽象多个 LLM Provider

支持的 Provider:
- MiniMax (主力,最新 M2.7)
- 腾讯混元 (兜底 + 合规叙事)
- DeepSeek
- 豆包 (字节火山方舟)
- 通义千问 (阿里 DashScope)
- 智谱 GLM
- Kimi (Moonshot)
- OpenAI / Azure OpenAI
- Anthropic Claude
- 本地: Ollama / LM Studio / MLX

设计原则:
- BYOK 优先 (用户自带 Key 时不上传服务器)
- LiteLLM 做底层抽象 (https://docs.litellm.ai)
- Fallback 链路:主模型失败自动切兜底
- 成本追踪:每次调用记录 tokens / cost
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, AsyncIterator

from loguru import logger

from .config import settings


@dataclass
class ProviderConfig:
    """单个 Provider 的配置"""
    name: str
    display_name: str
    api_key: str
    api_base: str
    default_model: str
    available_models: List[str] = field(default_factory=list)
    is_local: bool = False
    requires_byok: bool = False


@dataclass
class LLMResponse:
    """统一 LLM 响应格式"""
    content: str
    model: str
    provider: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: int = 0
    raw: Optional[Dict[str, Any]] = None


# ============================================================
# Provider 注册表
# ============================================================

PROVIDERS: Dict[str, ProviderConfig] = {
    "minimax": ProviderConfig(
        name="minimax",
        display_name="MiniMax",
        api_key=settings.minimax_api_key,
        api_base=settings.minimax_api_base,
        default_model=settings.minimax_default_model,
        available_models=[
            "MiniMax-Text-01",
            "MiniMax-M1",
            "abab6.5s-chat",
            "abab6.5g-chat",
        ],
    ),
    "hunyuan": ProviderConfig(
        name="hunyuan",
        display_name="腾讯混元",
        api_key=settings.hunyuan_api_key,
        api_base=settings.hunyuan_api_base,
        default_model=settings.hunyuan_default_model,
        available_models=[
            "hunyuan-turbos-latest",
            "hunyuan-pro",
            "hunyuan-standard",
            "hunyuan-lite",
        ],
    ),
    "deepseek": ProviderConfig(
        name="deepseek",
        display_name="DeepSeek",
        api_key=settings.deepseek_api_key,
        api_base="https://api.deepseek.com/v1",
        default_model="deepseek-chat",
        available_models=["deepseek-chat", "deepseek-coder", "deepseek-reasoner"],
    ),
    "doubao": ProviderConfig(
        name="doubao",
        display_name="字节豆包",
        api_key=settings.doubao_api_key,
        api_base="https://ark.cn-beijing.volces.com/api/v3",
        default_model="doubao-pro-32k",
        available_models=["doubao-pro-32k", "doubao-pro-128k", "doubao-lite-32k"],
    ),
    "dashscope": ProviderConfig(
        name="dashscope",
        display_name="阿里通义",
        api_key=settings.dashscope_api_key,
        api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
        default_model="qwen-max",
        available_models=["qwen-max", "qwen-plus", "qwen-turbo", "qwen-long"],
    ),
    "zhipu": ProviderConfig(
        name="zhipu",
        display_name="智谱 GLM",
        api_key=settings.zhipu_api_key,
        api_base="https://open.bigmodel.cn/api/paas/v4",
        default_model="glm-4-plus",
        available_models=["glm-4-plus", "glm-4-air", "glm-4-flash"],
    ),
    "moonshot": ProviderConfig(
        name="moonshot",
        display_name="月之暗面 Kimi",
        api_key=settings.moonshot_api_key,
        api_base="https://api.moonshot.cn/v1",
        default_model="moonshot-v1-32k",
        available_models=["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"],
    ),
    "openai": ProviderConfig(
        name="openai",
        display_name="OpenAI",
        api_key=settings.openai_api_key,
        api_base="https://api.openai.com/v1",
        default_model="gpt-4o-mini",
        available_models=["gpt-4o", "gpt-4o-mini", "o1-mini", "o1-preview"],
        requires_byok=True,
    ),
    "anthropic": ProviderConfig(
        name="anthropic",
        display_name="Anthropic Claude",
        api_key=settings.anthropic_api_key,
        api_base="https://api.anthropic.com",
        default_model="claude-sonnet-4-5",
        available_models=[
            "claude-sonnet-4-5",
            "claude-opus-4-5",
            "claude-haiku-4-5",
        ],
        requires_byok=True,
    ),
    "ollama": ProviderConfig(
        name="ollama",
        display_name="本地 Ollama",
        api_key="ollama",
        api_base="http://localhost:11434/v1",
        default_model="qwen2.5:14b",
        available_models=["qwen2.5:14b", "qwen2.5:7b", "llama3.2:8b", "deepseek-r1:14b"],
        is_local=True,
    ),
    "lmstudio": ProviderConfig(
        name="lmstudio",
        display_name="本地 LM Studio",
        api_key="lm-studio",
        api_base="http://localhost:1234/v1",
        default_model="local-model",
        is_local=True,
    ),
}


# ============================================================
# LLM Router 主类
# ============================================================


class LLMRouter:
    """
    LLM 路由器,统一调用多 Provider
    
    使用方式:
        router = LLMRouter()
        resp = await router.complete(
            messages=[{"role": "user", "content": "Hello"}],
            provider="minimax",  # 可选,默认 minimax
            model="MiniMax-Text-01",  # 可选,使用 provider 默认
            fallback_providers=["hunyuan", "deepseek"],  # 可选,失败时fallback
        )
    """

    def __init__(self, default_provider: str = "minimax"):
        self.default_provider = default_provider
        self._setup_litellm()

    def _setup_litellm(self):
        """配置 LiteLLM 全局参数"""
        try:
            import litellm
            # 设置统一超时
            litellm.request_timeout = 60
            # 关闭遥测
            litellm.suppress_debug_info = True
            self.litellm_available = True
        except ImportError:
            logger.warning("LiteLLM not installed, falling back to direct HTTP calls")
            self.litellm_available = False

    def get_provider(self, provider_name: str) -> Optional[ProviderConfig]:
        """获取 Provider 配置"""
        return PROVIDERS.get(provider_name)

    def list_available_providers(self, include_byok: bool = True) -> List[ProviderConfig]:
        """列出所有有 API Key 配置的 Provider"""
        result = []
        for name, cfg in PROVIDERS.items():
            if cfg.is_local or cfg.api_key:
                result.append(cfg)
            elif include_byok and cfg.requires_byok:
                result.append(cfg)
        return result

    async def complete(
        self,
        messages: List[Dict[str, str]],
        provider: Optional[str] = None,
        model: Optional[str] = None,
        api_key_override: Optional[str] = None,  # BYOK 用户自带 Key
        api_base_override: Optional[str] = None,  # BYOK 自定义 base
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False,
        fallback_providers: Optional[List[str]] = None,
        **kwargs,
    ) -> LLMResponse:
        """
        统一 completion 调用
        
        BYOK 模式:用户传入 api_key_override,完全不使用服务器 Key
        """
        target_provider = provider or self.default_provider
        attempt_chain = [target_provider] + (fallback_providers or [])

        last_error = None
        for prov_name in attempt_chain:
            cfg = self.get_provider(prov_name)
            if cfg is None:
                continue

            api_key = api_key_override or cfg.api_key
            if not api_key and not cfg.is_local:
                logger.debug(f"Skip {prov_name}: no API key")
                continue

            try:
                return await self._do_complete(
                    cfg=cfg,
                    api_key=api_key,
                    api_base=api_base_override or cfg.api_base,
                    model=model or cfg.default_model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=stream,
                    **kwargs,
                )
            except Exception as e:
                logger.warning(f"Provider {prov_name} failed: {e}")
                last_error = e
                continue

        raise RuntimeError(f"All LLM providers failed. Last error: {last_error}")

    async def _do_complete(
        self,
        cfg: ProviderConfig,
        api_key: str,
        api_base: str,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        stream: bool,
        **kwargs,
    ) -> LLMResponse:
        """实际执行 completion"""
        start = time.time()

        if self.litellm_available:
            import litellm

            # LiteLLM 模型名约定
            litellm_model = self._format_litellm_model(cfg.name, model)

            response = await litellm.acompletion(
                model=litellm_model,
                messages=messages,
                api_key=api_key,
                api_base=api_base,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream,
                **kwargs,
            )

            latency_ms = int((time.time() - start) * 1000)

            content = response.choices[0].message.content if not stream else ""
            usage = getattr(response, "usage", None)

            return LLMResponse(
                content=content or "",
                model=model,
                provider=cfg.name,
                prompt_tokens=getattr(usage, "prompt_tokens", 0) if usage else 0,
                completion_tokens=getattr(usage, "completion_tokens", 0) if usage else 0,
                total_tokens=getattr(usage, "total_tokens", 0) if usage else 0,
                latency_ms=latency_ms,
                raw=response.model_dump() if hasattr(response, "model_dump") else None,
            )
        else:
            # Fallback: 直接 HTTP 调用 OpenAI 兼容接口
            return await self._http_complete_openai_compat(
                cfg, api_key, api_base, model, messages, temperature, max_tokens, **kwargs
            )

    @staticmethod
    def _format_litellm_model(provider: str, model: str) -> str:
        """LiteLLM 模型名前缀约定"""
        if provider == "openai":
            return model
        elif provider == "anthropic":
            return model if model.startswith("anthropic/") else f"anthropic/{model}"
        elif provider == "deepseek":
            return f"deepseek/{model}"
        elif provider in ("ollama", "lmstudio"):
            return f"openai/{model}"  # OpenAI compat
        else:
            # 国内 OpenAI 兼容供应商,使用 openai/ 前缀
            return f"openai/{model}"

    async def _http_complete_openai_compat(
        self,
        cfg: ProviderConfig,
        api_key: str,
        api_base: str,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        **kwargs,
    ) -> LLMResponse:
        """直接 HTTP 调用 OpenAI 兼容接口(兜底方案)"""
        import httpx

        start = time.time()

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{api_base.rstrip('/')}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    **kwargs,
                },
            )
            response.raise_for_status()
            data = response.json()

        latency_ms = int((time.time() - start) * 1000)

        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})

        return LLMResponse(
            content=content,
            model=model,
            provider=cfg.name,
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
            latency_ms=latency_ms,
            raw=data,
        )


# ============================================================
# 单例 Router
# ============================================================

_router: Optional[LLMRouter] = None


def get_router() -> LLMRouter:
    global _router
    if _router is None:
        _router = LLMRouter()
    return _router


# ============================================================
# 简化使用接口
# ============================================================


async def chat(
    messages: List[Dict[str, str]],
    provider: str = "minimax",
    model: Optional[str] = None,
    **kwargs,
) -> str:
    """便捷接口:返回 content 字符串"""
    router = get_router()
    response = await router.complete(
        messages=messages,
        provider=provider,
        model=model,
        fallback_providers=["hunyuan", "deepseek"] if provider == "minimax" else None,
        **kwargs,
    )
    return response.content


async def chat_with_response(
    messages: List[Dict[str, str]],
    provider: str = "minimax",
    model: Optional[str] = None,
    **kwargs,
) -> LLMResponse:
    """便捷接口:返回完整 LLMResponse"""
    router = get_router()
    return await router.complete(
        messages=messages,
        provider=provider,
        model=model,
        fallback_providers=["hunyuan", "deepseek"] if provider == "minimax" else None,
        **kwargs,
    )
