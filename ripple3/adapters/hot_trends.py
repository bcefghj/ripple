"""Hot trends adapter — uses DailyHotApi + direct platform APIs.

Replaces the old xxapi.cn with more reliable data sources:
1. DailyHotApi (3,700+ stars, 40+ platforms)
2. Direct platform web APIs as fallback
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

log = logging.getLogger(__name__)

PLATFORMS = {
    "weibo": {"name": "微博热搜"},
    "douyin": {"name": "抖音热搜"},
    "zhihu": {"name": "知乎热榜"},
    "bilibili": {"name": "B站热门"},
    "baidu": {"name": "百度热搜"},
    "toutiao": {"name": "今日头条"},
    "36kr": {"name": "36氪"},
    "sspai": {"name": "少数派"},
    "ithome": {"name": "IT之家"},
    "juejin": {"name": "掘金"},
}


@dataclass
class TrendItem:
    title: str
    hot_value: str
    platform: str
    url: str = ""
    rank: int = 0


async def fetch_platform_trends(platform: str, *, limit: int = 20) -> list[TrendItem]:
    """Fetch trending topics from a single platform via DailyHotApi, fallback to direct API."""
    from adapters.dailyhot_adapter import fetch_platform as _dailyhot_fetch
    items = await _dailyhot_fetch(platform)

    if not items:
        items = await _fallback_platform(platform)

    info = PLATFORMS.get(platform, {"name": platform})
    results = []
    for i, item in enumerate(items[:limit]):
        results.append(TrendItem(
            title=getattr(item, "title", ""),
            hot_value=getattr(item, "hot_value", str(getattr(item, "hot_value", ""))),
            platform=info["name"],
            url=getattr(item, "url", ""),
            rank=i + 1,
        ))
    return results


async def _fallback_platform(platform: str) -> list:
    """Fallback to direct platform APIs if DailyHotApi fails."""
    try:
        from adapters.platform_apis import (
            _fetch_weibo_hot, _fetch_zhihu_hot,
            _fetch_bilibili_hot, _fetch_baidu_hot,
        )
        dispatch = {
            "weibo": _fetch_weibo_hot,
            "zhihu": _fetch_zhihu_hot,
            "bilibili": _fetch_bilibili_hot,
            "baidu": _fetch_baidu_hot,
        }
        fn = dispatch.get(platform)
        if fn:
            return await fn()
    except Exception as exc:
        log.warning("Fallback fetch for %s failed: %s", platform, exc)
    return []


async def fetch_all_trends(*, limit_per_platform: int = 15) -> dict[str, list[TrendItem]]:
    """Fetch trending topics from all platforms in parallel."""
    results: dict[str, list[TrendItem]] = {}

    async def _fetch(platform: str):
        items = await fetch_platform_trends(platform, limit=limit_per_platform)
        results[platform] = items

    await asyncio.gather(
        *[_fetch(p) for p in PLATFORMS],
        return_exceptions=True,
    )
    return results


def format_trends_for_llm(trends: dict[str, list[TrendItem]], *, max_per_platform: int = 10) -> str:
    """Format trending data into a string for LLM consumption."""
    parts = []
    for platform, items in trends.items():
        if not items:
            continue
        info = PLATFORMS.get(platform, {"name": platform})
        lines = [f"  {item.rank}. {item.title} (热度: {item.hot_value})" for item in items[:max_per_platform]]
        parts.append(f"【{info['name']}】\n" + "\n".join(lines))
    return "\n\n".join(parts) if parts else "（未获取到热搜数据）"
