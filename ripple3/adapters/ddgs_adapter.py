"""DuckDuckGo search adapter — free, no API key required.

Extracted from the original search.py as a standalone adapter.
Uses the ddgs library for text and news search.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from duckduckgo_search import DDGS

log = logging.getLogger(__name__)


@dataclass
class DDGSResult:
    title: str
    url: str
    snippet: str
    source: str = ""


@dataclass
class DDGSNewsResult:
    title: str
    url: str
    snippet: str
    date: str = ""
    source: str = ""


def ddgs_text_search(
    query: str,
    *,
    max_results: int = 10,
    region: str = "cn-zh",
    timelimit: str | None = None,
) -> list[DDGSResult]:
    """Synchronous DuckDuckGo text search."""
    results: list[DDGSResult] = []
    try:
        with DDGS() as ddgs:
            kwargs: dict = {"max_results": max_results, "region": region}
            if timelimit:
                kwargs["timelimit"] = timelimit
            for r in ddgs.text(query, **kwargs):
                results.append(DDGSResult(
                    title=r.get("title", ""),
                    url=r.get("href", ""),
                    snippet=r.get("body", ""),
                ))
    except Exception as exc:
        log.warning("DDGS text search '%s' failed: %s", query[:50], exc)
    return results


def ddgs_news_search(
    query: str,
    *,
    max_results: int = 10,
    region: str = "cn-zh",
    timelimit: str | None = None,
) -> list[DDGSNewsResult]:
    """Synchronous DuckDuckGo news search."""
    results: list[DDGSNewsResult] = []
    try:
        with DDGS() as ddgs:
            kwargs: dict = {"max_results": max_results, "region": region}
            if timelimit:
                kwargs["timelimit"] = timelimit
            for r in ddgs.news(query, **kwargs):
                results.append(DDGSNewsResult(
                    title=r.get("title", ""),
                    url=r.get("url", ""),
                    snippet=r.get("body", ""),
                    date=r.get("date", ""),
                    source=r.get("source", ""),
                ))
    except Exception as exc:
        log.warning("DDGS news search '%s' failed: %s", query[:50], exc)
    return results


def ddgs_multi_text(
    queries: list[str],
    *,
    max_per_query: int = 10,
    region: str = "cn-zh",
    timelimit: str | None = None,
) -> list[DDGSResult]:
    """Run multiple DDGS text queries sequentially and deduplicate."""
    results: list[DDGSResult] = []
    seen_urls: set[str] = set()

    with DDGS() as ddgs:
        for q in queries:
            try:
                kwargs: dict = {"max_results": max_per_query, "region": region}
                if timelimit:
                    kwargs["timelimit"] = timelimit
                for r in ddgs.text(q, **kwargs):
                    url = r.get("href", "")
                    if url not in seen_urls:
                        seen_urls.add(url)
                        results.append(DDGSResult(
                            title=r.get("title", ""),
                            url=url,
                            snippet=r.get("body", ""),
                            source=q,
                        ))
            except Exception as exc:
                log.warning("DDGS query '%s' failed: %s", q[:50], exc)

    return results
