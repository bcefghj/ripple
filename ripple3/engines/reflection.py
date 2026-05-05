"""Full-pipeline Reflection Engine — generate-evaluate-improve loop.

Implements the Reflection Pattern across all stages:
- Search Reflection: validates search quality, retries with improved queries
- Analysis Reflection: checks if Agent output has evidence backing
- Content Reflection: evaluates generated content against platform standards

Inspired by ContentEngine's LLM-as-Judge and GPT Researcher's quality validation.
Max 2 iterations per reflection to balance quality vs latency.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Callable

log = logging.getLogger(__name__)


@dataclass
class ReflectionResult:
    final_output: Any
    iterations: int
    quality_scores: list[float] = field(default_factory=list)
    improvements_made: list[str] = field(default_factory=list)
    passed: bool = True


async def reflect_search(
    domain: str,
    search_fn: Callable,
    query_sets: dict[str, list[str]],
    *,
    max_iterations: int = 2,
    min_quality: float = 70.0,
) -> ReflectionResult:
    """Search reflection loop: search → validate → retry if needed.

    Args:
        domain: The content domain being searched
        search_fn: Async function that performs the search given query_sets
        query_sets: Dict of query categories and their query lists
        max_iterations: Max retry attempts
        min_quality: Minimum quality score to pass
    """
    from engines.search_validator import validate_search_quality, generate_retry_queries
    from engines.relevance_filter import filter_by_relevance

    all_results = []
    improvements = []
    scores = []

    for iteration in range(max_iterations + 1):
        raw_results = await search_fn(query_sets)

        all_queries = []
        for qs in query_sets.values():
            all_queries.extend(qs)

        flat_results = []
        if isinstance(raw_results, dict):
            for v in raw_results.values():
                if isinstance(v, list):
                    flat_results.extend(v)
        elif isinstance(raw_results, list):
            flat_results = raw_results

        validation = validate_search_quality(domain, flat_results, min_score=min_quality)
        scores.append(validation.score)

        if validation.passed or iteration == max_iterations:
            filtered = await filter_by_relevance(domain, flat_results)
            all_results = filtered.relevant if filtered.relevant else flat_results
            break

        retry_queries = generate_retry_queries(domain, validation, all_queries)
        if not retry_queries:
            all_results = flat_results
            break

        improvements.append(
            f"第{iteration+1}轮重搜: {'; '.join(validation.diagnostics)} → 新增{len(retry_queries)}个查询"
        )

        for category in query_sets:
            query_sets[category].extend(retry_queries[:5])
            retry_queries = retry_queries[5:]
            if not retry_queries:
                break

        log.info("Search reflection iter %d: score=%.1f, retrying with %d new queries",
                 iteration + 1, validation.score, len(retry_queries))

    return ReflectionResult(
        final_output=all_results,
        iterations=len(scores),
        quality_scores=scores,
        improvements_made=improvements,
        passed=scores[-1] >= min_quality if scores else False,
    )


async def reflect_analysis(
    analysis_text: str,
    search_data_count: int,
    domain: str,
) -> tuple[float, list[str]]:
    """Evaluate analysis quality — check for evidence backing and specificity.

    Returns (quality_score, improvement_suggestions).
    """
    from core.llm import chat_json

    if not analysis_text or len(analysis_text) < 100:
        return 30.0, ["分析内容过短，缺乏深度"]

    messages = [
        {"role": "system", "content": """评估以下分析报告的质量，返回JSON：
{
  "score": 75,
  "has_evidence": true,
  "has_specific_data": true,
  "issues": ["问题1", "问题2"],
  "suggestions": ["改进建议1", "改进建议2"]
}

评分标准（0-100）：
- 是否引用了具体数据/案例 (30分)
- 是否有具体可执行的建议 (25分)
- 是否覆盖多个维度/视角 (20分)
- 语言是否清晰且有洞察力 (15分)
- 是否避免了空洞套话 (10分)"""},
        {"role": "user", "content": f"领域: {domain}\n基于{search_data_count}条数据的分析:\n{analysis_text[:3000]}"},
    ]

    try:
        data = await chat_json(messages, temperature=0.2, max_tokens=512)
        return data.get("score", 60), data.get("suggestions", [])
    except Exception:
        return 60.0, []
