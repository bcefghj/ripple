"""Topic Decomposition Engine — breaks broad domains into searchable sub-topics.

Inspired by Nexus Agents' Topic Decomposer and GPT Researcher's Planner Agent.
Instead of searching "数码科技" directly, decomposes it into specific sub-topics,
KOLs, platforms, and trending angles for targeted high-relevance searches.

Ripple 6.1: Added query type classification to avoid over-decomposing specific
event queries (e.g. "谢娜成都演唱会") into broad domain searches.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

from core.llm import chat_json

log = logging.getLogger(__name__)


@dataclass
class TopicTree:
    domain: str
    sub_domains: list[str] = field(default_factory=list)
    trending_topics: list[str] = field(default_factory=list)
    key_kols: list[str] = field(default_factory=list)
    platform_angles: dict[str, str] = field(default_factory=dict)
    audience_segments: list[str] = field(default_factory=list)
    content_formats: list[str] = field(default_factory=list)
    search_queries: list[str] = field(default_factory=list)
    query_type: str = "broad"  # "broad" | "specific_event" | "specific_person"


# ── Query Type Classification ─────────────────────────────────────────────────

_SPECIFIC_EVENT_PATTERNS = [
    r"[\u4e00-\u9fff]+演唱会",
    r"[\u4e00-\u9fff]+发布会",
    r"[\u4e00-\u9fff]+比赛",
    r"[\u4e00-\u9fff]+晚会",
    r"[\u4e00-\u9fff]+事件",
    r"[\u4e00-\u9fff]+热搜",
    r"[\u4e00-\u9fff]+新闻",
    r"[\u4e00-\u9fff]+争议",
    r"[\u4e00-\u9fff]+翻车",
    r"[\u4e00-\u9fff]+(成都|北京|上海|广州|深圳|杭州|南京|武汉|重庆|西安)",
]

_BROAD_DOMAIN_KEYWORDS = [
    "科技", "数码", "美食", "穿搭", "护肤", "美妆", "健身", "旅行",
    "职场", "教育", "母婴", "宠物", "家居", "汽车", "游戏", "音乐",
    "摄影", "读书", "理财", "情感", "娱乐", "体育", "三农", "vlog",
]


def classify_query_type(query: str) -> str:
    """Classify whether the user query is a broad domain or a specific event/topic.

    Returns: "broad" | "specific_event" | "specific_person"
    """
    query_lower = query.strip().lower()

    if len(query) <= 4 and any(kw in query_lower for kw in _BROAD_DOMAIN_KEYWORDS):
        return "broad"

    for pattern in _SPECIFIC_EVENT_PATTERNS:
        if re.search(pattern, query):
            return "specific_event"

    words = query.split()
    if len(words) >= 2 or len(query) > 6:
        has_verb = any(v in query for v in ["分析", "对比", "评测", "推荐", "盘点", "总结"])
        has_entity = len(query) > 4 and not all(
            any(kw in query_lower for kw in _BROAD_DOMAIN_KEYWORDS)
            for _ in [1]
        )
        if has_entity or has_verb:
            return "specific_event"

    if any(kw == query_lower for kw in _BROAD_DOMAIN_KEYWORDS):
        return "broad"

    if len(query) > 6:
        return "specific_event"

    return "broad"


def generate_specific_event_queries(query: str) -> list[str]:
    """Generate search queries optimized for a specific event/topic.

    Unlike broad decomposition, these queries stay tightly focused on the original topic.
    """
    from datetime import datetime
    date = f"{datetime.now().year}年{datetime.now().month}月"
    year = str(datetime.now().year)

    core_queries = [
        query,
        f"{query} 最新",
        f"{query} {date}",
        f"{query} 分析",
        f"{query} 热点",
    ]

    platform_queries = [
        f"site:mp.weixin.qq.com {query}",
        f"site:weibo.com {query}",
        f"site:xiaohongshu.com {query}",
        f"抖音 {query}",
        f"B站 {query}",
        f"视频号 {query}",
        f"微博 {query} 热议",
    ]

    context_queries = [
        f"{query} 网友评论",
        f"{query} 热搜 讨论",
        f"{query} 数据 分析",
        f"{query} 相关话题",
        f"{query} 背后故事",
        f"{query} 影响",
        f"{query} 博主 讨论",
        f"{query} KOC 内容",
    ]

    content_angle_queries = [
        f"{query} 怎么做内容",
        f"{query} 选题角度",
        f"{query} 流量 爆款",
        f"{query} 内容创作 切入点",
        f"{query} 短视频 创作",
    ]

    return core_queries + platform_queries + context_queries + content_angle_queries


# ── Domain Decomposition (for broad queries) ──────────────────────────────────

_DECOMPOSE_SYSTEM = """你是一个专业的内容领域分析师。你的任务是将一个宽泛的内容领域分解为可搜索的子话题。

请严格返回 JSON（无 markdown 包裹），格式如下：
{
  "sub_domains": ["子领域1", "子领域2", ...],
  "trending_topics": ["当前热门选题1", "当前热门选题2", ...],
  "key_kols": ["该领域知名博主/KOL1", "博主2", ...],
  "platform_angles": {"B站": "该平台的主流内容形式", "小红书": "...", "抖音": "..."},
  "audience_segments": ["目标受众群体1", "受众2", ...],
  "content_formats": ["内容形式1", "内容形式2", ...]
}

