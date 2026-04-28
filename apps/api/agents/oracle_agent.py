"""OracleAgent - 早期信号雷达 v2 (全真实数据)

核心创新:
1. 借鉴 Digital Oracle「资本永远先于舆论」理念
2. 跨平台时差检测: 话题在 A 平台已爆但 B 平台未到 → KOC 的内容窗口
3. 矛盾推理: 不同平台/市场的分歧本身就是最高价值的信号

数据源(全部真实, 无 Mock):
  国际信号层:
    - Polymarket (预测市场, 真金白银交易量)
    - Manifold Markets (社区预测合约)
    - HackerNews (科技/创业先行叙事)
  国内热搜层:
    - 微博热搜 (舆论风向标, 有热度值)
    - 抖音热搜 (短视频生态)
    - 百度热搜 (搜索意图, 有热度值)
    - B站热门 (年轻用户 + 深度内容)
"""

from __future__ import annotations

import asyncio
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import httpx
from loguru import logger


# ============================================================
# 数据结构
# ============================================================

@dataclass
class SignalSample:
    source: str
    keyword: str
    raw_value: float
    normalized: float = 0.0
    delta: float = 0.0
    rank: int = 0
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PlatformPresence:
    """一个话题在某平台上的存在情况"""
    platform: str
    found: bool
    rank: int = 0
    hot_value: float = 0.0
    keyword_matched: str = ""


@dataclass
class CrossPlatformGap:
    """跨平台时差窗口"""
    topic: str
    present_on: List[PlatformPresence]
    absent_on: List[str]
    coverage_ratio: float
    window_days: int
    opportunity: str
    content_angle: str


@dataclass
class Contradiction:
    """矛盾信号"""
    description: str
    platform_a: str
    platform_b: str
    insight: str
    content_suggestion: str


@dataclass
class TrendCandidate:
    topic: str
    category: str
    confidence: float
    horizon_days: int
    evidence: List[SignalSample] = field(default_factory=list)
    explanation: str = ""
    recommended_angle: str = ""
    best_platforms: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    cross_platform_gaps: List[CrossPlatformGap] = field(default_factory=list)
    contradictions: List[Contradiction] = field(default_factory=list)


@dataclass
class OracleReport:
    trends: List[TrendCandidate]
    all_hotlists: Dict[str, List[SignalSample]]
    cross_platform_matrix: Dict[str, Dict[str, Optional[int]]]
    contradictions: List[Contradiction]
    sources_scanned: int
    sources_succeeded: int
    scan_time_ms: int
    generated_at: datetime = field(default_factory=datetime.now)


# ============================================================
# CUSUM + MAD-zscore 算法 (真正使用)
# ============================================================

