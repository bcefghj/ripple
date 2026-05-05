"""SearXNG metasearch engine adapter.

Aggregates results from 70+ search engines via a single query.
Supports self-hosted or public instances.
No API key required.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

import httpx

log = logging.getLogger(__name__)

_TIMEOUT = httpx.Timeout(connect=5, read=20, write=5, pool=5)

PUBLIC_INSTANCES = [
    "https://search.sapti.me",
    "https://searx.tiekoetter.com",
    "https://search.bus-hit.me",
]


@dataclass
class SearXNGResult:
    title: str
    url: str
    snippet: str
    engine: str = ""


async def searxng_search(
    query: str,
    *,
    instance_url: str = "",
    num_results: int = 30,
    language: str = "zh",
    categories: str = "general",
) -> list[SearXNGResult]:
    from core.config import get_settings
    url = instance_url or get_settings().searxng_url
    if not url:
        for inst in PUBLIC_INSTANCES:
            results = await _try_instance(inst, query, language, categories)
            if results:
                return results[:num_results]
        return []

    return await _try_instance(url, query, language, categories)


async def _try_instance(
    base_url: str,
    query: str,
    language: str,
    categories: str,
) -> list[SearXNGResult]:
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(
                f"{base_url.rstrip('/')}/search",
                params={
                    "q": query,
                    "format": "json",
                    "language": language,
                    "categories": categories,
                },
            )
            resp.raise_for_status()
            data = resp.json()

        return [
            SearXNGResult(
                title=r.get("title", ""),
                url=r.get("url", ""),
                snippet=r.get("content", ""),
                engine=", ".join(r.get("engines", [])),
            )
            for r in data.get("results", [])
            if r.get("url")
        ]
    except Exception as exc:
        log.warning("SearXNG instance %s failed: %s", base_url, exc)
        return []


async def searxng_search_multi(
    queries: list[str],
    *,
    max_per_query: int = 30,
) -> list[SearXNGResult]:
    results: list[SearXNGResult] = []
    seen: set[str] = set()

    for q in queries[:6]:
        items = await searxng_search(q, num_results=max_per_query)
        for item in items:
            if item.url not in seen:
                seen.add(item.url)
                results.append(item)

    return results
