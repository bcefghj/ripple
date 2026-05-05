"""Multi-dimensional search adapter with async parallel execution.

Provides synchronous search primitives and async orchestrators that run
them in parallel via asyncio.TaskGroup + to_thread.

Includes:
  - TTL-based result cache (5 min) to avoid redundant queries
  - Per-query timeout protection (10s)
  - Semaphore-based concurrency cap to avoid rate-limiting
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from functools import wraps
from typing import Any

from ddgs import DDGS

log = logging.getLogger(__name__)

_SEARCH_TIMEOUT = 30
_CONCURRENCY_LIMIT = asyncio.Semaphore(6)

# ── Data models ──────────────────────────────────────────────────────────────


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


# ── Cache ────────────────────────────────────────────────────────────────────

_cache: dict[str, tuple[float, Any]] = {}
_CACHE_TTL = 300  # 5 minutes


def _cache_get(key: str) -> Any | None:
    entry = _cache.get(key)
    if entry and (time.monotonic() - entry[0]) < _CACHE_TTL:
        return entry[1]
    return None


def _cache_set(key: str, value: Any) -> None:
    _cache[key] = (time.monotonic(), value)


# ── Synchronous search primitives ────────────────────────────────────────────


def search_peers(domain: str, *, max_results: int = 30) -> list[SearchResult]:
    cache_key = f"peers:{domain}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    queries = [
        f"site:mp.weixin.qq.com {domain} 爆款 阅读量 2026",
        f"视频号 {domain} 优质内容 爆款 2026",
        f"site:xiaohongshu.com {domain} 爆款笔记 高赞",
        f"抖音 {domain} 热门内容 播放量 最新 2026",
        f"B站 {domain} 热门视频 最新 2026",
        f"{domain} KOC 爆款内容 分析 2026",
    ]
    result = _multi_query(queries, max_results)
    _cache_set(cache_key, result)
    return result


def search_bloggers(domain: str, *, max_results: int = 30) -> list[SearchResult]:
    cache_key = f"bloggers:{domain}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    queries = [
        f"site:mp.weixin.qq.com {domain} 博主 大V 值得关注 2026",
        f"视频号 {domain} 博主 达人 推荐 2026",
        f"site:xiaohongshu.com {domain} 博主 推荐 值得关注",
        f"{domain} KOC 博主 推荐 排行 2026",
        f"抖音 {domain} 达人 排行榜 最新",
        f"B站 {domain} UP主 排行 推荐 2026",
    ]
    result = _multi_query(queries, max_results)
    _cache_set(cache_key, result)
    return result


def search_news(domain: str, *, max_results: int = 20) -> list[NewsResult]:
    cache_key = f"news:{domain}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

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

    _cache_set(cache_key, results)
    return results


def search_competition(topic: str, *, max_results: int = 15) -> list[SearchResult]:
    cache_key = f"comp:{topic}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    queries = [
        f"site:xiaohongshu.com {topic} 2026",
        f"site:mp.weixin.qq.com {topic} 2026",
        f"视频号 {topic} 2026",
        f"抖音 {topic} 最新 2026",
        f"{topic} 爆款 分析 数据",
    ]
    result = _multi_query(queries, max_results)
    _cache_set(cache_key, result)
    return result


def search_trending(*, max_results: int = 20) -> list[SearchResult]:
    cached = _cache_get("trending")
    if cached is not None:
        return cached

    queries = [
        "微博热搜榜 今日 2026",
        "抖音热搜 今日热门话题 2026",
        "小红书 热门话题 最近流行 2026",
        "视频号 热门 推荐 今日 2026",
        "微信 热议 话题 今日",
    ]
    result = _multi_query(queries, max_results)
    _cache_set("trending", result)
    return result


def search_topic(topic: str, *, max_results: int = 10) -> list[SearchResult]:
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


# ── Async parallel orchestrators ─────────────────────────────────────────────


async def _run_with_timeout(fn, *args, timeout: float = _SEARCH_TIMEOUT):
    """Run a sync function in a thread with timeout and concurrency control."""
    async with _CONCURRENCY_LIMIT:
        try:
            return await asyncio.wait_for(
                asyncio.to_thread(fn, *args),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            log.warning("Search timed out after %ss: %s(%s)", timeout, fn.__name__, args[:1])
            return [] if "search" in fn.__name__ else []
        except Exception as exc:
            log.warning("Search failed: %s(%s): %s", fn.__name__, args[:1], exc)
            return []


async def search_parallel_radar(domain: str) -> dict:
    """Run all radar-related searches in parallel. ~3-5s instead of ~12s."""
    async with asyncio.TaskGroup() as tg:
        t_peers = tg.create_task(_run_with_timeout(search_peers, domain))
        t_bloggers = tg.create_task(_run_with_timeout(search_bloggers, domain))
        t_news = tg.create_task(_run_with_timeout(search_news, domain))
        t_trending = tg.create_task(_run_with_timeout(search_trending))
    return {
        "peers": t_peers.result(),
        "bloggers": t_bloggers.result(),
        "news": t_news.result(),
        "trending": t_trending.result(),
    }


async def search_parallel_idea(domain: str) -> dict:
    """Parallel searches for idea generation."""
    async with asyncio.TaskGroup() as tg:
        t_peers = tg.create_task(_run_with_timeout(search_peers, domain))
        t_news = tg.create_task(_run_with_timeout(search_news, domain))
        t_trending = tg.create_task(_run_with_timeout(search_trending))
    return {
        "peers": t_peers.result(),
        "news": t_news.result(),
        "trending": t_trending.result(),
    }


async def search_parallel_predict(topic: str) -> dict:
    """Parallel searches for viral prediction."""
    async with asyncio.TaskGroup() as tg:
        t_comp = tg.create_task(_run_with_timeout(search_competition, topic))
        t_trending = tg.create_task(_run_with_timeout(search_trending))
    return {
        "competition": t_comp.result(),
        "trending": t_trending.result(),
    }


async def search_parallel_distill(blogger: str) -> dict:
    """Parallel searches for style distillation."""
    async with asyncio.TaskGroup() as tg:
        t_content = tg.create_task(_run_with_timeout(search_topic, f"{blogger} 内容 作品 风格"))
        t_profile = tg.create_task(_run_with_timeout(search_topic, f"{blogger} 博主 介绍 领域"))
    return {
        "content": t_content.result(),
        "profile": t_profile.result(),
    }
