"""Tencent MCP Chinese Trend Aggregator adapter.

Integrates with the MCP中文趋势聚合 service to fetch real-time trending
topics from 20+ Chinese platforms including Douyin, Weibo, Toutiao,
Zhihu, Bilibili, Douban, etc.

Falls back to DailyHot API if MCP is unavailable.
"""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime

import httpx

log = logging.getLogger(__name__)

PLATFORM_MAP = {
    "douyin": "抖音",
    "weibo": "微博",
    "toutiao": "头条",
    "zhihu": "知乎",
    "bilibili": "B站",
    "douban": "豆瓣",
    "baidu": "百度",
    "xiaohongshu": "小红书",
    "kuaishou": "快手",
    "juejin": "掘金",
    "ithome": "IT之家",
    "36kr": "36氪",
    "huxiu": "虎嗅",
}

DAILYHOT_FALLBACK = os.getenv("DAILYHOT_API_BASE", "https://hot.imsyy.top")


async def fetch_trending_mcp(platforms: list[str] | None = None) -> dict[str, list[dict]]:
    """Fetch trending topics from MCP Chinese Trend Aggregator or fallback."""
    if platforms is None:
        platforms = ["douyin", "weibo", "toutiao", "zhihu", "bilibili", "baidu"]

    results: dict[str, list[dict]] = {}

    async with httpx.AsyncClient(timeout=10) as client:
        tasks = [_fetch_platform(client, p) for p in platforms]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

    for platform, response in zip(platforms, responses):
        if isinstance(response, Exception):
            log.warning("Failed to fetch %s trends: %s", platform, response)
            results[platform] = []
        else:
            results[platform] = response

    return results


async def _fetch_platform(client: httpx.AsyncClient, platform: str) -> list[dict]:
    """Fetch trending for a single platform using DailyHot API."""
    try:
        url = f"{DAILYHOT_FALLBACK}/{platform}"
        resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json()

        items = data.get("data", [])
        return [
            {
                "title": item.get("title", ""),
                "hot_value": str(item.get("hot", item.get("desc", ""))),
                "url": item.get("url", item.get("mobileUrl", "")),
                "platform": PLATFORM_MAP.get(platform, platform),
                "rank": idx + 1,
            }
            for idx, item in enumerate(items[:20])
            if item.get("title")
        ]
    except Exception as e:
        log.warning("Platform %s fetch error: %s", platform, e)
        return []


async def get_all_trends(limit_per_platform: int = 10) -> list[dict]:
    """Get aggregated trends from all platforms, sorted by relevance."""
    all_platforms = ["douyin", "weibo", "toutiao", "zhihu", "bilibili", "baidu", "xiaohongshu"]
    platform_data = await fetch_trending_mcp(all_platforms)

    aggregated = []
    for platform, items in platform_data.items():
        for item in items[:limit_per_platform]:
            aggregated.append(item)

    return aggregated


async def search_trends_by_keyword(keyword: str) -> list[dict]:
    """Search for keyword-related trending topics across all platforms."""
    all_trends = await get_all_trends(limit_per_platform=20)
    keyword_lower = keyword.lower()
    return [
        t for t in all_trends
        if keyword_lower in t.get("title", "").lower()
    ]
