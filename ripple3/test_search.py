#!/usr/bin/env python3
"""Search system verification test — validates all search layers.

Usage:
    python test_search.py          # Run all tests
    python test_search.py --quick  # Only test free (no-key) layers
"""

import asyncio
import logging
import sys
import time

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(name)s | %(message)s")
log = logging.getLogger("test_search")


async def test_config():
    """Test that config loads correctly and load_dotenv works."""
    from core.config import get_settings
    s = get_settings()
    log.info("=== Config Test ===")
    log.info("  xiaomi_api_key: %s", "SET" if s.xiaomi_api_key else "MISSING")
    log.info("  minimax_api_key: %s", "SET" if s.minimax_api_key else "MISSING")
    log.info("  serper_api_key: %s", "SET" if s.serper_api_key else "MISSING")
    log.info("  tavily_api_key: %s", "SET" if s.tavily_api_key else "MISSING")
    log.info("  exa_api_key: %s", "SET" if s.exa_api_key else "MISSING")
    log.info("  brave_api_key: %s", "SET" if s.brave_api_key else "MISSING")
    log.info("  you_api_key: %s", "SET" if s.you_api_key else "MISSING")
    log.info("  hunyuan_api_key: %s", "SET" if s.hunyuan_api_key else "MISSING")
    log.info("  qwen_api_key: %s", "SET" if s.qwen_api_key else "MISSING")
    log.info("  jina_api_key: %s", "SET" if s.jina_api_key else "MISSING")
    return True


async def test_baidu():
    """Test Baidu search (free, no key)."""
    log.info("=== Baidu Search Test ===")
    try:
        from adapters.baidu_adapter import baidu_search
        results = await asyncio.wait_for(baidu_search("美食探店 热门", num_results=5), timeout=20)
        log.info("  Results: %d", len(results))
        for r in results[:3]:
            log.info("    - %s | %s", r.title[:30], r.url[:50])
        return len(results) > 0
    except Exception as e:
        log.warning("  FAILED: %s", e)
        return False


async def test_platform_apis():
    """Test direct platform APIs (free, no key)."""
    log.info("=== Platform APIs Test ===")
    try:
        from adapters.platform_apis import fetch_all_platform_hot
        results = await asyncio.wait_for(fetch_all_platform_hot(), timeout=15)
        log.info("  Results: %d", len(results))
        for r in results[:5]:
            log.info("    - [%s] %s", r.platform, r.title[:30])
        return len(results) > 0
    except Exception as e:
        log.warning("  FAILED: %s", e)
        return False


async def test_dailyhot():
    """Test DailyHotApi (free, no key)."""
    log.info("=== DailyHotApi Test ===")
    try:
        from adapters.dailyhot_adapter import fetch_hot_flat
        results = await asyncio.wait_for(fetch_hot_flat(["weibo", "bilibili", "zhihu"]), timeout=15)
        log.info("  Results: %d", len(results))
        for r in results[:5]:
            log.info("    - [%s] %s (热度: %s)", r.platform, r.title[:30], r.hot_value)
        return len(results) > 0
    except Exception as e:
        log.warning("  FAILED: %s", e)
        return False


async def test_hot_trends():
    """Test aggregated hot trends."""
    log.info("=== Hot Trends Test ===")
    try:
        from adapters.hot_trends import fetch_all_trends, format_trends_for_llm
        trends = await asyncio.wait_for(fetch_all_trends(limit_per_platform=5), timeout=20)
        total = sum(len(items) for items in trends.values())
        log.info("  Platforms with data: %d", sum(1 for items in trends.values() if items))
        log.info("  Total items: %d", total)
        formatted = format_trends_for_llm(trends, max_per_platform=3)
        log.info("  Formatted preview: %s...", formatted[:100])
        return total > 0
    except Exception as e:
        log.warning("  FAILED: %s", e)
        return False


async def test_fan_out_search():
    """Test the full 8-layer fan-out search."""
    log.info("=== Fan-out Search Test ===")
    try:
        from adapters.search import _fan_out_search
        queries = ["美食探店 热门 2026", "美食博主 推荐"]
        start = time.time()
        results = await asyncio.wait_for(_fan_out_search(queries, max_per_query=5), timeout=60)
        elapsed = time.time() - start
        log.info("  Results: %d (in %.1fs)", len(results), elapsed)

        engines = {}
        for r in results:
            eng = r.engine.split(":")[0] if ":" in r.engine else r.engine
            engines[eng] = engines.get(eng, 0) + 1
        log.info("  Engine stats: %s", engines)

        for r in results[:5]:
            log.info("    - [%s] %s | %s", r.engine, r.title[:30], r.url[:50])
        return len(results) > 0
    except Exception as e:
        log.warning("  FAILED: %s", e)
        return False


