"""Baidu search adapter — free, no API key required.

Uses the baidusearch library (pip install baidusearch).
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

log = logging.getLogger(__name__)


@dataclass
class BaiduResult:
    title: str
    url: str
    snippet: str


def _baidu_search_sync(query: str, num_results: int = 20) -> list[BaiduResult]:
    try:
        from baidusearch.baidusearch import search
        raw = search(query, num_results=num_results)
        return [
            BaiduResult(
                title=r.get("title", ""),
                url=r.get("url", ""),
                snippet=r.get("abstract", ""),
            )
            for r in raw
            if isinstance(r, dict) and r.get("url")
        ]
    except Exception as exc:
        log.warning("Baidu search '%s' failed: %s", query[:50], exc)
        return []


async def baidu_search(query: str, num_results: int = 20) -> list[BaiduResult]:
    return await asyncio.to_thread(_baidu_search_sync, query, num_results)


async def baidu_search_multi(
    queries: list[str],
    *,
    max_per_query: int = 20,
) -> list[BaiduResult]:
    results: list[BaiduResult] = []
    seen: set[str] = set()

    for q in queries:
        try:
            items = await asyncio.wait_for(
                baidu_search(q, num_results=max_per_query),
                timeout=15,
            )
            for item in items:
                if item.url not in seen:
                    seen.add(item.url)
                    results.append(item)
        except asyncio.TimeoutError:
            log.warning("Baidu search timed out for '%s'", q[:50])
        except Exception as exc:
            log.warning("Baidu search error for '%s': %s", q[:50], exc)

    return results
