"""Google search adapter — free, no API key required.

Uses the googlesearch-python library (pip install googlesearch-python).
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

log = logging.getLogger(__name__)


@dataclass
class GoogleResult:
    title: str
    url: str
    snippet: str


def _google_search_sync(query: str, num_results: int = 20) -> list[GoogleResult]:
    try:
        from googlesearch import search
        results = []
        for url in search(query, num_results=num_results, lang="zh-CN"):
            results.append(GoogleResult(title="", url=url, snippet=""))
        return results
    except Exception as exc:
        log.warning("Google search '%s' failed: %s", query[:50], exc)
        return []


async def google_search(query: str, num_results: int = 20) -> list[GoogleResult]:
    return await asyncio.to_thread(_google_search_sync, query, num_results)


async def google_search_multi(
    queries: list[str],
    *,
    max_per_query: int = 20,
) -> list[GoogleResult]:
    results: list[GoogleResult] = []
    seen: set[str] = set()

    for q in queries[:6]:
        try:
            items = await asyncio.wait_for(
                google_search(q, num_results=max_per_query),
                timeout=20,
            )
            for item in items:
                if item.url not in seen:
                    seen.add(item.url)
                    results.append(item)
        except asyncio.TimeoutError:
            log.warning("Google search timed out for '%s'", q[:50])
        except Exception as exc:
            log.warning("Google search error for '%s': %s", q[:50], exc)

    return results
