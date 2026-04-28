"""Oracle Scanner - 7 数据源并行扫描

复用旧版 OracleAgent 的真实数据接入逻辑,但适配新的 ReplayNode + Citation 系统。
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import httpx
from loguru import logger

from ..types import Citation


@dataclass
class HotItem:
    """单条热搜/信号"""
    source: str
    title: str
    rank: int
    raw_value: float
    normalized: float
    url: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ScanResult:
    items_by_source: Dict[str, List[HotItem]]
    sources_succeeded: int
    sources_failed: int
    total_ms: int


CN_API_BASE = "https://v2.xxapi.cn/api"

POLYMARKET_GAMMA = "https://gamma-api.polymarket.com"
MANIFOLD_API = "https://api.manifold.markets/v0"
HACKERNEWS_API = "https://hacker-news.firebaseio.com/v0"


async def _fetch_polymarket(client: httpx.AsyncClient) -> List[HotItem]:
    try:
        r = await client.get(
            f"{POLYMARKET_GAMMA}/markets",
            params={"limit": 30, "active": "true", "closed": "false", "order": "volume24hr", "ascending": "false"},
            timeout=20,
        )
        r.raise_for_status()
        data = r.json()
        items = []
        for i, m in enumerate(data[:20]):
            vol = float(m.get("volume24hr", 0) or 0)
            if vol < 1000:
                continue
            items.append(HotItem(
                source="polymarket",
                title=m.get("question", "")[:200],
                rank=i + 1,
                raw_value=vol,
                normalized=min(1.0, vol / 1_000_000),
                url=f"https://polymarket.com/market/{m.get('slug', '')}",
                metadata={"volume24hr": vol, "outcomes": m.get("outcomePrices", "")},
            ))
        return items
    except Exception as e:
        logger.warning(f"Polymarket fetch failed: {e}")
        return []


async def _fetch_manifold(client: httpx.AsyncClient) -> List[HotItem]:
    try:
        r = await client.get(f"{MANIFOLD_API}/markets", params={"limit": 50}, timeout=15)
        r.raise_for_status()
        data = r.json()
        items = []
        for i, m in enumerate(sorted(data, key=lambda x: x.get("volume24Hours", 0), reverse=True)[:15]):
            vol = float(m.get("volume24Hours", 0) or 0)
            if vol < 100:
                continue
            items.append(HotItem(
                source="manifold",
                title=m.get("question", "")[:200],
                rank=i + 1,
                raw_value=vol,
                normalized=min(1.0, vol / 50_000),
                url=m.get("url", ""),
            ))
        return items
    except Exception as e:
        logger.warning(f"Manifold fetch failed: {e}")
        return []


async def _fetch_hackernews(client: httpx.AsyncClient) -> List[HotItem]:
    try:
        r = await client.get(f"{HACKERNEWS_API}/topstories.json", timeout=15)
        r.raise_for_status()
        ids = r.json()[:20]
        item_tasks = [
            client.get(f"{HACKERNEWS_API}/item/{i}.json", timeout=10) for i in ids
        ]
        responses = await asyncio.gather(*item_tasks, return_exceptions=True)
        items = []
        for i, resp in enumerate(responses):
            if isinstance(resp, Exception):
                continue
            d = resp.json()
            score = int(d.get("score", 0))
            if score < 10:
                continue
            items.append(HotItem(
                source="hackernews",
                title=d.get("title", "")[:200],
                rank=i + 1,
                raw_value=float(score),
                normalized=min(1.0, score / 500),
                url=d.get("url", f"https://news.ycombinator.com/item?id={d.get('id')}"),
            ))
        return items
    except Exception as e:
        logger.warning(f"HackerNews fetch failed: {e}")
        return []


def _parse_hot_value(value: Any, fallback: float) -> float:
    """解析中文热度值: 支持 '141万' / '7.5亿' / 数字字符串 / 数字"""
    if isinstance(value, (int, float)):
        return float(value)
    if not isinstance(value, str):
        return fallback
    s = value.strip()
    try:
        if s.endswith("万"):
            return float(s[:-1]) * 10_000
        if s.endswith("亿"):
            return float(s[:-1]) * 100_000_000
        return float(s.replace(",", ""))
    except (ValueError, TypeError):
        return fallback


async def _fetch_cn(client: httpx.AsyncClient, name: str, endpoint: str) -> List[HotItem]:
    try:
        r = await client.get(f"{CN_API_BASE}/{endpoint}", timeout=15)
        r.raise_for_status()
        data = r.json()
        if data.get("code") != 200:
            return []
        items_raw = data.get("data", [])
        items = []
        for i, raw in enumerate(items_raw[:30]):
            if not isinstance(raw, dict):
                continue
            title = raw.get("title", "") or raw.get("name", "") or raw.get("word", "") or raw.get("query", "")
            if not title:
                continue
            hot = _parse_hot_value(raw.get("hot") or raw.get("score") or raw.get("heat"), float(30 - i))
            url = raw.get("url", "") or raw.get("link", "") or raw.get("mobil_url", "")
            items.append(HotItem(
                source=name,
                title=str(title)[:200],
                rank=i + 1,
                raw_value=hot,
                normalized=max(0.0, 1.0 - i / 30),
                url=url,
                metadata={"hot_raw": raw.get("hot")},
            ))
        return items
    except Exception as e:
        logger.warning(f"{name} fetch failed: {e}")
        return []


class OracleScanner:
    """7 数据源并行扫描器"""

    SOURCES = [
        ("polymarket", "polymarket", _fetch_polymarket),
        ("manifold", "manifold", _fetch_manifold),
        ("hackernews", "hackernews", _fetch_hackernews),
        ("weibo", "weibo", lambda c: _fetch_cn(c, "weibo", "weibohot")),
        ("douyin", "douyin", lambda c: _fetch_cn(c, "douyin", "douyinhot")),
        ("baidu", "baidu", lambda c: _fetch_cn(c, "baidu", "baiduhot")),
        ("bilibili", "bilibili", lambda c: _fetch_cn(c, "bilibili", "bilibilihot")),
    ]

    async def scan(self, timeout: int = 30) -> ScanResult:
        start = time.time()
        items_by_source: Dict[str, List[HotItem]] = {}
        succeeded = 0
        failed = 0

        async with httpx.AsyncClient() as client:
            tasks = [fetch(client) for _, _, fetch in self.SOURCES]
            try:
                results = await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True),
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                results = [TimeoutError("scan timeout")] * len(tasks)

            for (name, _, _), result in zip(self.SOURCES, results):
                if isinstance(result, Exception):
                    items_by_source[name] = []
                    failed += 1
                else:
                    items_by_source[name] = result or []
                    if result:
                        succeeded += 1
                    else:
                        failed += 1

        total_ms = int((time.time() - start) * 1000)
        return ScanResult(
            items_by_source=items_by_source,
            sources_succeeded=succeeded,
            sources_failed=failed,
            total_ms=total_ms,
        )

    @staticmethod
    def to_citations(items: List[HotItem]) -> List[Citation]:
        from datetime import datetime
        result = []
        for item in items:
            result.append(Citation(
                url=item.url or f"#{item.source}-{item.rank}",
                title=item.title,
                source_type=item.source if item.source in {
                    "polymarket", "manifold", "hackernews",
                    "weibo", "douyin", "baidu", "bilibili",
                } else "knowledge_base",
                retrieved_at=datetime.utcnow(),
                snippet=f"rank #{item.rank}, value={item.raw_value}",
                confidence=item.normalized,
            ))
        return result


_singleton: Optional[OracleScanner] = None


def get_oracle_scanner() -> OracleScanner:
    global _singleton
    if _singleton is None:
        _singleton = OracleScanner()
    return _singleton
