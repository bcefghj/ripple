"""Tencent Hunyuan search-enhanced adapter.

Uses Hunyuan's enable_enhancement to get grounded web search results,
then parses the LLM response into structured SearchResult objects.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass

import httpx

log = logging.getLogger(__name__)

_TIMEOUT = httpx.Timeout(connect=10, read=60, write=10, pool=10)


@dataclass
class HunyuanSearchResult:
    title: str
    url: str
    snippet: str


async def hunyuan_search(query: str) -> list[HunyuanSearchResult]:
    """Use Hunyuan with search enhancement to get grounded results."""
    from core.config import get_settings
    s = get_settings()
    if not s.hunyuan_api_key:
        return []

    headers = {
        "Authorization": f"Bearer {s.hunyuan_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": s.hunyuan_model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "你是搜索助手。用户会给你一个搜索词，请搜索并返回相关结果。"
                    "以JSON数组格式返回，每条包含 title、url、snippet 三个字段。"
                    "至少返回10条结果。只输出JSON，不要其他文字。"
                ),
            },
            {"role": "user", "content": query},
        ],
        "enable_enhancement": True,
        "temperature": 0.1,
        "max_tokens": 4096,
    }

    try:
        url = f"{s.hunyuan_api_base.rstrip('/')}/chat/completions"
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        content = data["choices"][0]["message"]["content"]
        return _parse_results(content)
    except Exception as exc:
        log.warning("Hunyuan search failed for '%s': %s", query[:50], exc)
        return []


async def hunyuan_search_multi(queries: list[str]) -> list[HunyuanSearchResult]:
    """Run multiple Hunyuan searches with EnableEnhancement for grounded results."""
    from core.config import get_settings
    if not get_settings().hunyuan_api_key:
        return []

    results: list[HunyuanSearchResult] = []
    seen: set[str] = set()
    for q in queries[:6]:
        items = await hunyuan_search(q)
        for item in items:
            if item.url not in seen:
                seen.add(item.url)
                results.append(item)
    return results


def _parse_results(text: str) -> list[HunyuanSearchResult]:
    """Best-effort parse of LLM output into search results."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()

    try:
        start = text.find("[")
        end = text.rfind("]") + 1
        if start >= 0 and end > start:
            items = json.loads(text[start:end])
            return [
                HunyuanSearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("snippet", item.get("content", "")),
                )
                for item in items
                if isinstance(item, dict) and item.get("url")
            ]
    except (json.JSONDecodeError, ValueError):
        pass

    results: list[HunyuanSearchResult] = []
    for line in text.split("\n"):
        line = line.strip()
        url_match = re.search(r'https?://\S+', line)
        if url_match:
            results.append(HunyuanSearchResult(
                title=re.sub(r'https?://\S+', '', line).strip()[:100],
                url=url_match.group(),
                snippet=line[:200],
            ))
    return results
