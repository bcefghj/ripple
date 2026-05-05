"""MiniMax Token Plan web search adapter.

Uses the MiniMax Coding Plan search endpoint (``/v1/coding_plan/search``)
which is included free with every Token Plan subscription (450 calls/day).

Fallback: if the direct search endpoint fails, use MiniMax chat completions
with a web-search system prompt to extract structured results.
"""

from __future__ import annotations

import asyncio
import json
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
    """Perform a web search using MiniMax Coding Plan search API."""
    from core.config import get_settings
    s = get_settings()
    if not s.minimax_api_key:
        return []

    host = s.minimax_search_host or "https://api.minimaxi.com"
    url = f"{host.rstrip('/')}/v1/coding_plan/search"
    headers = {
        "Authorization": f"Bearer {s.minimax_api_key}",
        "Content-Type": "application/json",
        "MM-API-Source": "Minimax-MCP",
    }
    payload = {"q": query, "count": min(count, 30)}

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        results: list[MiniMaxSearchResult] = []
        items = (
            data.get("organic")
            or data.get("results")
            or data.get("organic_results")
            or data.get("web", {}).get("results")
            or []
        )
        for item in items:
            title = item.get("title", "")
            link = item.get("url") or item.get("link") or ""
            snippet = item.get("snippet") or item.get("description") or item.get("content", "")
            if link:
                results.append(MiniMaxSearchResult(title=title, url=link, snippet=snippet))

        log.info("MiniMax search OK: query='%s' → %d results", query[:40], len(results))
        return results
    except httpx.HTTPStatusError as exc:
        log.warning("MiniMax search HTTP %s for '%s', trying fallback", exc.response.status_code, query[:40])
        return await _fallback_chat_search(query, s)
    except Exception as exc:
        log.warning("MiniMax search error for '%s': %s, trying fallback", query[:40], exc)
        return await _fallback_chat_search(query, s)


async def _fallback_chat_search(query: str, settings) -> list[MiniMaxSearchResult]:
    """Fallback: ask MiniMax LLM to search and return structured results."""
    headers = {
        "Authorization": f"Bearer {settings.minimax_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.minimax_text_model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "你是搜索助手。请针对用户的查询进行联网搜索，"
                    "然后以 JSON 数组返回 10-20 条搜索结果。"
                    "每条格式: {\"title\": \"...\", \"url\": \"...\", \"snippet\": \"...\"}\n"
                    "只输出 JSON 数组，不要其他文字。"
                ),
            },
            {"role": "user", "content": query},
        ],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "web_search",
                    "description": "Search the web for real-time information",
                    "parameters": {
                        "type": "object",
                        "properties": {"query": {"type": "string"}},
                        "required": ["query"],
                    },
                },
            }
        ],
        "temperature": 0.1,
        "max_tokens": 4096,
    }

    try:
        url = f"{settings.minimax_api_base.rstrip('/')}/chat/completions"
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        content = data["choices"][0]["message"].get("content", "")
        results = _parse_json_results(content)
        log.info("MiniMax fallback search: query='%s' → %d results", query[:40], len(results))
        return results
    except Exception as exc:
        log.warning("MiniMax fallback chat search failed: %s", exc)
        return []


def _parse_json_results(text: str) -> list[MiniMaxSearchResult]:
    """Parse JSON array from LLM output."""
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
    """Run multiple MiniMax searches concurrently with deduplication."""
    from core.config import get_settings
    if not get_settings().minimax_api_key:
        return []

    async def _search_one(q: str) -> list[MiniMaxSearchResult]:
        try:
            return await minimax_web_search(q, count=max_per_query)
        except Exception as exc:
            log.warning("MiniMax multi-search failed for '%s': %s", q[:40], exc)
            return []

    batch = queries[:10]
    all_items = await asyncio.gather(*[_search_one(q) for q in batch])

    results: list[MiniMaxSearchResult] = []
    seen: set[str] = set()
    for items in all_items:
        for item in items:
            if item.url and item.url not in seen:
                seen.add(item.url)
                results.append(item)

    log.info("MiniMax multi-search: %d queries → %d unique results", len(batch), len(results))
    return results