要求：
- sub_domains: 8-12个具体子领域（不是形容词，而是实际的内容品类）
- trending_topics: 8-10个当前可能热门的具体选题方向
- key_kols: 5-8个该领域知名的真实博主（确保是真实存在的）
- platform_angles: 覆盖 B站、小红书、抖音、视频号、公众号
- audience_segments: 3-5个主要受众画像
- content_formats: 4-6种常见内容形式

注意：
- 子领域必须足够具体，能直接用于搜索
- 热门选题要有时效性，反映当下趋势
- KOL必须是真实存在的，不要编造"""


async def decompose_domain(domain: str) -> TopicTree:
    """Decompose a broad domain into a structured topic tree for targeted searching.

    Ripple 6.1: First classifies query type. For specific events, generates
    tightly-focused queries instead of broad decomposition.
    """
    query_type = classify_query_type(domain)
    log.info("Query type classification: '%s' → %s", domain, query_type)

    if query_type == "specific_event":
        tree = TopicTree(domain=domain, query_type="specific_event")
        tree.search_queries = generate_specific_event_queries(domain)
        tree.trending_topics = [domain]
        tree.sub_domains = [domain]
        log.info(
            "Specific event mode: %s → %d focused queries",
            domain, len(tree.search_queries),
        )
        return tree

    messages = [
        {"role": "system", "content": _DECOMPOSE_SYSTEM},
        {"role": "user", "content": f"请分解这个内容领域：「{domain}」\n当前时间：2026年5月"},
    ]

    try:
        data = await chat_json(messages, temperature=0.4, max_tokens=2048)
        tree = TopicTree(
            domain=domain,
            query_type="broad",
            sub_domains=data.get("sub_domains", []),
            trending_topics=data.get("trending_topics", []),
            key_kols=data.get("key_kols", []),
            platform_angles=data.get("platform_angles", {}),
            audience_segments=data.get("audience_segments", []),
            content_formats=data.get("content_formats", []),
        )
        tree.search_queries = _generate_targeted_queries(tree)
        log.info(
            "Topic decomposition: %s → %d sub-domains, %d queries",
            domain, len(tree.sub_domains), len(tree.search_queries),
        )
        return tree
    except Exception as exc:
        log.warning("Topic decomposition failed: %s, using fallback", exc)
        return _fallback_decompose(domain)


def _generate_targeted_queries(tree: TopicTree) -> list[str]:
    """Generate targeted search queries from the topic tree."""
    queries: list[str] = []
    domain = tree.domain

    for sub in tree.sub_domains[:10]:
        queries.append(f"{sub} 内容创作 教程")
        queries.append(f"{sub} 爆款 案例分析")

    for topic in tree.trending_topics[:8]:
        queries.append(f"{topic}")
        queries.append(f"{topic} 怎么做")

    for kol in tree.key_kols[:6]:
        queries.append(f"{kol} {domain}")
        queries.append(f"{kol} 作品 代表作")

    platforms = {"B站": "bilibili.com", "小红书": "xiaohongshu.com"}
    for platform, site in platforms.items():
        if platform in tree.platform_angles:
            queries.append(f"site:{site} {domain}")
            for sub in tree.sub_domains[:3]:
                queries.append(f"site:{site} {sub}")

    for segment in tree.audience_segments[:3]:
        queries.append(f"{domain} {segment} 推荐")

    return queries


def _fallback_decompose(domain: str) -> TopicTree:
    """Fallback when LLM decomposition fails — use heuristic sub-topics."""
    tree = TopicTree(domain=domain)
    tree.sub_domains = [
        f"{domain} 入门",
        f"{domain} 测评",
        f"{domain} 推荐",
        f"{domain} 对比",
        f"{domain} 趋势",
    ]
    tree.trending_topics = [f"{domain} 最新", f"{domain} 热门"]
    tree.platform_angles = {
        "B站": "深度评测视频",
        "小红书": "种草笔记",
        "抖音": "短平快对比",
    }
    tree.search_queries = _generate_targeted_queries(tree)
    return tree


async def decompose_topic_for_prediction(topic: str, domain: str = "") -> list[str]:
    """Generate focused search queries for evaluating a specific topic's viral potential."""
    messages = [
        {"role": "system", "content": """你是内容竞品分析专家。给定一个选题，生成15-20个精准搜索查询，
用于找到该选题的竞品内容、相关数据和市场空间。

严格返回 JSON 数组（无 markdown），每个元素是一个搜索查询字符串。
查询要求：
- 5个直接竞品查询（搜索类似主题的已有内容）
- 5个平台定向查询（在主流平台搜索该话题）
- 5个受众需求查询（搜索用户对这个话题的讨论和需求）
- 3-5个差异化角度查询（寻找独特切入点）"""},
        {"role": "user", "content": f"选题：「{topic}」\n领域：{domain or '综合'}"},
    ]

    try:
        data = await chat_json(messages, temperature=0.5, max_tokens=1024)
        if isinstance(data, list):
            return data[:20]
        return data.get("queries", [])[:20]
    except Exception as exc:
        log.warning("Topic prediction decomposition failed: %s", exc)
        return [
            topic,
            f"{topic} 怎么做",
            f"{topic} 教程",
            f"site:xiaohongshu.com {topic}",
            f"site:bilibili.com {topic}",
            f"{topic} 热门",
            f"{topic} 数据",
        ]
