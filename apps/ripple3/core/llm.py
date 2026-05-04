"""Unified LLM gateway — MiMo primary, MiniMax fallback.

Both providers expose an OpenAI-compatible /chat/completions endpoint,
so we use the same httpx logic for both.

Supports:
  - chat()        — standard one-shot completion
  - chat_stream()  — async generator yielding partial content (SSE)
  - chat_deep()   — high-token, low-temperature deep analysis
  - chat_json()   — one-shot with JSON extraction
"""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any

import httpx

from core.config import get_settings

log = logging.getLogger(__name__)

_TIMEOUT = httpx.Timeout(connect=10, read=180, write=10, pool=10)
_STREAM_TIMEOUT = httpx.Timeout(connect=10, read=300, write=10, pool=10)


@dataclass
class LLMResponse:
    content: str
    model: str
    usage: dict[str, int] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)


def _build_providers(provider: str) -> list[tuple[str, str, str]]:
    """Return ordered list of (base_url, api_key, model) tuples."""
    s = get_settings()
    providers: list[tuple[str, str, str]] = []
    if provider in ("auto", "minimax"):
        providers.append((s.minimax_api_base, s.minimax_api_key, s.minimax_text_model))
    if provider in ("auto", "xiaomi"):
        providers.append((s.xiaomi_api_base, s.xiaomi_api_key, s.xiaomi_model))
    return providers


# ── one-shot completion ─────────────────────────────────────────────────────

async def _call_openai_compat(
    base_url: str,
    api_key: str,
    model: str,
    messages: list[dict[str, str]],
    temperature: float = 0.7,
    max_tokens: int = 4096,
    response_format: dict | None = None,
) -> LLMResponse:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if response_format:
        payload["response_format"] = response_format

    url = f"{base_url.rstrip('/')}/chat/completions"
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()

    choice = data["choices"][0]
    return LLMResponse(
        content=choice["message"]["content"],
        model=data.get("model", model),
        usage=data.get("usage", {}),
        raw=data,
    )


async def chat(
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.7,
    max_tokens: int = 4096,
    response_format: dict | None = None,
    provider: str = "auto",
) -> LLMResponse:
    """Send a chat completion request. Tries MiniMax first, falls back to MiMo."""
    providers = _build_providers(provider)

    last_err: Exception | None = None
    for base, key, model in providers:
        if not key:
            continue
        try:
            return await _call_openai_compat(
                base, key, model, messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format=response_format,
            )
        except Exception as exc:
            log.warning("LLM call failed (%s): %s", model, exc)
            last_err = exc

    raise RuntimeError(f"All LLM providers failed. Last error: {last_err}")


# ── streaming completion ────────────────────────────────────────────────────

async def _stream_openai_compat(
    base_url: str,
    api_key: str,
    model: str,
    messages: list[dict[str, str]],
    temperature: float = 0.7,
    max_tokens: int = 4096,
) -> AsyncIterator[str]:
    """Yield content deltas from an SSE stream."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": True,
    }

    url = f"{base_url.rstrip('/')}/chat/completions"
    async with httpx.AsyncClient(timeout=_STREAM_TIMEOUT) as client:
        async with client.stream("POST", url, headers=headers, json=payload) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                line = line.strip()
                if not line or not line.startswith("data:"):
                    continue
                data_str = line[len("data:"):].strip()
                if data_str == "[DONE]":
                    break
                try:
                    chunk = json.loads(data_str)
                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        yield content
                except (json.JSONDecodeError, IndexError, KeyError):
                    continue


async def chat_stream(
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.7,
    max_tokens: int = 4096,
    provider: str = "auto",
) -> AsyncIterator[str]:
    """Streaming chat — yields partial content strings as they arrive.

    Usage::

        async for chunk in chat_stream(messages):
            print(chunk, end="", flush=True)
    """
    providers = _build_providers(provider)

    last_err: Exception | None = None
    for base, key, model in providers:
        if not key:
            continue
        try:
            async for chunk in _stream_openai_compat(
                base, key, model, messages,
                temperature=temperature,
                max_tokens=max_tokens,
            ):
                yield chunk
            return
        except Exception as exc:
            log.warning("Stream call failed (%s): %s", model, exc)
            last_err = exc

    raise RuntimeError(f"All LLM providers failed (stream). Last error: {last_err}")


async def chat_stream_full(
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.7,
    max_tokens: int = 4096,
    provider: str = "auto",
) -> tuple[str, AsyncIterator[str]]:
    """Like chat_stream but also accumulates and returns the full text.

    Returns an async iterator that yields chunks; after exhausting it call
    ``collected`` on the wrapper to get the full string.
    """
    collected: list[str] = []

    async def _wrapper() -> AsyncIterator[str]:
        async for chunk in chat_stream(
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
            provider=provider,
        ):
            collected.append(chunk)
            yield chunk

    return collected, _wrapper()


# ── deep analysis mode ──────────────────────────────────────────────────────

async def chat_deep(
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.2,
    max_tokens: int = 8192,
    provider: str = "auto",
) -> LLMResponse:
    """Deep analysis: low temperature, high token budget, prefer MiniMax-M2.7."""
    return await chat(
        messages,
        temperature=temperature,
        max_tokens=max_tokens,
        provider=provider if provider != "auto" else "minimax",
    )


async def chat_deep_stream(
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.2,
    max_tokens: int = 8192,
    provider: str = "auto",
) -> AsyncIterator[str]:
    """Deep analysis with streaming output."""
    async for chunk in chat_stream(
        messages,
        temperature=temperature,
        max_tokens=max_tokens,
        provider=provider if provider != "auto" else "minimax",
    ):
        yield chunk


# ── JSON extraction ─────────────────────────────────────────────────────────

async def chat_json(
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.4,
    max_tokens: int = 4096,
    provider: str = "auto",
) -> dict:
    """Chat and parse the response as JSON (with lenient extraction)."""
    resp = await chat(
        messages,
        temperature=temperature,
        max_tokens=max_tokens,
        provider=provider,
    )
    return _extract_json(resp.content)


async def chat_deep_json(
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.2,
    max_tokens: int = 8192,
    provider: str = "auto",
) -> dict:
    """Deep analysis returning parsed JSON."""
    resp = await chat_deep(
        messages,
        temperature=temperature,
        max_tokens=max_tokens,
        provider=provider,
    )
    return _extract_json(resp.content)


def _extract_json(text: str) -> dict:
    """Best-effort JSON extraction from LLM output."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end > start:
            return json.loads(text[start:end])
        start = text.find("[")
        end = text.rfind("]") + 1
        if start != -1 and end > start:
            return json.loads(text[start:end])
        raise
