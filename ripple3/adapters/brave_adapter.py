"""Brave Search API adapter.

Free tier: ~1,000 searches/month ($5 free credit).
Env: BRAVE_API_KEY
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

import httpx

log = logging.getLogger(__name__)

_API_URL = "https://api.search.brave.com/res/v1/web/search"
_TIMEOUT = httpx.Timeout(connect=5, read=15, write=5, pool=5)


@dataclass
class BraveResult:
    title: str
    url: str
    snippet: str


async def search_brave(
    query: str,
    *,
    count: int = 20,
    search_lang: str = "zh-hans",
    country: str = "cn",
) -> list[BraveResult]:
    from core.config import get_settings
    api_key = get_settings().brave_api_key
    if not api_key:
        return []

    headers = {
        "X-Subscription-Token": api_key,
        "Accept": "application/json",
    }
    params = {
        "q": query,
        "count": min(count, 20),
        "search_lang": search_lang,
        "country": country,
    }

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(_API_URL, headers=headers, params=params)
            resp.raise_for_status()
            data = resp.json()

        results = []
        for item in data.get("web", {}).get("results", []):
            results.append(BraveResult(
                title=item.get("title", ""),
                url=item.get("url", ""),
                snippet=item.get("description", ""),
            ))
        return results
    except Exception as exc:
        log.warning("Brave search failed for '%s': %s", query[:50], exc)
        return []


async def search_brave_multi(
    queries: list[str],
    *,
    max_per_query: int = 20,
) -> list[BraveResult]:
    from core.config import get_settings
    if not get_settings().brave_api_key:
        return []

    results: list[BraveResult] = []
    seen: set[str] = set()
    lock = asyncio.Lock()

    async def _search(q: str):
        items = await search_brave(q, count=max_per_query)
        async with lock:
            for item in items:
                if item.url not in seen:
                    seen.add(item.url)
                    results.append(item)

    await asyncio.gather(*[_search(q) for q in queries], return_exceptions=True)
    return results