async def test_searxng():
    """Test SearXNG (free, uses public instances)."""
    log.info("=== SearXNG Test ===")
    try:
        from adapters.searxng_adapter import searxng_search
        results = await asyncio.wait_for(searxng_search("Python programming", num_results=5), timeout=15)
        log.info("  Results: %d", len(results))
        for r in results[:3]:
            log.info("    - %s | %s", r.title[:30], r.url[:50])
        return len(results) > 0
    except Exception as e:
        log.warning("  FAILED: %s", e)
        return False


async def test_jina():
    """Test Jina AI search (free tier)."""
    log.info("=== Jina Search Test ===")
    try:
        from adapters.jina_adapter import jina_search
        results = await asyncio.wait_for(jina_search("美食探店", max_results=3), timeout=15)
        log.info("  Results: %d", len(results))
        for r in results[:3]:
            log.info("    - %s | %s", r.title[:30], r.url[:50])
        return len(results) > 0
    except Exception as e:
        log.warning("  FAILED: %s", e)
        return False


async def test_minimax_search():
    """Test MiniMax Coding Plan search (requires MINIMAX_API_KEY)."""
    log.info("=== MiniMax Search Test ===")
    try:
        from core.config import get_settings
        s = get_settings()
        if not s.minimax_api_key:
            log.warning("  SKIP: MINIMAX_API_KEY not set")
            return None

        from adapters.minimax_search import minimax_web_search
        results = await asyncio.wait_for(
            minimax_web_search("谢娜 2026年5月 成都演唱会", count=10),
            timeout=20,
        )
        log.info("  Results: %d", len(results))
        for r in results[:5]:
            log.info("    - %s | %s", r.title[:40], r.url[:60])

        if len(results) == 0:
            log.warning("  WARNING: MiniMax returned 0 results — endpoint may still be wrong")
        return len(results) > 0
    except Exception as e:
        log.warning("  FAILED: %s", e)
        return False


async def test_minimax_multi():
    """Test MiniMax concurrent multi-query search."""
    log.info("=== MiniMax Multi-Search Test ===")
    try:
        from core.config import get_settings
        if not get_settings().minimax_api_key:
            log.warning("  SKIP: MINIMAX_API_KEY not set")
            return None

        from adapters.minimax_search import minimax_search_multi
        queries = [
            "谢娜 成都演唱会 2026",
            "小红书 爆款 护肤 2026",
            "数码科技 最新趋势",
        ]
        start = time.time()
        results = await asyncio.wait_for(minimax_search_multi(queries, max_per_query=10), timeout=30)
        elapsed = time.time() - start
        log.info("  Results: %d unique (in %.1fs)", len(results), elapsed)
        for r in results[:5]:
            log.info("    - %s | %s", r.title[:40], r.url[:60])
        return len(results) > 0
    except Exception as e:
        log.warning("  FAILED: %s", e)
        return False


async def test_realtime_relevance():
    """Test that search can find a recent real-world event."""
    log.info("=== Realtime Relevance Test (谢娜演唱会) ===")
    try:
        from adapters.search import _fan_out_search
        queries = ["谢娜 2026年5月5日 成都演唱会"]
        start = time.time()
        results = await asyncio.wait_for(_fan_out_search(queries, max_per_query=10), timeout=60)
        elapsed = time.time() - start

        relevant = [r for r in results if "谢娜" in r.title or "演唱会" in r.title]
        log.info("  Total: %d, Relevant: %d (in %.1fs)", len(results), len(relevant), elapsed)
        for r in relevant[:5]:
            log.info("    - [%s] %s", r.engine, r.title[:40])

        if not relevant and results:
            log.info("  Top 5 results (for diagnosis):")
            for r in results[:5]:
                log.info("    - [%s] %s | %s", r.engine, r.title[:40], r.url[:50])

        return len(relevant) > 0
    except Exception as e:
        log.warning("  FAILED: %s", e)
        return False


async def main():
    quick = "--quick" in sys.argv

    tests = [
        ("Config", test_config),
        ("MiniMax Search", test_minimax_search),
        ("MiniMax Multi-Search", test_minimax_multi),
        ("Baidu (free)", test_baidu),
        ("Platform APIs (free)", test_platform_apis),
        ("DailyHotApi (free)", test_dailyhot),
        ("Hot Trends (aggregated)", test_hot_trends),
    ]

    if not quick:
        tests.extend([
            ("SearXNG", test_searxng),
            ("Jina AI", test_jina),
            ("Full Fan-out Search", test_fan_out_search),
            ("Realtime Relevance", test_realtime_relevance),
        ])

    results = {}
    for name, test_fn in tests:
        try:
            passed = await test_fn()
            results[name] = passed
        except Exception as e:
            log.error("Test '%s' crashed: %s", name, e)
            results[name] = False
        log.info("")

    log.info("=" * 60)
    log.info("TEST RESULTS")
    log.info("=" * 60)
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    for name, ok in results.items():
        status = "PASS" if ok else "FAIL"
        log.info("  [%s] %s", status, name)
    log.info("")
    log.info("  %d/%d passed", passed, total)

    if passed < total:
        log.warning("  Some tests failed. Check API keys and network connectivity.")
    else:
        log.info("  All tests passed!")

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
