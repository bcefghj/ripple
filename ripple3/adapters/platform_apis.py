"""Direct platform Web API adapter — no key required.

Fetches hot/trending data directly from platform frontend APIs.
These are the same endpoints the platform websites use internally.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

import httpx

log = logging.getLogger(__name__)

_TIMEOUT = httpx.Timeout(connect=5, read=10, write=5, pool=5)
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9",
}


@dataclass
class PlatformResult:
    title: str
    url: str
    snippet: str
    platform: str
    hot_value: str = ""


async def _fetch_weibo_hot() -> list[PlatformResult]:
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT, headers=_HEADERS) as c:
            resp = await c.get("https://weibo.com/ajax/side/hotSearch")
            data = resp.json()
        results = []
        for item in data.get("data", {}).get("realtime", [])[:30]:
            results.append(PlatformResult(
                title=item.get("word", item.get("note", "")),
                url=f"https://s.weibo.com/weibo?q={item.get('word', '')}",
                snippet=item.get("label_name", ""),
                platform="微博",
                hot_value=str(item.get("num", "")),
            ))
        return results
    except Exception as exc:
        log.warning("Weibo hot fetch failed: %s", exc)
        return []


async def _fetch_zhihu_hot() -> list[PlatformResult]:
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT, headers=_HEADERS) as c:
            resp = await c.get("https://www.zhihu.com/api/v3/feed/topstory/hot-list-web?limit=30")
            data = resp.json()
        results = []
        for item in data.get("data", [])[:30]:
            target = item.get("target", {})
            results.append(PlatformResult(
                title=target.get("title", ""),
                url=f"https://www.zhihu.com/question/{target.get('id', '')}",
                snippet=target.get("excerpt", "")[:200],
                platform="知乎",
                hot_value=str(item.get("detail_text", "")),
            ))
        return results
    except Exception as exc:
        log.warning("Zhihu hot fetch failed: %s", exc)
        return []


async def _fetch_bilibili_hot() -> list[PlatformResult]:
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT, headers=_HEADERS) as c:
            resp = await c.get("https://api.bilibili.com/x/web-interface/popular?ps=30")
            data = resp.json()
        results = []
        for item in data.get("data", {}).get("list", [])[:30]:
            results.append(PlatformResult(
                title=item.get("title", ""),
                url=f"https://www.bilibili.com/video/{item.get('bvid', '')}",
                snippet=item.get("desc", "")[:200],
                platform="B站",
                hot_value=str(item.get("stat", {}).get("view", "")),
            ))
        return results
    except Exception as exc:
        log.warning("Bilibili hot fetch failed: %s", exc)
        return []


async def _fetch_baidu_hot() -> list[PlatformResult]:
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT, headers=_HEADERS) as c:
            resp = await c.get("https://top.baidu.com/api/board?platform=wise&tab=realtime")
            data = resp.json()
        results = []
        cards = data.get("data", {}).get("cards", [])
        if cards:
            for item in cards[0].get("content", [])[:30]:
                results.append(PlatformResult(
                    title=item.get("word", item.get("query", "")),
                    url=item.get("url", item.get("rawUrl", "")),
                    snippet=item.get("desc", "")[:200],
                    platform="百度",
                    hot_value=str(item.get("hotScore", "")),
                ))
        return results
    except Exception as exc:
        log.warning("Baidu hot fetch failed: %s", exc)
        return []


async def _fetch_bilibili_search(keyword: str) -> list[PlatformResult]:
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT, headers=_HEADERS) as c:
            resp = await c.get(
                "https://api.bilibili.com/x/web-interface/wbi/search/all/v2",
                params={"keyword": keyword, "page": 1},
            )
            data = resp.json()
        results = []
        for item in data.get("data", {}).get("result", []):
            if isinstance(item, dict) and item.get("result_type") == "video":
                for v in item.get("data", [])[:10]:
                    title = v.get("title", "").replace('<em class="keyword">', "").replace("</em>", "")
                    results.append(PlatformResult(
                        title=title,
                        url=f"https://www.bilibili.com/video/{v.get('bvid', '')}",
                        snippet=v.get("description", "")[:200],
                        platform="B站搜索",
                    ))
        return results
    except Exception as exc:
        log.warning("Bilibili search failed for '%s': %s", keyword[:50], exc)
        return []


async def fetch_all_platform_hot() -> list[PlatformResult]:
    """Fetch hot/trending from all platforms in parallel."""
    tasks = [
        _fetch_weibo_hot(),
        _fetch_zhihu_hot(),
        _fetch_bilibili_hot(),
        _fetch_baidu_hot(),
    ]
    results_lists = await asyncio.gather(*tasks, return_exceptions=True)

    combined: list[PlatformResult] = []
    for result in results_lists:
        if isinstance(result, list):
            combined.extend(result)
    return combined


async def search_platforms(queries: list[str]) -> list[PlatformResult]:
    """Search across platforms using their web APIs."""
    tasks = [fetch_all_platform_hot()]
    for q in queries[:3]:
        tasks.append(_fetch_bilibili_search(q))

    results_lists = await asyncio.gather(*tasks, return_exceptions=True)
    combined: list[PlatformResult] = []
    seen: set[str] = set()
    for result in results_lists:
        if isinstance(result, list):
            for item in result:
                if item.url not in seen:
                    seen.add(item.url)
                    combined.append(item)
    return combined
