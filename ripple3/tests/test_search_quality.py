"""Automated tests for Ripple 6.0 search quality, agent output, and end-to-end flow.

Run with: python -m pytest tests/test_search_quality.py -v
Or directly: python tests/test_search_quality.py
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def test_topic_decomposition():
    """Test 1: Topic decomposition generates meaningful sub-topics."""
    from engines.topic_decomposer import decompose_domain

    print("\n" + "=" * 60)
    print("TEST 1: Topic Decomposition")
    print("=" * 60)

    tree = await decompose_domain("数码科技")

    assert tree.domain == "数码科技"
    assert len(tree.sub_domains) >= 5, f"Expected >= 5 sub-domains, got {len(tree.sub_domains)}"
    assert len(tree.search_queries) >= 15, f"Expected >= 15 queries, got {len(tree.search_queries)}"

    print(f"  Domain: {tree.domain}")
    print(f"  Sub-domains ({len(tree.sub_domains)}): {tree.sub_domains[:5]}...")
    print(f"  Trending topics ({len(tree.trending_topics)}): {tree.trending_topics[:3]}...")
    print(f"  KOLs ({len(tree.key_kols)}): {tree.key_kols[:3]}...")
    print(f"  Platform angles: {list(tree.platform_angles.keys())}")
    print(f"  Total search queries: {len(tree.search_queries)}")
    print("  PASS")
    return True


async def test_query_builder():
    """Test 2: Query builder generates 30+ targeted queries."""
    from engines.topic_decomposer import decompose_domain
    from adapters.query_builder import build_radar_queries

    print("\n" + "=" * 60)
    print("TEST 2: Query Builder (30+ queries)")
    print("=" * 60)

    tree = await decompose_domain("数码科技")
    queries = build_radar_queries(tree)

    total_queries = sum(len(v) for v in queries.values())
    assert total_queries >= 30, f"Expected >= 30 total queries, got {total_queries}"

    print(f"  Categories: {list(queries.keys())}")
    for key, qs in queries.items():
        print(f"  {key}: {len(qs)} queries")
        for q in qs[:3]:
            print(f"    - {q}")

    print(f"  Total: {total_queries} queries")
    print("  PASS")
    return True


async def test_relevance_filter():
    """Test 3: Relevance filter correctly identifies domain-relevant content."""
    from engines.relevance_filter import filter_by_relevance
    from dataclasses import dataclass

    print("\n" + "=" * 60)
    print("TEST 3: Relevance Filter")
    print("=" * 60)

    @dataclass
    class MockResult:
        title: str
        url: str
        snippet: str

    results = [
        MockResult("iPhone 16 Pro 深度评测", "https://example.com/1", "这款手机的A18芯片性能提升明显，拍照效果出色"),
        MockResult("折叠屏手机一年使用体验", "https://example.com/2", "华为Mate X6的折叠屏在日常使用中表现如何"),
        MockResult("千元机推荐2026", "https://example.com/3", "预算有限但想要好的手机体验？这5款千元机值得考虑"),
        MockResult("第五人格COA全球赛", "https://example.com/4", "电竞战队对决精彩回顾"),
        MockResult("给老鼠在墙壁里开了家网吧", "https://example.com/5", "创意整活视频合集"),
        MockResult("华强买瓜恶搞动画", "https://example.com/6", "二次创作搞笑视频"),
        MockResult("MacBook Pro M4 测评", "https://example.com/7", "苹果最新笔记本电脑性能测试"),
        MockResult("蓝牙耳机降噪对比", "https://example.com/8", "AirPods Pro vs 索尼WH1000XM5 降噪效果对比"),
        MockResult("探店美食vlog", "https://example.com/9", "三亚餐厅探店记录"),
        MockResult("智能手表健康监测", "https://example.com/10", "Apple Watch和华为手表的健康监测功能对比"),
    ]

    filtered = await filter_by_relevance("数码科技", results, threshold=0.5)

    print(f"  Input: {len(results)} results")
    print(f"  Relevant: {len(filtered.relevant)} results")
    print(f"  Filtered out: {len(filtered.filtered)} results")
    print(f"  Relevance rate: {filtered.relevance_rate:.0%}")
    print(f"  Diagnostics: {filtered.diagnostics}")

    relevant_titles = [r.title for r in filtered.relevant]
    assert "iPhone 16 Pro 深度评测" in relevant_titles, "Should keep tech review"
    assert "MacBook Pro M4 测评" in relevant_titles, "Should keep laptop review"

    assert filtered.relevance_rate >= 0.5, f"Expected relevance >= 50%, got {filtered.relevance_rate:.0%}"
    print("  PASS")
    return True


async def test_search_validator():
    """Test 4: Search validator correctly identifies quality issues."""
    from engines.search_validator import validate_search_quality, generate_retry_queries
    from dataclasses import dataclass

    print("\n" + "=" * 60)
    print("TEST 4: Search Quality Validator")
    print("=" * 60)

    @dataclass
    class MockResult:
        title: str
        url: str
        snippet: str
        date: str = ""

    good_results = [
        MockResult("手机测评2026", f"https://site{i}.com/article", "这是一篇关于数码科技手机测评的详细文章" * 3)
        for i in range(20)
    ]

    bad_results = [
        MockResult("游戏视频", "https://game.com/1", ""),
        MockResult("搞笑动画", "https://game.com/2", "短"),
        MockResult("八卦新闻", "https://game.com/3", ""),
    ]

    good_validation = validate_search_quality("数码科技", good_results)
    bad_validation = validate_search_quality("数码科技", bad_results)

    print(f"  Good results validation:")
    print(f"    Score: {good_validation.score:.1f}")
    print(f"    Passed: {good_validation.passed}")
    print(f"  Bad results validation:")
    print(f"    Score: {bad_validation.score:.1f}")
    print(f"    Passed: {bad_validation.passed}")
    print(f"    Diagnostics: {bad_validation.diagnostics}")

    assert good_validation.score > bad_validation.score, "Good results should score higher"

    retry_queries = generate_retry_queries("数码科技", bad_validation, [])
    print(f"  Retry queries generated: {len(retry_queries)}")
    assert len(retry_queries) > 0, "Should generate retry queries for bad results"
    print("  PASS")
    return True


async def test_viral_scorer():
    """Test 5: Viral scorer produces meaningful scores."""
    from engines.viral_scorer import score_viral_potential

    print("\n" + "=" * 60)
    print("TEST 5: CES Viral Scorer")
    print("=" * 60)

    score = await score_viral_potential(
        topic="折叠屏手机一年真实使用体验分享",
        domain="数码科技",
        platform="小红书",
    )

    print(f"  Topic: 折叠屏手机一年真实使用体验分享")
    print(f"  Total Score: {score.total_score}/100")
    print(f"  Predicted Pool: {score.predicted_pool}")
    print(f"  Pool Probability: {score.pool_probability}")
    print(f"  Dimensions: {len(score.dimensions)}")
    print(f"  Strengths: {score.strengths[:2]}")
    print(f"  Weaknesses: {score.weaknesses[:2]}")
    print(f"  Tips: {score.optimization_tips[:2]}")

    assert 0 <= score.total_score <= 100, f"Score out of range: {score.total_score}"
    assert score.predicted_pool, "Should have a predicted pool"
    print("  PASS")
    return True


async def run_all_tests():
    """Run all tests and report results."""
    print("\n" + "=" * 60)
    print("RIPPLE 6.0 AUTOMATED TEST SUITE")
    print("=" * 60)

    results = {}

    tests = [
        ("Topic Decomposition", test_topic_decomposition),
        ("Query Builder", test_query_builder),
        ("Relevance Filter", test_relevance_filter),
        ("Search Validator", test_search_validator),
        ("Viral Scorer", test_viral_scorer),
    ]

    for name, test_fn in tests:
        try:
            passed = await test_fn()
            results[name] = "PASS" if passed else "FAIL"
        except Exception as exc:
            results[name] = f"ERROR: {exc}"
            print(f"  ERROR: {exc}")

    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    for name, result in results.items():
        status = "PASS" if result == "PASS" else "FAIL"
        print(f"  [{status}] {name}: {result}")

    passed = sum(1 for v in results.values() if v == "PASS")
    total = len(results)
    print(f"\n  {passed}/{total} tests passed")
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
