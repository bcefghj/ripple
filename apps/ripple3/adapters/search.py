"""Multi-dimensional search adapter with 2026 freshness and Tencent platform focus.

Provides:
  - search_peers()       — high-engagement posts in a domain
  - search_bloggers()    — top bloggers / KOLs in a domain
  - search_news()        — recent news and rising topics
  - search_competition() — existing content on a specific topic
  - search_trending()    — real-time trending topics across platforms
  - search_topic()       — general keyword search
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from ddgs import DDGS

log = logging.getLogger(__name__)


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    source: str = ""


@dataclass
class NewsResult:
    title: str
    url: str
    snippet: str
    date: str = ""
    source: str = ""


def search_peers(domain: str, *, max_results: int = 30) -> list[SearchResult]:
    """Search for recent high-engagement content — weighted toward Tencent platforms."""
    queries = [
        f"视频号 {domain} 优质内容 爆款 2025 2026",
        f"公众号 {domain} 爆款文章 高阅读量 最新",
        f"小红书 {domain} 爆款笔记 高赞 最新",
        f"抖音 {domain} 热门内容 播放量 最新",
        f"B站 {domain} 热门视频 最新",
    ]
    return _multi_query(queries, max_results)


def search_bloggers(domain: str, *, max_results: int = 30) -> list[SearchResult]:
    """Search for top bloggers / KOLs — including Tencent ecosystem creators."""
    queries = [
        f"视频号 {domain} 博主 达人 推荐 2025 2026",
        f"公众号 {domain} 大V 值得关注 最新",
        f"{domain} KOC 博主 推荐 排行 最新",
        f"小红书 {domain} 博主 推荐 值得关注",
        f"抖音 {domain} 达人 排行榜 最新",
        f"B站 {domain} UP主 排行 推荐",
    ]
    return _multi_query(queries, max_results)


def search_news(domain: str, *, max_results: int = 20) -> list[NewsResult]:
    """Search recent news and trending topics."""
    queries = [
        f"{domain} 最新趋势 2026",
        f"{domain} 热点话题 最新动态",
    ]
    results: list[NewsResult] = []
    seen_urls: set[str] = set()
    per_query = max(max_results // len(queries), 5)

    with DDGS() as ddgs:
        for q in queries:
            try:
                for r in ddgs.news(q, max_results=per_query, region="cn-zh"):
                    url = r.get("url", "")
                    if url in seen_urls:
                        continue
                    seen_urls.add(url)
                    results.append(NewsResult(
                        title=r.get("title", ""),
                        url=url,
                        snippet=r.get("body", ""),
                        date=r.get("date", ""),
                        source=r.get("source", ""),
                    ))
            except Exception as exc:
                log.warning("News search '%s' failed: %s", q, exc)

    return results


def search_competition(topic: str, *, max_results: int = 15) -> list[SearchResult]:
    """Search for existing content on a specific topic to assess competition."""
    queries = [
        f"小红书 {topic} 最新",
        f"视频号 {topic}",
        f"抖音 {topic} 最新",
        f"{topic} 爆款 分析",
    ]
    return _multi_query(queries, max_results)


def search_trending(*, max_results: int = 20) -> list[SearchResult]:
    """Fetch current trending topics across Chinese social platforms."""
    queries = [
        "微博热搜榜 今日",
        "抖音热搜 今日热门话题",
        "小红书 热门话题 最近流行",
        "B站 热门 今日",
    ]
    return _multi_query(queries, max_results)


def search_topic(topic: str, *, max_results: int = 10) -> list[SearchResult]:
    """General search for a specific topic."""
    results: list[SearchResult] = []
    with DDGS() as ddgs:
        try:
            for r in ddgs.text(topic, max_results=max_results, region="cn-zh"):
                results.append(SearchResult(
                    title=r.get("title", ""),
                    url=r.get("href", ""),
                    snippet=r.get("body", ""),
                ))
        except Exception as exc:
            log.warning("Search '%s' failed: %s", topic, exc)
    return results


def _multi_query(queries: list[str], max_results: int) -> list[SearchResult]:
    """Run multiple queries, deduplicate by URL."""
    results: list[SearchResult] = []
    seen_urls: set[str] = set()
    per_query = max(max_results // len(queries), 5)

    with DDGS() as ddgs:
        for q in queries:
            try:
                for r in ddgs.text(q, max_results=per_query, region="cn-zh"):
                    url = r.get("href", "")
                    if url in seen_urls:
                        continue
                    seen_urls.add(url)
                    results.append(SearchResult(
                        title=r.get("title", ""),
                        url=url,
                        snippet=r.get("body", ""),
                        source=q,
                    ))
            except Exception as exc:
                log.warning("Search query '%s' failed: %s", q, exc)

    return results
