"""Hot trends aggregation adapter — multi-source fallback.

Tries multiple free hot-trend APIs in order:
1. api.zxki.cn (stable, JSON)
2. DailyHotApi self-hosted (if configured)
3. Direct platform APIs (fallback)
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

import httpx

log = logging.getLogger(__name__)

_TIMEOUT = httpx.Timeout(connect=5, read=10, write=5, pool=5)

PLATFORM_ENDPOINTS = {
    "weibo": "微博热搜",
    "douyin": "抖音热点",
    "bilibili": "B站热门",
    "zhihu": "知乎热榜",
    "baidu": "百度热搜",
    "kuaishou": "快手热搜",
    "toutiao": "今日头条",
    "36kr": "36氪",
}

_ZXKI_TYPE_MAP = {
    "weibo": "weibo",
    "douyin": "douyin",
    "bilibili": "bilibili",
    "zhihu": "zhihu",
    "baidu": "baidu",
    "kuaishou": "kuaishou",
    "toutiao": "toutiao",
    "36kr": "36kr",
}


@dataclass
class DailyHotItem:
    title: str
    url: str
    hot_value: str
    platform: str
    rank: int = 0


async def _fetch_zxki(platform: str) -> list[DailyHotItem]:
    """Fetch from api.zxki.cn — stable free hot-trend API."""
    type_key = _ZXKI_TYPE_MAP.get(platform, platform)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(
                "https://api.zxki.cn/api/jhrs",
                params={"type": type_key},
            )
            resp.raise_for_status()
            data = resp.json()

        if not data.get("success"):
            return []

        platform_name = PLATFORM_ENDPOINTS.get(platform, platform)
        results = []
        for i, item in enumerate(data.get("data", [])[:30]):
            if isinstance(item, dict):
                results.append(DailyHotItem(
                    title=item.get("title", item.get("name", "")),
                    url=item.get("url", item.get("mobilUrl", "")),
                    hot_value=str(item.get("hot", item.get("hotValue", ""))),
                    platform=platform_name,
                    rank=i + 1,
                ))
        return results
    except Exception as exc:
        log.debug("zxki.cn %s failed: %s", platform, exc)
        return []


async def _fetch_dailyhot_api(platform: str, base_url: str) -> list[DailyHotItem]:
    """Fetch from DailyHotApi (self-hosted or public)."""
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(f"{base_url}/{platform}/")
            resp.raise_for_status()

            ct = resp.headers.get("content-type", "")
            if "json" not in ct:
                return []

            data = resp.json()

        items_data = data.get("data", [])
        if not isinstance(items_data, list):
            return []

        platform_name = PLATFORM_ENDPOINTS.get(platform, platform)
        results = []
        for i, item in enumerate(items_data[:30]):
            if isinstance(item, dict):
                results.append(DailyHotItem(
                    title=item.get("title", item.get("name", "")),
                    url=item.get("url", item.get("mobileUrl", "")),
                    hot_value=str(item.get("hot", item.get("hotValue", ""))),
                    platform=platform_name,
                    rank=i + 1,
                ))
        return results
    except Exception as exc:
        log.debug("DailyHotApi %s failed: %s", platform, exc)
        return []


async def fetch_platform(platform: str, base_url: str = "") -> list[DailyHotItem]:
    """Fetch trending items with multi-source fallback."""
    results = await _fetch_zxki(platform)
    if results:
        return results

    from core.config import get_settings
    dh_base = base_url or get_settings().dailyhot_api_base
    if dh_base:
        results = await _fetch_dailyhot_api(platform, dh_base)
        if results:
            return results

    return []


async def fetch_all_hot(platforms: list[str] | None = None) -> dict[str, list[DailyHotItem]]:
    """Fetch hot trends from all platforms in parallel."""
    if platforms is None:
        platforms = list(PLATFORM_ENDPOINTS.keys())

    results: dict[str, list[DailyHotItem]] = {}

    async def _fetch(p: str):
        items = await fetch_platform(p)
        results[p] = items

    await asyncio.gather(*[_fetch(p) for p in platforms], return_exceptions=True)
    return results


async def fetch_hot_flat(platforms: list[str] | None = None) -> list[DailyHotItem]:
    """Fetch all hot items as a flat list."""
    data = await fetch_all_hot(platforms)
    combined = []
    for items in data.values():
        combined.extend(items)
    return combined
