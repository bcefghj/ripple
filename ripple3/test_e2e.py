#!/usr/bin/env python3
"""End-to-end test — validates the full Ripple pipeline from intent to output.

Usage:
    python test_e2e.py              # Run all E2E tests
    python test_e2e.py --search     # Only test search pipeline
    python test_e2e.py --intent     # Only test intent classification
"""

import asyncio
import logging
import sys
import time

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(name)s | %(message)s")
log = logging.getLogger("test_e2e")


async def test_intent_classification():
    """Test that intent classification correctly routes different user inputs."""
    log.info("=== Intent Classification Test ===")
    from core.intent import classify_intent

    cases = [
        ("帮我分析数码科技领域", "radar", "数码"),
        ("帮我想10个选题灵感", "idea", ""),
        ("谢娜成都演唱会 这个内容", "predict", "谢娜"),
        ("帮我写一篇小红书笔记", "create", ""),
        ("分析何同学的风格", "distill", "何同学"),
        ("你好", "chat", ""),
    ]

    passed = 0
    for message, expected_intent, expected_keyword in cases:
        result = await classify_intent(message, [])
        intent_ok = result.intent == expected_intent
        keyword_ok = not expected_keyword or expected_keyword in (result.domain + result.topic)

        status = "PASS" if intent_ok else "FAIL"
        log.info(
            "  [%s] '%s' → intent=%s (expected %s), domain=%s, topic=%s",
            status, message[:20], result.intent, expected_intent, result.domain, result.topic,
        )
        if intent_ok:
            passed += 1

    log.info("  Intent classification: %d/%d passed", passed, len(cases))
    return passed >= len(cases) - 1


async def test_search_pipeline():
    """Test the full search pipeline with a real-world query."""
    log.info("=== Search Pipeline Test ===")
    from adapters.search import _fan_out_search

    queries = ["谢娜 成都演唱会 2026年5月"]
    start = time.time()
    results = await asyncio.wait_for(_fan_out_search(queries, max_per_query=10), timeout=60)
    elapsed = time.time() - start

    engines = {}
    for r in results:
        eng = r.engine.split(":")[0] if ":" in r.engine else r.engine
        engines[eng] = engines.get(eng, 0) + 1

    relevant = [r for r in results if "谢娜" in r.title or "演唱会" in r.title]

    log.info("  Total results: %d (in %.1fs)", len(results), elapsed)
    log.info("  Relevant (谢娜/演唱会): %d", len(relevant))
    log.info("  Active engines: %s", engines)

    for r in relevant[:5]:
        log.info("    - [%s] %s", r.engine, r.title[:50])

    ok = len(results) > 0
    if not relevant:
        log.warning("  WARNING: No relevant results found for known event")
    return ok


async def test_minimax_search_benchmark():
    """Benchmark MiniMax search across different query types."""
    log.info("=== MiniMax Search Benchmark ===")
    from adapters.minimax_search import minimax_web_search

    queries = [
        "谢娜 成都演唱会 2026",
        "小红书 爆款笔记 护肤 2026",
        "数码科技 最新趋势 2026年5月",
        "AI 人工智能 最新进展",
        "美食探店 成都 推荐",
    ]

    total_results = 0
    for q in queries:
        start = time.time()
        results = await minimax_web_search(q, count=10)
        elapsed = time.time() - start
        total_results += len(results)
        log.info("  '%s' → %d results (%.1fs)", q[:30], len(results), elapsed)

    log.info("  Total: %d results from %d queries (avg %.1f/query)", total_results, len(queries), total_results / len(queries))
    return total_results > len(queries) * 3


async def test_chat_api_simulation():
    """Simulate the /api/chat endpoint flow without actually running the server."""
    log.info("=== Chat API Simulation ===")
    from core.intent import classify_intent
    from adapters.minimax_search import minimax_search_multi

    message = "谢娜成都演唱会 这个内容"
    intent = await classify_intent(message, [])
    log.info("  Intent: %s, domain=%s, topic=%s", intent.intent, intent.domain, intent.topic)

    search_results = await minimax_search_multi([message, f"{message} 最新"], max_per_query=10)
    log.info("  Search: %d results", len(search_results))

    if search_results:
        log.info("  Top 3:")
        for r in search_results[:3]:
            log.info("    - %s", r.title[:50])

    return len(search_results) > 0


async def main():
    search_only = "--search" in sys.argv
    intent_only = "--intent" in sys.argv

    tests = []

    if intent_only:
        tests = [("Intent Classification", test_intent_classification)]
    elif search_only:
        tests = [
            ("MiniMax Benchmark", test_minimax_search_benchmark),
            ("Search Pipeline", test_search_pipeline),
        ]
    else:
        tests = [
            ("Intent Classification", test_intent_classification),
            ("MiniMax Benchmark", test_minimax_search_benchmark),
            ("Search Pipeline", test_search_pipeline),
            ("Chat API Simulation", test_chat_api_simulation),
        ]

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
    log.info("E2E TEST RESULTS")
    log.info("=" * 60)
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    for name, ok in results.items():
        status = "PASS" if ok else "FAIL"
        log.info("  [%s] %s", status, name)
    log.info("")
    log.info("  %d/%d passed", passed, total)
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
