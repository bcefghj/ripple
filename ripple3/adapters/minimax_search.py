"""MiniMax Token Plan web search adapter.

Leverages the MiniMax Coding Plan's built-in web_search capability
via direct HTTP API call. Each Token Plan subscription includes 450
search calls per day at no extra cost.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import httpx

log = logging.getLogger(__name__)

_TIMEOUT = httpx.Timeout(connect=10, read=30, write=10, pool=10)


@dataclass
class MiniMaxSearchResult:
    title: str
    url: str
    snippet: str


async def minimax_web_search(query: str, count: int = 20) -> list[MiniMaxSearchResult]:
    """Perform a web search using MiniMax Token Plan's built-in search API."""
    from core.config import get_settings
    s = get_settings()
    if not s.minimax_api_key:
        return []

    host = s.minimax_search_host or "https://api.minimaxi.com"
    url = f"{host.rstrip('/')}/v1/web_search"
    headers = {
        "Authorization": f"Bearer {s.minimax_api_key}",
        "Content-Type": "application/json",
    }
    payload = {"query": query, "count": min(count, 30)}

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        results: list[MiniMaxSearchResult] = []
        for item in data.get("results", data.get("organic_results", [])):
            results.append(MiniMaxSearchResult(
                title=item.get("title", ""),
                url=item.get("url", item.get("link", "")),
                snippet=item.get("snippet", item.get("description", "")),
            ))
        return results
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            return await _fallback_chat_search(query, s)
        log.warning("MiniMax web_search failed for '%s': %s", query[:50], exc)
        return []
    except Exception as exc:
        log.warning("MiniMax web_search failed for '%s': %s", query[:50], exc)
        return await _fallback_chat_search(query, s)


async def _fallback_chat_search(query: str, settings) -> list[MiniMaxSearchResult]:
    """Fallback: use MiniMax chat with web search tool call if direct endpoint unavailable."""
    import json

    headers = {
        "Authorization": f"Bearer {settings.minimax_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.minimax_text_model,
        "messages": [
            {"role": "system", "content": "你是搜索助手。搜索并以JSON数组返回结果，每条含title/url/snippet。只输出JSON。"},
            {"role": "user", "content": query},
        ],
        "tools": [{"type": "web_search", "web_search": {"enable": True}}],
        "temperature": 0.1,
        "max_tokens": 4096,
    }

    try:
        url = f"{settings.minimax_api_base.rstrip('/')}/chat/completions"
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        content = data["choices"][0]["message"]["content"]
        return _parse_json_results(content)
    except Exception as exc:
        log.warning("MiniMax fallback chat search failed: %s", exc)
        return []


def _parse_json_results(text: str) -> list[MiniMaxSearchResult]:
    """Parse JSON array from LLM output."""
    import json
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()

    try:
        start = text.find("[")
        end = text.rfind("]") + 1
        if start >= 0 and end > start:
            items = json.loads(text[start:end])
            return [
                MiniMaxSearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("snippet", ""),
                )
                for item in items
                if isinstance(item, dict) and item.get("url")
            ]
    except (json.JSONDecodeError, ValueError):
        pass
    return []


async def minimax_search_multi(queries: list[str], max_per_query: int = 20) -> list[MiniMaxSearchResult]:
    """Run multiple MiniMax searches with deduplication."""
    from core.config import get_settings
    if not get_settings().minimax_api_key:
        return []

    results: list[MiniMaxSearchResult] = []
    seen: set[str] = set()

    for q in queries[:8]:
        items = await minimax_web_search(q, count=max_per_query)
        for item in items:
            if item.url and item.url not in seen:
                seen.add(item.url)
                results.append(item)

    log.info("MiniMax search: %d queries → %d results", min(len(queries), 8), len(results))
    return results
