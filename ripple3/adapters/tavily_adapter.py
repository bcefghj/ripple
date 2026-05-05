"""Tavily search adapter — high-quality AI-optimized search results.

Falls back gracefully if no API key is configured.
Env: TAVILY_API_KEY
"""

from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass

import httpx

log = logging.getLogger(__name__)

_API_URL = "https://api.tavily.com/search"
_TIMEOUT = httpx.Timeout(connect=5, read=15, write=5, pool=5)


@dataclass
class TavilyResult:
    title: str
    url: str
    snippet: str
    score: float = 0.0


async def search_tavily(
    query: str,
    *,
    max_results: int = 20,
    search_depth: str = "advanced",
    include_domains: list[str] | None = None,
    days: int = 30,
) -> list[TavilyResult]:
    """Search via Tavily API. Returns empty list if no key or on error."""
    from core.config import get_settings
    api_key = get_settings().tavily_api_key
    if not api_key:
        return []

    payload = {
        "api_key": api_key,
        "query": query,
        "max_results": min(max_results, 20),
        "search_depth": search_depth,
        "days": days,
    }
    if include_domains:
        payload["include_domains"] = include_domains

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(_API_URL, json=payload)
            resp.raise_for_status()
            data = resp.json()

        results = []
        for item in data.get("results", []):
            results.append(TavilyResult(
                title=item.get("title", ""),
                url=item.get("url", ""),
                snippet=item.get("content", ""),
                score=item.get("score", 0.0),
            ))
        return results

    except Exception as exc:
        log.warning("Tavily search failed for '%s': %s", query[:50], exc)
        return []


async def search_tavily_multi(
    queries: list[str],
    *,
    max_per_query: int = 5,
) -> list[TavilyResult]:
    """Run multiple Tavily searches in parallel and deduplicate."""
    from core.config import get_settings
    if not get_settings().tavily_api_key:
        return []

    results: list[TavilyResult] = []
    seen_urls: set[str] = set()

    async def _search(q: str):
        items = await search_tavily(q, max_results=max_per_query)
        for item in items:
            if item.url not in seen_urls:
                seen_urls.add(item.url)
                results.append(item)

    async with asyncio.TaskGroup() as tg:
        for q in queries:
            tg.create_task(_search(q))

    results.sort(key=lambda r: r.score, reverse=True)
    return results
