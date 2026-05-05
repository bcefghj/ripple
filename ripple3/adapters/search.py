"""Multi-engine search coordinator — 9-layer parallel search matrix.

Orchestrates 9 layers of search engines to deliver 1000+ results per analysis:
  0. MiniMax Token Plan web search (highest priority, free with subscription)
  1. LLM search (Hunyuan w/ EnableEnhancement, Qwen)
  2. Search APIs (Serper, Tavily, Exa, You, Brave)
  3. Free libraries (Baidu, Google, DuckDuckGo)
  4. Platform direct APIs (Weibo, Bilibili, Zhihu, Baidu)
  5. Hot trends aggregation (DailyHotApi)
  6. Meta-search (SearXNG)
  7. Jina AI (search + reader)

Ripple 6.0 Upgrades:
  - Topic Decomposition driven query generation (30+ targeted queries)
  - MiniMax web search as Layer 0 (450 free searches/day)
  - Relevance filtering with LLM classification
  - Search quality self-validation with auto-retry (Reflection Pattern)
  - 9-layer parallel fan-out with deduplication
  - TTL-based result cache (5 min), empty results never cached
  - Semaphore-based concurrency cap (raised to 30)
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from adapters.ddgs_adapter import ddgs_multi_text, ddgs_news_search, DDGSResult, DDGSNewsResult

log = logging.getLogger(__name__)

_SEARCH_TIMEOUT = 30
_CONCURRENCY_LIMIT = asyncio.Semaphore(30)

# ── Data models ──────────────────────────────────────────────────────────────


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    source: str = ""
    date: str = ""
    engine: str = ""


@dataclass
class NewsResult:
    title: str
    url: str
    snippet: str
    date: str = ""
    source: str = ""


# ── Cache ────────────────────────────────────────────────────────────────────

_cache: dict[str, tuple[float, Any]] = {}
_CACHE_TTL = 300


def _cache_get(key: str) -> Any | None:
    entry = _cache.get(key)
    if entry and (time.monotonic() - entry[0]) < _CACHE_TTL:
        return entry[1]
    return None


def _cache_set(key: str, value: Any) -> None:
    if isinstance(value, dict):
        total = sum(len(v) for v in value.values() if isinstance(v, list))
        if total == 0:
            return
    elif isinstance(value, list) and len(value) == 0:
        return
    _cache[key] = (time.monotonic(), value)


# ── Time helpers ─────────────────────────────────────────────────────────────

def _current_date_str() -> str:
    """e.g. '2026年5月'"""
    now = datetime.now()
    return f"{now.year}年{now.month}月"


def _current_year() -> str:
    return str(datetime.now().year)


def _iso_30_days_ago() -> str:
    """ISO date string 30 days ago, for Exa startPublishedDate."""
    from datetime import timedelta
    return (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%dT00:00:00.000Z")


# ── Async helpers ────────────────────────────────────────────────────────────

async def _run_with_timeout(fn, *args, timeout: float = _SEARCH_TIMEOUT):
    async with _CONCURRENCY_LIMIT:
        try:
            return await asyncio.wait_for(
                asyncio.to_thread(fn, *args),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            log.warning("Search timed out after %ss: %s", timeout, fn.__name__)
            return []
        except Exception as exc:
            log.warning("Search failed: %s: %s", fn.__name__, exc)
            return []


def _dedup_results(results: list[SearchResult]) -> list[SearchResult]:
    seen: set[str] = set()
    deduped: list[SearchResult] = []
    for r in results:
        if r.url not in seen:
            seen.add(r.url)
            deduped.append(r)
    return deduped


# ── Query generation ─────────────────────────────────────────────────────────

def _generate_peer_queries(domain: str) -> list[str]:
    date = _current_date_str()
    year = _current_year()
    return [
        f"site:mp.weixin.qq.com {domain} 爆款 阅读量 {date}",
        f"视频号 {domain} 优质内容 爆款 {date}",
        f"site:xiaohongshu.com {domain} 爆款笔记 高赞 {year}",
        f"抖音 {domain} 热门内容 播放量 最新 {date}",
        f"B站 {domain} 热门视频 最新 {date}",
        f"{domain} KOC 爆款内容 分析 {date}",
        f"{domain} 内容创作 趋势 {date}",
        f"{domain} 爆款案例 数据分析 {year}",
        f"site:weibo.com {domain} 热门话题 {date}",
        f"{domain} 优质内容 推荐 最新",
        f"{domain} 涨粉 方法 {year}",
        f"{domain} 内容运营 策略 {date}",
        f"{domain} 热点 追踪 {date}",
        f"{domain} 自媒体 干货 {year}",
        f"{domain} 短视频 爆款 创作技巧 {year}",
    ]


def _generate_blogger_queries(domain: str) -> list[str]:
    date = _current_date_str()
    year = _current_year()
    return [
        f"site:mp.weixin.qq.com {domain} 博主 大V 值得关注 {date}",
        f"视频号 {domain} 博主 达人 推荐 {date}",
        f"site:xiaohongshu.com {domain} 博主 推荐 值得关注 {year}",
        f"{domain} KOC 博主 推荐 排行 {date}",
        f"抖音 {domain} 达人 排行榜 最新 {date}",
        f"B站 {domain} UP主 排行 推荐 {date}",
        f"{domain} 博主 粉丝量 {year}",
        f"{domain} 头部博主 风格 分析 {year}",
        f"{domain} 新人博主 黑马 崛起 {date}",
        f"微博 {domain} 大V 推荐 {date}",
        f"{domain} KOL 合作 推荐 {year}",
        f"{domain} 创作者 访谈 经验 {year}",
        f"{domain} 达人 带货 排名 {date}",
        f"{domain} 视频号 创作者 推荐 {date}",
        f"{domain} 公众号 值得关注 {date}",
    ]


def _generate_news_queries(domain: str) -> list[str]:
    date = _current_date_str()
    return [
        f"{domain} 最新趋势 {date}",
        f"{domain} 热点话题 最新动态 {date}",
        f"{domain} 行业新闻 {date}",
        f"{domain} 政策变化 最新 {date}",
        f"{domain} 平台更新 算法变化 {date}",
    ]


def _generate_competition_queries(topic: str) -> list[str]:
    date = _current_date_str()
    year = _current_year()
    return [
        f"site:xiaohongshu.com {topic} {date}",
        f"site:mp.weixin.qq.com {topic} {date}",
        f"视频号 {topic} {date}",
        f"抖音 {topic} 最新 {date}",
        f"{topic} 爆款 分析 数据 {year}",
        f"{topic} 内容 竞品 分析 {year}",
        f"B站 {topic} {date}",
        f"微博 {topic} 讨论 {date}",
        f"{topic} 受众 分析 {year}",
        f"{topic} 创作 角度 切入 {year}",
    ]


def _generate_trending_queries() -> list[str]:
    date = _current_date_str()
    return [
        f"微博热搜榜 今日 {date}",
        f"抖音热搜 今日热门话题 {date}",
        f"小红书 热门话题 最近流行 {date}",
        f"视频号 热门 推荐 今日 {date}",
        f"微信 热议 话题 今日",
        f"B站 热门 排行 今日 {date}",
        f"知乎 热榜 今日 {date}",
        f"百度热搜 今日 {date}",
    ]


# ── Multi-engine search functions ────────────────────────────────────────────

async def _search_ddgs(queries: list[str], max_per_query: int = 10) -> list[SearchResult]:
    """DuckDuckGo search (sync, run in thread)."""
    raw = await _run_with_timeout(
        ddgs_multi_text, queries,
        max_per_query=max_per_query,
        timelimit="m",
    )
    return [
        SearchResult(title=r.title, url=r.url, snippet=r.snippet, source=r.source, engine="ddgs")
        for r in (raw or [])
    ]


async def _search_serper(queries: list[str], num_per_query: int = 20) -> list[SearchResult]:
    """Google search via Serper API."""
    try:
        from adapters.serper_adapter import search_serper_multi
        raw = await search_serper_multi(queries, num_per_query=num_per_query, tbs="qdr:m")
        return [
            SearchResult(title=r.title, url=r.url, snippet=r.snippet, date=r.date, engine="serper")
            for r in raw
        ]
    except Exception:
        return []


async def _search_exa(queries: list[str], num_per_query: int = 10) -> list[SearchResult]:
    """Semantic search via Exa API."""
    try:
        from adapters.exa_adapter import search_exa_multi
        raw = await search_exa_multi(
            queries,
            num_per_query=num_per_query,
            start_published_date=_iso_30_days_ago(),
        )
        return [
            SearchResult(
                title=r.title, url=r.url, snippet=r.snippet,
                date=r.published_date, engine="exa",
            )
            for r in raw
        ]
    except Exception:
        return []


async def _search_tavily(queries: list[str], max_per_query: int = 10) -> list[SearchResult]:
    """AI-optimized search via Tavily API."""
    try:
        from adapters.tavily_adapter import search_tavily_multi
        raw = await search_tavily_multi(queries, max_per_query=max_per_query)
        return [
            SearchResult(title=r.title, url=r.url, snippet=r.snippet, engine="tavily")
            for r in raw
        ]
    except Exception:
        return []


async def _search_hunyuan(queries: list[str]) -> list[SearchResult]:
    """Layer 1: Tencent Hunyuan search-enhanced."""
    try:
        from adapters.hunyuan_search import hunyuan_search_multi
        raw = await hunyuan_search_multi(queries)
        return [
            SearchResult(title=r.title, url=r.url, snippet=r.snippet, engine="hunyuan")
            for r in raw
        ]
    except Exception:
        return []


async def _search_qwen(queries: list[str]) -> list[SearchResult]:
    """Layer 1: Alibaba Qwen search-enhanced."""
    try:
        from adapters.qwen_search import qwen_search_multi
        raw = await qwen_search_multi(queries)
        return [
            SearchResult(title=r.title, url=r.url, snippet=r.snippet, engine="qwen")
            for r in raw
        ]
    except Exception:
        return []


async def _search_brave(queries: list[str], max_per_query: int = 20) -> list[SearchResult]:
    """Layer 2: Brave Search API."""
    try:
        from adapters.brave_adapter import search_brave_multi
        raw = await search_brave_multi(queries, max_per_query=max_per_query)
        return [
            SearchResult(title=r.title, url=r.url, snippet=r.snippet, engine="brave")
            for r in raw
        ]
    except Exception:
        return []


async def _search_you(queries: list[str], max_per_query: int = 20) -> list[SearchResult]:
    """Layer 2: You.com Search API."""
    try:
        from adapters.you_adapter import search_you_multi
        raw = await search_you_multi(queries, max_per_query=max_per_query)
        return [
            SearchResult(title=r.title, url=r.url, snippet=r.snippet, engine="you")
            for r in raw
        ]
    except Exception:
        return []


async def _search_baidu(queries: list[str], max_per_query: int = 20) -> list[SearchResult]:
    """Layer 3: Baidu search (free, no key)."""
    try:
        from adapters.baidu_adapter import baidu_search_multi
        raw = await baidu_search_multi(queries, max_per_query=max_per_query)
        return [
            SearchResult(title=r.title, url=r.url, snippet=r.snippet, engine="baidu")
            for r in raw
        ]
    except Exception:
        return []


async def _search_google(queries: list[str], max_per_query: int = 20) -> list[SearchResult]:
    """Layer 3: Google search (free, no key)."""
    try:
        from adapters.google_adapter import google_search_multi
        raw = await google_search_multi(queries, max_per_query=max_per_query)
        return [
            SearchResult(title=r.title, url=r.url, snippet=r.snippet, engine="google")
            for r in raw
        ]
    except Exception:
        return []


async def _search_platform_apis(queries: list[str]) -> list[SearchResult]:
    """Layer 4: Direct platform web APIs."""
    try:
        from adapters.platform_apis import search_platforms
        raw = await search_platforms(queries)
        return [
            SearchResult(
                title=r.title, url=r.url, snippet=r.snippet,
                source=r.platform, engine=f"platform:{r.platform}",
            )
            for r in raw
        ]
    except Exception:
        return []


async def _search_dailyhot(queries: list[str]) -> list[SearchResult]:
    """Layer 5: DailyHotApi hot trends aggregation."""
    try:
        from adapters.dailyhot_adapter import fetch_hot_flat
        raw = await fetch_hot_flat()
        domain_keywords = set()
        for q in queries[:5]:
            domain_keywords.update(q.replace("site:", "").split()[:3])

        results = []
        for item in raw:
            title = item.title.lower()
            relevant = not domain_keywords or any(kw.lower() in title for kw in domain_keywords if len(kw) > 1)
            if relevant or len(results) < 50:
                results.append(SearchResult(
                    title=item.title, url=item.url,
                    snippet=f"热度: {item.hot_value}",
                    source=item.platform, engine=f"dailyhot:{item.platform}",
                ))
        return results
    except Exception:
        return []


async def _search_searxng(queries: list[str], max_per_query: int = 30) -> list[SearchResult]:
    """Layer 6: SearXNG meta-search."""
    try:
        from adapters.searxng_adapter import searxng_search_multi
        raw = await searxng_search_multi(queries, max_per_query=max_per_query)
        return [
            SearchResult(title=r.title, url=r.url, snippet=r.snippet, engine="searxng")
            for r in raw
        ]
    except Exception:
        return []


async def _search_jina(queries: list[str]) -> list[SearchResult]:
    """Layer 7: Jina AI search."""
    try:
        from adapters.jina_adapter import jina_search_multi
        raw = await jina_search_multi(queries)
        return [
            SearchResult(title=r.title, url=r.url, snippet=r.snippet, engine="jina")
            for r in raw
        ]
    except Exception:
        return []


async def _search_minimax(queries: list[str], max_per_query: int = 20) -> list[SearchResult]:
    """Layer 0: MiniMax Token Plan built-in web search (free, 450/day)."""
    try:
        from adapters.minimax_search import minimax_search_multi
        raw = await minimax_search_multi(queries, max_per_query=max_per_query)
        return [
            SearchResult(title=r.title, url=r.url, snippet=r.snippet, engine="minimax")
            for r in raw
        ]
    except Exception:
        return []


async def _fan_out_search(queries: list[str], *, max_per_query: int = 20) -> list[SearchResult]:
    """9-layer search matrix: fire all in parallel, merge and deduplicate."""
    tasks = [
        _search_minimax(queries[:8], max_per_query=max_per_query),
        _search_hunyuan(queries[:6]),
        _search_qwen(queries[:6]),
        _search_serper(queries, num_per_query=max_per_query),
        _search_tavily(queries[:12], max_per_query=max_per_query),
        _search_exa(queries[:12], num_per_query=min(max_per_query, 10)),
        _search_you(queries[:8], max_per_query=max_per_query),
        _search_brave(queries[:8], max_per_query=max_per_query),
        _search_baidu(queries, max_per_query=max_per_query),
        _search_google(queries[:8], max_per_query=max_per_query),
        _search_ddgs(queries, max_per_query=max_per_query),
        _search_platform_apis(queries),
        _search_dailyhot(queries),
        _search_searxng(queries[:8], max_per_query=max_per_query),
        _search_jina(queries[:5]),
    ]
    results_lists = await asyncio.gather(*tasks, return_exceptions=True)

    combined: list[SearchResult] = []
    engine_stats: dict[str, int] = {}
    for result in results_lists:
        if isinstance(result, list):
            for r in result:
                combined.append(r)
                engine = r.engine.split(":")[0] if ":" in r.engine else r.engine
                engine_stats[engine] = engine_stats.get(engine, 0) + 1

    deduped = _dedup_results(combined)
    log.info(
        "搜索矩阵: %d 条原始 → %d 条去重 | 引擎统计: %s",
        len(combined), len(deduped), engine_stats,
    )
    return deduped


# ── Public search functions ──────────────────────────────────────────────────

def search_topic(topic: str, *, max_results: int = 10) -> list[SearchResult]:
    """Simple synchronous single-topic search (kept for backward compat)."""
    from duckduckgo_search import DDGS
    results: list[SearchResult] = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(topic, max_results=max_results, region="cn-zh"):
                results.append(SearchResult(
                    title=r.get("title", ""),
                    url=r.get("href", ""),
                    snippet=r.get("body", ""),
                ))
    except Exception as exc:
        log.warning("Search '%s' failed: %s", topic, exc)
    return results


async def search_parallel_radar(domain: str) -> dict:
    """Run all radar-related searches across all engines in parallel.

    Ripple 6.0: Uses Topic Decomposition for targeted queries,
    relevance filtering, and search quality validation with retry.
    Target: 1000+ relevant results.
    """
    cache_key = f"radar:{domain}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    try:
        from engines.topic_decomposer import decompose_domain
        from adapters.query_builder import build_radar_queries
        from engines.relevance_filter import filter_by_relevance
        from engines.search_validator import validate_search_quality, generate_retry_queries

        tree = await decompose_domain(domain)
        query_sets = build_radar_queries(tree)
    except Exception as exc:
        log.warning("Topic decomposition failed, using legacy queries: %s", exc)
        query_sets = {
            "peers": _generate_peer_queries(domain),
            "bloggers": _generate_blogger_queries(domain),
            "news": _generate_news_queries(domain),
            "trending": _generate_trending_queries(),
        }

    max_per = 25

    async def _run_search(qs: dict) -> dict:
        tasks = {
            key: _fan_out_search(queries, max_per_query=max_per)
            for key, queries in qs.items()
        }
        results = await asyncio.gather(*tasks.values())
        return dict(zip(tasks.keys(), results))

    result = await _run_search(query_sets)

    # Reflection: validate and retry if needed
    all_results = []
    for v in result.values():
        all_results.extend(v)

    try:
        validation = validate_search_quality(domain, all_results)
        if not validation.passed and validation.retry_suggestions:
            retry_queries = generate_retry_queries(domain, validation, 
                [q for qs in query_sets.values() for q in qs])
            if retry_queries:
                log.info("Search reflection: retrying with %d new queries", len(retry_queries))
                extra_results = await _fan_out_search(retry_queries, max_per_query=max_per)
                result.setdefault("peers", []).extend(extra_results)
    except Exception as exc:
        log.warning("Search validation failed: %s", exc)

    # Relevance filtering on peers (the main content category)
    try:
        if result.get("peers"):
            filtered = await filter_by_relevance(domain, result["peers"])
            result["peers"] = filtered.relevant if filtered.relevant else result["peers"]
    except Exception as exc:
        log.warning("Relevance filter failed: %s", exc)

    _cache_set(cache_key, result)
    return result


async def search_parallel_idea(domain: str) -> dict:
    """Parallel searches for idea generation with Topic Decomposition."""
    cache_key = f"idea:{domain}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    try:
        from engines.topic_decomposer import decompose_domain
        from adapters.query_builder import build_idea_queries

        tree = await decompose_domain(domain)
        query_sets = build_idea_queries(tree)
    except Exception:
        query_sets = {
            "peers": _generate_peer_queries(domain),
            "news": _generate_news_queries(domain),
            "trending": _generate_trending_queries(),
        }

    peers, news, trending = await asyncio.gather(
        _fan_out_search(query_sets.get("peers", []), max_per_query=25),
        _fan_out_search(query_sets.get("news", []), max_per_query=15),
        _fan_out_search(query_sets.get("trending", []), max_per_query=15),
    )

    result = {"peers": peers, "news": news, "trending": trending}
    _cache_set(cache_key, result)
    return result


async def search_parallel_predict(topic: str, domain: str = "") -> dict:
    """Parallel searches for viral prediction with targeted queries."""
    cache_key = f"predict:{topic}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    try:
        from adapters.query_builder import build_predict_queries
        query_sets = build_predict_queries(topic, domain)
    except Exception:
        query_sets = {
            "competition": _generate_competition_queries(topic),
            "trending": _generate_trending_queries(),
        }

    competition, trending = await asyncio.gather(
        _fan_out_search(query_sets.get("competition", []), max_per_query=25),
        _fan_out_search(query_sets.get("trending", []), max_per_query=15),
    )

    result = {"competition": competition, "trending": trending}
    _cache_set(cache_key, result)
    return result


async def search_parallel_distill(blogger: str, domain: str = "") -> dict:
    """Parallel searches for style distillation with targeted queries."""
    cache_key = f"distill:{blogger}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    try:
        from adapters.query_builder import build_distill_queries
        query_sets = build_distill_queries(blogger, domain)
    except Exception:
        query_sets = {
            "content": [
                f"{blogger} 内容 作品 风格",
                f"{blogger} 代表作 热门 文章",
                f"{blogger} 视频 爆款",
                f"site:xiaohongshu.com {blogger}",
                f"site:mp.weixin.qq.com {blogger}",
                f"B站 {blogger} 视频",
            ],
            "profile": [
                f"{blogger} 博主 介绍 领域",
                f"{blogger} 个人简介 粉丝",
                f"{blogger} 创作者 背景",
            ],
        }

    content, profile = await asyncio.gather(
        _fan_out_search(query_sets.get("content", []), max_per_query=20),
        _fan_out_search(query_sets.get("profile", []), max_per_query=15),
    )

    result = {"content": content, "profile": profile}
    _cache_set(cache_key, result)
    return result