def mad_zscore(value: float, history: List[float]) -> float:
    if not history or len(history) < 3:
        return 0.0
    median = sorted(history)[len(history) // 2]
    abs_dev = sorted([abs(x - median) for x in history])
    mad = abs_dev[len(abs_dev) // 2]
    if mad == 0:
        return 0.0
    return (value - median) / (1.4826 * mad)


def cusum_alarm(deltas: List[float], kappa: float = 0.5, threshold: float = 3.0) -> bool:
    g = 0.0
    for d in deltas:
        g = max(0.0, g + (d - kappa))
        if g > threshold:
            return True
    return False


# ============================================================
# 真实数据源
# ============================================================

class SignalSourceBase:
    name = "base"
    display_name = "Base"
    platform_type = "unknown"  # "international" or "cn_hot"
    timeout = 12.0

    async def fetch(self, query: str = "") -> List[SignalSample]:
        raise NotImplementedError

    async def fetch_hotlist(self) -> List[SignalSample]:
        """拉取整个热榜(不依赖用户查询)"""
        return await self.fetch("")


class PolymarketSource(SignalSourceBase):
    """Polymarket 预测市场 — 按 24h 交易量排序"""
    name = "polymarket"
    display_name = "Polymarket 预测市场"
    platform_type = "international"
    base_url = "https://gamma-api.polymarket.com"

    async def fetch_hotlist(self) -> List[SignalSample]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(
                    f"{self.base_url}/events",
                    params={
                        "limit": 20,
                        "active": "true",
                        "order": "volume24hr",
                        "ascending": "false",
                    },
                )
                if resp.status_code != 200:
                    return []
                events = resp.json()
                samples = []
                for i, ev in enumerate(events[:20]):
                    title = ev.get("title", "")
                    vol24 = float(ev.get("volume24hr", 0) or 0)
                    vol_total = float(ev.get("volume", 0) or 0)
                    if not title:
                        continue
                    samples.append(SignalSample(
                        source=self.name,
                        keyword=title[:120],
                        raw_value=vol24,
                        normalized=max(0, 1.0 - i * 0.05),
                        rank=i + 1,
                        metadata={
                            "volume_total": vol_total,
                            "slug": ev.get("slug", ""),
                            "url": f"https://polymarket.com/event/{ev.get('slug', '')}",
                        },
                    ))
                return samples
        except Exception as e:
            logger.debug(f"PolymarketSource failed: {e}")
            return []

    async def fetch(self, query: str) -> List[SignalSample]:
        if not query:
            return await self.fetch_hotlist()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(
                    f"{self.base_url}/events",
                    params={
                        "limit": 10,
                        "active": "true",
                        "order": "volume24hr",
                        "ascending": "false",
                    },
                )
                if resp.status_code != 200:
                    return []
                events = resp.json()
                q_lower = query.lower()
                samples = []
                for i, ev in enumerate(events):
                    title = ev.get("title", "")
                    if q_lower in title.lower():
                        vol24 = float(ev.get("volume24hr", 0) or 0)
                        samples.append(SignalSample(
                            source=self.name,
                            keyword=title[:120],
                            raw_value=vol24,
                            normalized=max(0, 1.0 - i * 0.05),
                            rank=i + 1,
                            metadata={
                                "slug": ev.get("slug", ""),
                                "url": f"https://polymarket.com/event/{ev.get('slug', '')}",
                            },
                        ))
                return samples
        except Exception as e:
            logger.debug(f"PolymarketSource search failed: {e}")
            return []


class ManifoldSource(SignalSourceBase):
    """Manifold Markets — 社区预测合约"""
    name = "manifold"
    display_name = "Manifold 预测市场"
    platform_type = "international"
    base_url = "https://api.manifold.markets/v0"

    async def fetch(self, query: str) -> List[SignalSample]:
        if not query:
            query = "trending"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(
                    f"{self.base_url}/search-markets",
                    params={"term": query, "limit": 10, "sort": "24-hour-vol"},
                )
                if resp.status_code != 200:
                    return []
                markets = resp.json()
                samples = []
                for i, m in enumerate(markets[:10]):
                    title = m.get("question", "")
                    vol24 = float(m.get("volume24Hours", 0) or 0)
                    if vol24 > 0:
                        samples.append(SignalSample(
                            source=self.name,
                            keyword=title[:100],
                            raw_value=vol24,
                            normalized=max(0, 1.0 - i * 0.1),
                            rank=i + 1,
                        ))
                return samples
        except Exception as e:
            logger.debug(f"ManifoldSource failed: {e}")
            return []


class HackerNewsSource(SignalSourceBase):
    """HackerNews Top — 科技/创业先行信号"""
    name = "hackernews"
    display_name = "HackerNews"
    platform_type = "international"
    base_url = "https://hacker-news.firebaseio.com/v0"

    async def fetch_hotlist(self) -> List[SignalSample]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(f"{self.base_url}/topstories.json")
                if resp.status_code != 200:
                    return []
                story_ids = resp.json()[:20]

                async def get_story(sid):
                    try:
                        r = await client.get(f"{self.base_url}/item/{sid}.json")
                        return r.json() if r.status_code == 200 else None
                    except Exception:
                        return None

                stories = await asyncio.gather(*[get_story(sid) for sid in story_ids])
                samples = []
                for i, s in enumerate(stories):
                    if not s or not isinstance(s, dict):
                        continue
                    title = s.get("title", "")
                    score = float(s.get("score", 0))
                    samples.append(SignalSample(
                        source=self.name,
                        keyword=title[:120],
                        raw_value=score,
                        normalized=max(0, 1.0 - i * 0.05),
                        rank=i + 1,
                        metadata={"url": s.get("url", "")},
                    ))
                return samples
        except Exception as e:
            logger.debug(f"HackerNewsSource failed: {e}")
            return []

    async def fetch(self, query: str) -> List[SignalSample]:
        return await self.fetch_hotlist()


# ── 国内热搜数据源(全部真实 API) ──

class WeiboHotSource(SignalSourceBase):
    """微博热搜 — 实时热搜榜 + 热度值"""
    name = "weibo"
    display_name = "微博热搜"
    platform_type = "cn_hot"

    async def fetch_hotlist(self) -> List[SignalSample]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get("https://v2.xxapi.cn/api/weibohot")
                if resp.status_code != 200:
                    return []
                data = resp.json()
                items = data.get("data", []) if isinstance(data, dict) else []
                if not isinstance(items, list):
                    return []
                samples = []
                for i, it in enumerate(items[:50]):
                    if not isinstance(it, dict):
                        continue
                    title = it.get("title", it.get("name", ""))
                    hot_str = str(it.get("hot", it.get("hotScore", "0")))
                    hot_val = _parse_hot_value(hot_str)
                    if not title:
                        continue
                    samples.append(SignalSample(
                        source=self.name,
                        keyword=title,
                        raw_value=hot_val,
                        normalized=max(0, 1.0 - i * 0.02),
                        rank=i + 1,
                        metadata={"hot_display": it.get("hot", "")},
                    ))
                return samples
        except Exception as e:
            logger.debug(f"WeiboHotSource failed: {e}")
            return []

    async def fetch(self, query: str) -> List[SignalSample]:
        return await self.fetch_hotlist()


def _parse_hot_value(s: str) -> float:
    """解析 '71万'、'790万'、'33,000' 等热度值"""
    s = s.strip().replace(",", "")
    if not s:
        return 0.0
    if "亿" in s:
        try:
            return float(s.replace("亿", "")) * 1e8
        except ValueError:
            return 0.0
    if "万" in s:
        try:
            return float(s.replace("万", "")) * 1e4
        except ValueError:
            return 0.0
    try:
        return float(s)
    except ValueError:
        return 0.0


class DouyinHotSource(SignalSourceBase):
    """抖音热搜 — 实时热搜词"""
    name = "douyin"
    display_name = "抖音热搜"
    platform_type = "cn_hot"

    async def fetch_hotlist(self) -> List[SignalSample]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get("https://v2.xxapi.cn/api/douyinhot")
                if resp.status_code != 200:
                    return []
                data = resp.json()
                items = data.get("data", []) if isinstance(data, dict) else []
                if not isinstance(items, list):
                    return []
                samples = []
                for i, it in enumerate(items[:50]):
                    title = it.get("word", it.get("title", it.get("name", ""))) if isinstance(it, dict) else str(it)
                    if not title:
                        continue
                    hot_val = float(it.get("hot", it.get("hotScore", 50 - i)) if isinstance(it, dict) else 50 - i)
                    samples.append(SignalSample(
                        source=self.name,
                        keyword=str(title),
                        raw_value=hot_val,
                        normalized=max(0, 1.0 - i * 0.02),
                        rank=i + 1,
                    ))
                return samples
        except Exception as e:
            logger.debug(f"DouyinHotSource failed: {e}")
            return []

    async def fetch(self, query: str) -> List[SignalSample]:
        return await self.fetch_hotlist()


class BaiduHotSource(SignalSourceBase):
    """百度热搜 — 搜索意图信号"""
    name = "baidu"
    display_name = "百度热搜"
    platform_type = "cn_hot"

    async def fetch_hotlist(self) -> List[SignalSample]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get("https://v2.xxapi.cn/api/baiduhot")
                if resp.status_code != 200:
                    return []
                data = resp.json()
                items = data.get("data", []) if isinstance(data, dict) else []
                if not isinstance(items, list):
                    return []
                samples = []
                for i, it in enumerate(items[:50]):
                    if not isinstance(it, dict):
                        continue
                    title = it.get("title", it.get("name", ""))
                    hot_str = str(it.get("hot", it.get("hotScore", "0")))
                    hot_val = _parse_hot_value(hot_str)
                    if not title:
                        continue
                    samples.append(SignalSample(
                        source=self.name,
                        keyword=title,
                        raw_value=hot_val,
                        normalized=max(0, 1.0 - i * 0.02),
                        rank=i + 1,
                        metadata={"hot_display": it.get("hot", "")},
                    ))
                return samples
        except Exception as e:
            logger.debug(f"BaiduHotSource failed: {e}")
            return []

    async def fetch(self, query: str) -> List[SignalSample]:
        return await self.fetch_hotlist()


class BilibiliHotSource(SignalSourceBase):
    """B站热搜 — 年轻用户 + 深度内容信号"""
    name = "bilibili"
    display_name = "B站热搜"
    platform_type = "cn_hot"

    async def fetch_hotlist(self) -> List[SignalSample]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get("https://v2.xxapi.cn/api/bilibilihot")
                if resp.status_code != 200:
                    return []
                data = resp.json()
                items = data.get("data", []) if isinstance(data, dict) else []
                if not isinstance(items, list):
                    return []
                samples = []
                for i, it in enumerate(items[:50]):
                    title = it if isinstance(it, str) else (it.get("title", it.get("name", "")) if isinstance(it, dict) else str(it))
                    if not title:
                        continue
                    samples.append(SignalSample(
                        source=self.name,
                        keyword=str(title),
                        raw_value=float(50 - i),
                        normalized=max(0, 1.0 - i * 0.02),
                        rank=i + 1,
                    ))
                return samples
        except Exception as e:
            logger.debug(f"BilibiliHotSource failed: {e}")
            return []

    async def fetch(self, query: str) -> List[SignalSample]:
        return await self.fetch_hotlist()


# ============================================================
# 跨平台关键词匹配
# ============================================================

def keyword_match(query: str, candidate: str, threshold: float = 0.5) -> bool:
    """模糊关键词匹配 (中英文兼容)

    策略:
    1. 精确子串: "五一旅游" in "五一旅游攻略" → True
    2. 中文 bigram 匹配: 把"五一旅游"拆成"五一"和"旅游", 都出现在候选中 → True
    3. 字符重叠(宽松): overlap >= threshold
    """
    q = query.lower().strip()
    c = candidate.lower().strip()
    if not q or not c:
        return False
    if q in c or c in q:
        return True

    if any("\u4e00" <= ch <= "\u9fff" for ch in q):
        tokens = _chinese_ngrams(q)
        if tokens and len(tokens) >= 2:
            matched = sum(1 for t in tokens if t in c)
            if matched / len(tokens) >= threshold:
                return True

    q_chars = set(q.replace(" ", ""))
    c_chars = set(c.replace(" ", ""))
    if not q_chars:
        return False
    overlap = len(q_chars & c_chars) / len(q_chars)
    return overlap >= threshold


def _chinese_ngrams(text: str, min_len: int = 2) -> List[str]:
    """简单中文分词: 提取所有连续中文字符子串(bigram 级)"""
    tokens = []
    buf = []
    for ch in text:
        if "\u4e00" <= ch <= "\u9fff":
            buf.append(ch)
        else:
            if len(buf) >= min_len:
                tokens.append("".join(buf))
            buf = []
    if len(buf) >= min_len:
        tokens.append("".join(buf))
    return tokens


def find_topic_in_hotlist(
    topic_keywords: List[str],
    hotlist: List[SignalSample],
) -> Optional[SignalSample]:
    """在热榜中查找匹配的话题"""
    for kw in topic_keywords:
        for sample in hotlist:
            if keyword_match(kw, sample.keyword):
                return sample
    return None


# ============================================================
# 矛盾推理 (基于真实数据)
# ============================================================

def find_contradictions(
    hotlists: Dict[str, List[SignalSample]],
    topic_keywords: List[str],
) -> List[Contradiction]:
    """基于真实热搜数据寻找跨平台矛盾"""
    contradictions = []

    presence: Dict[str, Optional[SignalSample]] = {}
    for platform, samples in hotlists.items():
        presence[platform] = find_topic_in_hotlist(topic_keywords, samples)

    cn_platforms = ["weibo", "douyin", "baidu", "bilibili"]
    intl_platforms = ["polymarket", "manifold", "hackernews"]

    cn_found = {p: presence.get(p) for p in cn_platforms if presence.get(p)}
    intl_found = {p: presence.get(p) for p in intl_platforms if presence.get(p)}

    if intl_found and not cn_found:
        intl_details = ", ".join(
            f"{p}(#{s.rank})" for p, s in intl_found.items()
        )
        contradictions.append(Contradiction(
            description=f"国际预测市场已有信号({intl_details}), 但国内热搜尚未覆盖",
            platform_a="国际市场",
            platform_b="国内热搜",
            insight="信息差窗口 5-7 天: 国际市场已经在交易这个话题, 国内讨论尚未启动",
            content_suggestion="做「国外都在讨论…」「Polymarket 上 XX 万美元在押注…」类跨文化解读内容, 信息差红利显著",
        ))

    if cn_found and not intl_found:
        cn_details = ", ".join(f"{p}(#{s.rank})" for p, s in cn_found.items())
        contradictions.append(Contradiction(
            description=f"国内热搜已爆({cn_details}), 但国际预测市场无对应合约",
            platform_a="国内热搜",
            platform_b="国际市场",
            insight="纯本土话题, 无国际参照, 需快速跟进",
            content_suggestion="聚焦国内用户共鸣点, 做接地气的本土解读",
        ))

    found_cn_names = set(cn_found.keys())
    not_found_cn = [p for p in cn_platforms if p not in found_cn_names]

    if found_cn_names and not_found_cn:
        found_str = ", ".join(
            f"{p}(#{cn_found[p].rank})" for p in found_cn_names
        )
        absent_str = ", ".join(not_found_cn)
        platform_lag = {
            "douyin": ("抖音", "短视频内容", 2),
            "bilibili": ("B站", "深度视频内容", 3),
            "baidu": ("百度搜索", "教程/问答类内容", 2),
            "weibo": ("微博", "话题讨论/观点输出", 1),
        }
        for absent_p in not_found_cn:
            if absent_p in platform_lag:
                p_cn, content_type, days = platform_lag[absent_p]
                contradictions.append(Contradiction(
                    description=f"话题在 {found_str} 已上榜, 但{p_cn}尚未出现",
                    platform_a=found_str,
                    platform_b=p_cn,
                    insight=f"跨平台时差窗口约 {days}-{days+2} 天",
                    content_suggestion=f"抓紧在{p_cn}布局{content_type}, 抢占先发优势",
                ))

    return contradictions


# ============================================================
# 主 OracleAgent
# ============================================================

class OracleAgent:
    """早期信号雷达 v2 — 全真实数据 + 跨平台时差检测 + 矛盾推理"""

    def __init__(self):
        self.sources: List[SignalSourceBase] = [
            PolymarketSource(),
            ManifoldSource(),
            HackerNewsSource(),
            WeiboHotSource(),
            DouyinHotSource(),
            BaiduHotSource(),
            BilibiliHotSource(),
        ]

    async def scan(
        self,
        topic_seed: str,
        category: str = "通用",
        target_platforms: Optional[List[str]] = None,
    ) -> OracleReport:
        start_time = time.time()
        target_platforms = target_platforms or ["channels", "xhs", "douyin"]

        topic_keywords = self._extract_keywords(topic_seed)

        results = await asyncio.gather(
            *[s.fetch_hotlist() for s in self.sources],
            return_exceptions=True,
        )

        all_hotlists: Dict[str, List[SignalSample]] = {}
        all_samples: List[SignalSample] = []
        succeeded = 0

        for source, result in zip(self.sources, results):
            if isinstance(result, Exception):
                logger.warning(f"[Oracle] {source.display_name} 失败: {result}")
                all_hotlists[source.name] = []
                continue
            if isinstance(result, list) and len(result) > 0:
                all_hotlists[source.name] = result
                all_samples.extend(result)
                succeeded += 1
                logger.debug(f"[Oracle] {source.display_name}: {len(result)} 条")
            else:
                all_hotlists[source.name] = []
                logger.debug(f"[Oracle] {source.display_name}: 空数据")

        cross_matrix = self._build_cross_platform_matrix(topic_keywords, all_hotlists)
        contradictions = find_contradictions(all_hotlists, topic_keywords)
        trends = self._aggregate_trends(
            topic_seed, topic_keywords, all_hotlists, all_samples,
            contradictions, category, target_platforms,
        )

        scan_time_ms = int((time.time() - start_time) * 1000)

        return OracleReport(
            trends=trends,
            all_hotlists=all_hotlists,
            cross_platform_matrix=cross_matrix,
            contradictions=contradictions,
            sources_scanned=len(self.sources),
            sources_succeeded=succeeded,
            scan_time_ms=scan_time_ms,
        )

    def _extract_keywords(self, topic_seed: str) -> List[str]:
        """从话题种子提取多个搜索关键词"""
        keywords = [topic_seed]
        for sep in ["，", ",", "、", " "]:
            if sep in topic_seed:
                keywords.extend([w.strip() for w in topic_seed.split(sep) if len(w.strip()) >= 2])
        if len(topic_seed) > 8:
            mid = len(topic_seed) // 2
            keywords.append(topic_seed[:mid])
            keywords.append(topic_seed[mid:])
        return list(set(keywords))

    def _build_cross_platform_matrix(
        self,
        topic_keywords: List[str],
        hotlists: Dict[str, List[SignalSample]],
    ) -> Dict[str, Dict[str, Optional[int]]]:
        """构建跨平台覆盖矩阵"""
        matrix: Dict[str, Dict[str, Optional[int]]] = {}
        for kw in topic_keywords[:5]:
            row: Dict[str, Optional[int]] = {}
            for platform, samples in hotlists.items():
                match = find_topic_in_hotlist([kw], samples)
                row[platform] = match.rank if match else None
            matrix[kw] = row
        return matrix

    def _aggregate_trends(
        self,
        topic_seed: str,
        topic_keywords: List[str],
        hotlists: Dict[str, List[SignalSample]],
        all_samples: List[SignalSample],
        contradictions: List[Contradiction],
        category: str,
        target_platforms: List[str],
    ) -> List[TrendCandidate]:
        trends = []

        direct_matches: Dict[str, List[SignalSample]] = {}
        for kw in topic_keywords:
            for platform, samples in hotlists.items():
                match = find_topic_in_hotlist([kw], samples)
                if match:
                    direct_matches.setdefault(kw, []).append(match)

        if direct_matches:
            best_kw = max(direct_matches, key=lambda k: len(direct_matches[k]))
            evidence = direct_matches[best_kw]
            unique_sources = set(s.source for s in evidence)
            source_diversity = len(unique_sources) / len(self.sources)
            avg_norm = sum(s.normalized for s in evidence) / len(evidence)

            norm_values = [s.normalized for s in evidence]
            cusum_boost = 0.05 if cusum_alarm([v * 10 for v in norm_values]) else 0.0
            z = mad_zscore(norm_values[-1], norm_values) if len(norm_values) >= 3 else 0
            zscore_boost = min(0.1, abs(z) * 0.02) if z > 1.5 else 0.0

            confidence = min(1.0,
                0.35 * source_diversity
                + 0.35 * avg_norm
                + 0.15 * min(1.0, len(evidence) / 3)
                + cusum_boost + zscore_boost
            )
            horizon_days = max(1, int(7 * (1 - confidence)))

            present_str = ", ".join(f"{s.source}(#{s.rank})" for s in evidence)
            absent = [s.name for s in self.sources if s.name not in unique_sources]

            trends.append(TrendCandidate(
                topic=best_kw,
                category=category,
                confidence=confidence,
                horizon_days=horizon_days,
                evidence=evidence,
                explanation=f"在 {len(unique_sources)} 个平台命中: {present_str}. 未出现平台: {', '.join(absent[:3])}",
                recommended_angle=self._suggest_angle(unique_sources, contradictions),
                best_platforms=target_platforms[:3],
                risks=self._assess_risks(confidence, unique_sources),
                contradictions=contradictions,
            ))

        top_intl = self._find_intl_opportunities(hotlists, topic_keywords)
        for t in top_intl:
            if not any(existing.topic == t.topic for existing in trends):
                trends.append(t)

        top_cn_gaps = self._find_cn_platform_gaps(hotlists)
        for t in top_cn_gaps:
            if not any(existing.topic == t.topic for existing in trends):
                trends.append(t)

        trends.sort(key=lambda t: t.confidence, reverse=True)
        return trends[:10]

    def _find_intl_opportunities(
        self,
        hotlists: Dict[str, List[SignalSample]],
        topic_keywords: List[str],
    ) -> List[TrendCandidate]:
        """发现国际市场有但国内没有的话题(跨国信息差)"""
        opportunities = []
        pm_samples = hotlists.get("polymarket", [])
        cn_all_keywords = set()
        for p in ["weibo", "douyin", "baidu", "bilibili"]:
            for s in hotlists.get(p, []):
                cn_all_keywords.add(s.keyword.lower())

        for sample in pm_samples[:10]:
            title_lower = sample.keyword.lower()
            found_in_cn = any(
                keyword_match(word, cn_kw, 0.4)
                for word in title_lower.split()
                if len(word) > 3
                for cn_kw in list(cn_all_keywords)[:100]
            )
            if not found_in_cn and sample.raw_value > 100000:
                opportunities.append(TrendCandidate(
                    topic=sample.keyword,
                    category="国际热点",
                    confidence=min(0.85, 0.3 + sample.normalized * 0.5),
                    horizon_days=5,
                    evidence=[sample],
                    explanation=f"Polymarket 24h 交易量 ${sample.raw_value:,.0f}, 国内热搜零覆盖",
                    recommended_angle="跨文化解读: 「国外都在讨论…但国内还没人关注」",
                    best_platforms=["channels", "wechat_official"],
                    risks=["话题可能不适合国内传播", "翻译/文化差异需注意"],
                ))

        return opportunities[:3]

    def _find_cn_platform_gaps(
        self,
        hotlists: Dict[str, List[SignalSample]],
    ) -> List[TrendCandidate]:
        """发现在部分国内平台上热但其他平台还没到的话题"""
        gaps = []
        cn_platforms = ["weibo", "douyin", "baidu", "bilibili"]

        for src_platform in cn_platforms:
            src_list = hotlists.get(src_platform, [])
            for sample in src_list[:10]:
                present_in = [src_platform]
                absent_from = []
                for other_p in cn_platforms:
                    if other_p == src_platform:
                        continue
                    other_list = hotlists.get(other_p, [])
                    match = find_topic_in_hotlist([sample.keyword], other_list)
                    if match:
                        present_in.append(other_p)
                    else:
                        absent_from.append(other_p)

                if len(present_in) == 1 and absent_from and sample.rank <= 10:
                    gaps.append(TrendCandidate(
                        topic=sample.keyword,
                        category="跨平台时差",
                        confidence=min(0.7, 0.4 + sample.normalized * 0.3),
                        horizon_days=3,
                        evidence=[sample],
                        explanation=f"仅在{src_platform}热搜#{sample.rank}, 但{'/'.join(absent_from)}均未出现 → 内容窗口期 2-4 天",
                        recommended_angle=f"从{src_platform}热度切入, 抢先布局{'/'.join(absent_from)}",
                        best_platforms=absent_from[:2],
                        risks=["话题可能是平台特有不具跨平台传播性"],
                    ))

        gaps.sort(key=lambda t: t.evidence[0].rank if t.evidence else 99)
        return gaps[:5]

    def _suggest_angle(self, sources: set, contradictions: List[Contradiction]) -> str:
        if contradictions:
            return contradictions[0].content_suggestion
        if "polymarket" in sources or "manifold" in sources:
            return "国际视角解读 / 数据驱动分析"
        elif "hackernews" in sources:
            return "科技圈前沿 / 极客视角"
        elif "weibo" in sources and "douyin" not in sources:
            return "微博热议扩展到短视频 / 深度解读"
        elif "douyin" in sources and "weibo" not in sources:
            return "抖音热点扩展到图文 / 详细教程"
        return "多角度深度分析"

    def _assess_risks(self, confidence: float, sources: set) -> List[str]:
        risks = []
        if confidence < 0.4:
            risks.append("置信度较低, 建议先做小范围测试")
        if len(sources) < 2:
            risks.append("信号源不足 2 个, 可能是偶发噪声")
        if len(sources) >= 4:
            risks.append("多平台已覆盖, 竞争可能激烈, 需差异化角度")
        return risks

    def format_report(self, report: OracleReport, topic_seed: str) -> str:
        """将 OracleReport 格式化为可注入 prompt 的结构化文本"""
        lines = []
        lines.append("=" * 60)
        lines.append("RIPPLE 早期信号雷达报告")
        lines.append(f"话题: {topic_seed}")
        lines.append(f"扫描时间: {report.generated_at.strftime('%Y-%m-%d %H:%M')}")
        lines.append(f"数据源: {report.sources_succeeded}/{report.sources_scanned} 个成功")
        lines.append(f"耗时: {report.scan_time_ms}ms")
        lines.append("=" * 60)

        lines.append("\n## 各平台实时数据")
        for platform, samples in report.all_hotlists.items():
            source_obj = next((s for s in self.sources if s.name == platform), None)
            display = source_obj.display_name if source_obj else platform
            if samples:
                top3 = ", ".join(f"#{s.rank}{s.keyword[:20]}" for s in samples[:3])
                lines.append(f"  {display}: {len(samples)} 条 | Top3: {top3}")
            else:
                lines.append(f"  {display}: 无数据")

        if report.cross_platform_matrix:
            lines.append("\n## 跨平台覆盖矩阵(话题在各平台的排名, 空=未出现)")
            platforms = list(report.all_hotlists.keys())
            header = "关键词".ljust(20) + " | ".join(p.ljust(10) for p in platforms)
            lines.append(f"  {header}")
            lines.append(f"  {'─' * len(header)}")
            for kw, row in report.cross_platform_matrix.items():
                vals = []
                for p in platforms:
                    rank = row.get(p)
                    vals.append(f"#{rank}".ljust(10) if rank else "—".ljust(10))
                lines.append(f"  {kw[:20].ljust(20)}{' | '.join(vals)}")

        if report.contradictions:
            lines.append("\n## 矛盾信号(高价值洞察)")
            for i, c in enumerate(report.contradictions, 1):
                lines.append(f"  [{i}] {c.description}")
                lines.append(f"      洞察: {c.insight}")
                lines.append(f"      内容建议: {c.content_suggestion}")

        if report.trends:
            lines.append("\n## 趋势候选(按置信度排序)")
            for i, t in enumerate(report.trends[:5], 1):
                lines.append(f"  [{i}] [{t.confidence:.0%}] {t.topic[:50]}")
                lines.append(f"      类别: {t.category} | 窗口期: {t.horizon_days} 天")
                lines.append(f"      依据: {t.explanation[:100]}")
                lines.append(f"      推荐角度: {t.recommended_angle}")
                if t.risks:
                    lines.append(f"      风险: {'; '.join(t.risks)}")

        lines.append("\n" + "=" * 60)
        return "\n".join(lines)
