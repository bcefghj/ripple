"""Serper (Google Search) adapter — high-quality Google SERP results.

Supports up to 100 results per query, news search, and time-range filtering.
Env: SERPER_API_KEY
"""

from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass

import httpx

log = logging.getLogger(__name__)

_API_URL = "https://google.serper.dev"
_TIMEOUT = httpx.Timeout(connect=5, read=20, write=5, pool=5)


@dataclass
class SerperResult:
    title: str
    url: str
    snippet: str
    date: str = ""
    position: int = 0


async def search_serper(
    query: str,
    *,
    num: int = 20,
    gl: str = "cn",
    hl: str = "zh-cn",
    tbs: str = "",
    search_type: str = "search",
) -> list[SerperResult]:
    """Search via Serper API. Returns empty list if no key or on error."""
    from core.config import get_settings
    api_key = get_settings().serper_api_key
    if not api_key:
        return []

    endpoint = f"{_API_URL}/{search_type}"
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json",
    }
    payload: dict = {
        "q": query,
        "num": min(num, 100),
        "gl": gl,
        "hl": hl,
    }
    if tbs:
        payload["tbs"] = tbs

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(endpoint, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        results: list[SerperResult] = []
        for item in data.get("organic", []):
            results.append(SerperResult(
                title=item.get("title", ""),
                url=item.get("link", ""),
                snippet=item.get("snippet", ""),
                date=item.get("date", ""),
                position=item.get("position", 0),
            ))
        return results

    except Exception as exc:
        log.warning("Serper search failed for '%s': %s", query[:50], exc)
        return []


async def search_serper_news(
    query: str,
    *,
    num: int = 20,
    gl: str = "cn",
    hl: str = "zh-cn",
    tbs: str = "",
) -> list[SerperResult]:
    """Search Google News via Serper."""
    from core.config import get_settings
    api_key = get_settings().serper_api_key
    if not api_key:
        return []

    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json",
    }
    payload: dict = {
        "q": query,
        "num": min(num, 100),
        "gl": gl,
        "hl": hl,
    }
    if tbs:
        payload["tbs"] = tbs

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(f"{_API_URL}/news", headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        results: list[SerperResult] = []
        for item in data.get("news", []):
            results.append(SerperResult(
                title=item.get("title", ""),
                url=item.get("link", ""),
                snippet=item.get("snippet", ""),
                date=item.get("date", ""),
            ))
        return results

    except Exception as exc:
        log.warning("Serper news search failed for '%s': %s", query[:50], exc)
        return []


async def search_serper_multi(
    queries: list[str],
    *,
    num_per_query: int = 20,
    tbs: str = "",
) -> list[SerperResult]:
    """Run multiple Serper searches in parallel and deduplicate."""
    from core.config import get_settings
    if not get_settings().serper_api_key:
        return []

    results: list[SerperResult] = []
    seen_urls: set[str] = set()
    lock = asyncio.Lock()

    async def _search(q: str):
        items = await search_serper(q, num=num_per_query, tbs=tbs)
        async with lock:
            for item in items:
                if item.url not in seen_urls:
                    seen_urls.add(item.url)
                    results.append(item)

    await asyncio.gather(*[_search(q) for q in queries], return_exceptions=True)
    return results
