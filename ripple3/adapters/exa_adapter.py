"""Exa semantic search adapter — AI-native neural search.

Supports keyword, neural, and auto search modes with content extraction.
Env: EXA_API_KEY
"""

from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass

import httpx

log = logging.getLogger(__name__)

_API_URL = "https://api.exa.ai"
_TIMEOUT = httpx.Timeout(connect=5, read=30, write=5, pool=5)


@dataclass
class ExaResult:
    title: str
    url: str
    snippet: str
    score: float = 0.0
    published_date: str = ""
    highlights: list[str] | None = None


async def search_exa(
    query: str,
    *,
    num_results: int = 10,
    search_type: str = "auto",
    use_autoprompt: bool = True,
    include_text: bool = True,
    start_published_date: str = "",
) -> list[ExaResult]:
    """Search via Exa API. Returns empty list if no key or on error."""
    from core.config import get_settings
    api_key = get_settings().exa_api_key
    if not api_key:
        return []

    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json",
    }

    payload: dict = {
        "query": query,
        "numResults": min(num_results, 30),
        "type": search_type,
        "useAutoprompt": use_autoprompt,
        "contents": {},
    }

    if include_text:
        payload["contents"]["text"] = {"maxCharacters": 500}
        payload["contents"]["highlights"] = {"numSentences": 3}

    if start_published_date:
        payload["startPublishedDate"] = start_published_date

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(
                f"{_API_URL}/search",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

        results: list[ExaResult] = []
        for item in data.get("results", []):
            text = item.get("text", "")
            highlights = item.get("highlights", [])
            snippet = highlights[0] if highlights else text[:300]

            results.append(ExaResult(
                title=item.get("title", ""),
                url=item.get("url", ""),
                snippet=snippet,
                score=item.get("score", 0.0),
                published_date=item.get("publishedDate", ""),
                highlights=highlights or None,
            ))
        return results

    except Exception as exc:
        log.warning("Exa search failed for '%s': %s", query[:50], exc)
        return []


async def search_exa_multi(
    queries: list[str],
    *,
    num_per_query: int = 10,
    start_published_date: str = "",
) -> list[ExaResult]:
    """Run multiple Exa searches in parallel and deduplicate."""
    from core.config import get_settings
    if not get_settings().exa_api_key:
        return []

    results: list[ExaResult] = []
    seen_urls: set[str] = set()
    lock = asyncio.Lock()

    async def _search(q: str):
        items = await search_exa(
            q,
            num_results=num_per_query,
            start_published_date=start_published_date,
        )
        async with lock:
            for item in items:
                if item.url not in seen_urls:
                    seen_urls.add(item.url)
                    results.append(item)

    await asyncio.gather(*[_search(q) for q in queries], return_exceptions=True)
    results.sort(key=lambda r: r.score, reverse=True)
    return results
