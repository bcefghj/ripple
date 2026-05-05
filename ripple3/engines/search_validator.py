"""Search Quality Validator — self-testing loop with automatic retry.

Implements the Reflection Pattern for search: after each search round,
validates quality metrics. If below threshold, diagnoses the issue and
generates improved queries for a retry (max 2 iterations).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

log = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    passed: bool
    score: float  # 0-100
    relevance_rate: float
    diversity_score: float
    freshness_rate: float
    density_rate: float
    diagnostics: list[str] = field(default_factory=list)
    retry_suggestions: list[str] = field(default_factory=list)


def validate_search_quality(
    domain: str,
    results: list,
    min_score: float = 70.0,
) -> ValidationResult:
    """Evaluate search result quality across 4 dimensions.

    Dimensions:
    1. Relevance (40%): % of titles containing domain keywords
    2. Diversity (20%): number of distinct source domains
    3. Freshness (20%): % with date info suggesting recent content
    4. Density (20%): % with non-empty, meaningful snippets
    """
    if not results:
        return ValidationResult(
            passed=False, score=0, relevance_rate=0,
            diversity_score=0, freshness_rate=0, density_rate=0,
            diagnostics=["无搜索结果"],
            retry_suggestions=[f"使用更具体的关键词搜索 {domain}"],
        )

    total = len(results)

    # 1. Relevance check
    domain_words = [w for w in domain.replace("领域", "").split() if len(w) > 1]
    if not domain_words:
        domain_words = [domain]

    relevant_count = 0
    for r in results:
        text = f"{r.title} {r.snippet}".lower()
        if any(w.lower() in text for w in domain_words):
            relevant_count += 1
    relevance_rate = relevant_count / total

    # 2. Diversity check
    domains_seen: set[str] = set()
    for r in results:
        url = getattr(r, "url", "")
        if url:
            parts = url.split("/")
            if len(parts) >= 3:
                domains_seen.add(parts[2])
    diversity_score = min(len(domains_seen) / 10, 1.0)

    # 3. Freshness check
    fresh_keywords = ["2026", "2025", "最新", "今日", "近期", "本周", "本月"]
    fresh_count = sum(
        1 for r in results
        if any(kw in f"{r.title} {r.snippet} {getattr(r, 'date', '')}" for kw in fresh_keywords)
    )
    freshness_rate = fresh_count / total

    # 4. Information density
    dense_count = sum(
        1 for r in results
        if len(getattr(r, "snippet", "")) > 30
    )
    density_rate = dense_count / total

    score = (
        relevance_rate * 40 +
        diversity_score * 20 +
        freshness_rate * 20 +
        density_rate * 20
    )

    diagnostics = []
    retry_suggestions = []

    if relevance_rate < 0.5:
        diagnostics.append(f"相关性不足: 仅 {relevance_rate:.0%} 内容与「{domain}」相关")
        retry_suggestions.append(f"增加更具体的子领域关键词")
        retry_suggestions.append(f"使用 site: 限定到相关平台")

    if diversity_score < 0.5:
        diagnostics.append(f"来源单一: 仅 {len(domains_seen)} 个不同来源")
        retry_suggestions.append("增加不同搜索引擎的查询")

    if freshness_rate < 0.2:
        diagnostics.append(f"内容陈旧: 仅 {freshness_rate:.0%} 为近期内容")
        retry_suggestions.append("在查询中添加时间限定词")

    if density_rate < 0.6:
        diagnostics.append(f"信息稀疏: {(1-density_rate):.0%} 摘要为空或过短")

    passed = score >= min_score

    log.info(
        "Search validation [%s]: score=%.1f (%s) | relevance=%.0f%% diversity=%.0f%% fresh=%.0f%% dense=%.0f%%",
        domain, score, "PASS" if passed else "FAIL",
        relevance_rate * 100, diversity_score * 100,
        freshness_rate * 100, density_rate * 100,
    )

    return ValidationResult(
        passed=passed,
        score=score,
        relevance_rate=relevance_rate,
        diversity_score=diversity_score,
        freshness_rate=freshness_rate,
        density_rate=density_rate,
        diagnostics=diagnostics,
        retry_suggestions=retry_suggestions,
    )


def generate_retry_queries(domain: str, validation: ValidationResult, existing_queries: list[str]) -> list[str]:
    """Generate improved queries based on validation diagnostics."""
    new_queries: list[str] = []

    if validation.relevance_rate < 0.5:
        new_queries.extend([
            f"{domain} 专业 内容",
            f"{domain} 垂直 领域",
            f"{domain} 核心 话题",
            f"site:bilibili.com {domain} 测评",
            f"site:xiaohongshu.com {domain} 分享",
        ])

    if validation.diversity_score < 0.5:
        new_queries.extend([
            f"{domain} 公众号 推荐",
            f"{domain} 知乎 讨论",
            f"{domain} 微博 话题",
        ])

    if validation.freshness_rate < 0.2:
        from datetime import datetime
        month = datetime.now().month
        year = datetime.now().year
        new_queries.extend([
            f"{domain} {year}年{month}月",
            f"{domain} 最新动态",
            f"{domain} 近期 热点",
        ])

    seen = set(existing_queries)
    return [q for q in new_queries if q not in seen]
