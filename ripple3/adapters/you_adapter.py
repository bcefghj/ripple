"""You.com Search API adapter.

Free tier: $100 free credits.
Env: YOU_API_KEY
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

import httpx

log = logging.getLogger(__name__)

_API_URL = "https://api.ydc-index.io/search"
_TIMEOUT = httpx.Timeout(connect=5, read=15, write=5, pool=5)


@dataclass
class YouResult:
    title: str
    url: str
    snippet: str


async def search_you(
    query: str,
    *,
    num_web_results: int = 20,
    country: str = "CN",
    search_lang: str = "zh-hans",
) -> list[YouResult]:
    from core.config import get_settings
    api_key = get_settings().you_api_key
    if not api_key:
        return []

    headers = {"X-API-Key": api_key}
    params = {
        "query": query,
        "num_web_results": min(num_web_results, 20),
        "country": country,
        "search_lang": search_lang,
    }

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(_API_URL, headers=headers, params=params)
            resp.raise_for_status()
            data = resp.json()

        results = []
        for hit in data.get("hits", []):
            results.append(YouResult(
                title=hit.get("title", ""),
                url=hit.get("url", ""),
                snippet="\n".join(hit.get("snippets", []))[:300],
            ))
        return results
    except Exception as exc:
        log.warning("You.com search failed for '%s': %s", query[:50], exc)
        return []


async def search_you_multi(
    queries: list[str],
    *,
    max_per_query: int = 20,
) -> list[YouResult]:
    from core.config import get_settings
    if not get_settings().you_api_key:
        return []

    results: list[YouResult] = []
    seen: set[str] = set()
    lock = asyncio.Lock()

    async def _search(q: str):
        items = await search_you(q, num_web_results=max_per_query)
        async with lock:
            for item in items:
                if item.url not in seen:
                    seen.add(item.url)
                    results.append(item)

    await asyncio.gather(*[_search(q) for q in queries], return_exceptions=True)
    return results
