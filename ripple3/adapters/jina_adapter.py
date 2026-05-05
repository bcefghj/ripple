"""Jina AI search + reader adapter.

Search: GET https://s.jina.ai/<query> — web search returning clean text
Reader: GET https://r.jina.ai/<url> — convert any URL to LLM-friendly markdown
Free: 10M tokens/month.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

import httpx

log = logging.getLogger(__name__)

_TIMEOUT = httpx.Timeout(connect=5, read=20, write=5, pool=5)


@dataclass
class JinaSearchResult:
    title: str
    url: str
    snippet: str


async def jina_search(query: str, *, max_results: int = 10) -> list[JinaSearchResult]:
    """Search via Jina s.jina.ai."""
    from core.config import get_settings
    api_key = get_settings().jina_api_key

    headers: dict[str, str] = {
        "Accept": "application/json",
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(
                f"https://s.jina.ai/{query}",
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()

        results = []
        items = data if isinstance(data, list) else data.get("data", data.get("results", []))
        for item in items[:max_results]:
            if isinstance(item, dict):
                results.append(JinaSearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("description", item.get("content", ""))[:300],
                ))
        return results
    except Exception as exc:
        log.warning("Jina search failed for '%s': %s", query[:50], exc)
        return []


async def jina_read(url: str) -> str:
    """Read a URL via Jina r.jina.ai, returning clean markdown."""
    from core.config import get_settings
    api_key = get_settings().jina_api_key

    headers: dict[str, str] = {"Accept": "text/plain"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(
                f"https://r.jina.ai/{url}",
                headers=headers,
            )
            resp.raise_for_status()
            return resp.text[:5000]
    except Exception as exc:
        log.warning("Jina read failed for '%s': %s", url[:80], exc)
        return ""


async def jina_search_multi(
    queries: list[str],
    *,
    max_per_query: int = 10,
) -> list[JinaSearchResult]:
    results: list[JinaSearchResult] = []
    seen: set[str] = set()

    for q in queries[:3]:
        items = await jina_search(q, max_results=max_per_query)
        for item in items:
            if item.url not in seen:
                seen.add(item.url)
                results.append(item)

    return results
