"""Intelligent Query Builder — Topic Decomposition driven, 30+ targeted queries.

Replaces the old _generate_peer_queries / _generate_blogger_queries approach
with a 4-layer strategy that prioritizes relevance over volume:
  Layer 1: Pure domain queries (highest relevance)
  Layer 2: Sub-domain expansion (LLM-generated sub-topics)
  Layer 3: Platform-directed queries (site: prefixed)
  Layer 4: KOL-directed queries (specific creator names)
"""

from __future__ import annotations

import logging
from datetime import datetime

from engines.topic_decomposer import TopicTree

log = logging.getLogger(__name__)


def _current_date_str() -> str:
    now = datetime.now()
    return f"{now.year}年{now.month}月"


def _current_year() -> str:
    return str(datetime.now().year)


def build_radar_queries(tree: TopicTree) -> dict[str, list[str]]:
    """Build query sets for domain radar analysis using topic tree.

    Returns dict with keys: peers, bloggers, news, trending
    Target: 30+ queries per category for broad coverage.
    """
    domain = tree.domain
    date = _current_date_str()
    year = _current_year()

    peers: list[str] = []
    for sub in tree.sub_domains[:10]:
        peers.append(f"{sub} 内容 创作者")
        peers.append(f"{sub} 优质内容 推荐")
        peers.append(f"{sub} 爆款 案例")

    for topic in tree.trending_topics[:6]:
        peers.append(topic)
        peers.append(f"{topic} 数据分析")

    platforms = {
        "bilibili.com": "B站",
        "xiaohongshu.com": "小红书",
    }
    for site, name in platforms.items():
        peers.append(f"site:{site} {domain}")
        for sub in tree.sub_domains[:3]:
            peers.append(f"site:{site} {sub}")

    peers.append(f"{domain} KOC 涨粉 策略 {year}")
    peers.append(f"{domain} 内容生态 分析 {year}")

    bloggers: list[str] = []
    for kol in tree.key_kols[:8]:
        bloggers.append(f"{kol}")
        bloggers.append(f"{kol} {domain} 作品")

    bloggers.append(f"{domain} 博主 排行 推荐 {year}")
    bloggers.append(f"{domain} KOL 达人 排名")
    bloggers.append(f"{domain} UP主 推荐")
    bloggers.append(f"{domain} 小红书 博主 推荐")
    bloggers.append(f"{domain} 新人博主 黑马")
    for sub in tree.sub_domains[:4]:
        bloggers.append(f"{sub} 博主 达人")

    news: list[str] = []
    news.append(f"{domain} 最新趋势 {date}")
    news.append(f"{domain} 行业动态 {date}")
    news.append(f"{domain} 平台政策 算法变化 {year}")
    news.append(f"{domain} 热点话题 {date}")
    for topic in tree.trending_topics[:4]:
        news.append(f"{topic} 最新")

    trending: list[str] = []
    trending.append(f"{domain} 热搜 今日")
    trending.append(f"{domain} 热门话题 {date}")
    trending.append(f"抖音 {domain} 热门")
    trending.append(f"小红书 {domain} 热门")
    trending.append(f"B站 {domain} 热门")
    trending.append(f"微博 {domain} 话题")

    log.info(
        "Query builder (radar): peers=%d, bloggers=%d, news=%d, trending=%d",
        len(peers), len(bloggers), len(news), len(trending),
    )
    return {"peers": peers, "bloggers": bloggers, "news": news, "trending": trending}


def build_idea_queries(tree: TopicTree, user_context: str = "") -> dict[str, list[str]]:
    """Build queries for idea generation."""
    domain = tree.domain
    year = _current_year()

    peers: list[str] = []
    for sub in tree.sub_domains[:8]:
        peers.append(f"{sub} 选题 灵感")
        peers.append(f"{sub} 内容创意")
    for topic in tree.trending_topics[:6]:
        peers.append(topic)
    if user_context:
        peers.append(f"{domain} {user_context}")

    peers.append(f"{domain} 选题方向 {year}")
    peers.append(f"{domain} 内容机会 蓝海")
    peers.append(f"{domain} 新手 入门 选题")

    news: list[str] = []
    news.append(f"{domain} 最新热点")
    news.append(f"{domain} 近期话题 讨论")
    for topic in tree.trending_topics[:4]:
        news.append(f"{topic} 讨论 观点")

    trending: list[str] = []
    trending.append(f"{domain} 今日热搜")
    trending.append(f"抖音 {domain} 热门话题")
    trending.append(f"小红书 {domain} 热门笔记")

    return {"peers": peers, "news": news, "trending": trending}


def build_predict_queries(topic: str, domain: str = "") -> dict[str, list[str]]:
    """Build queries for viral prediction of a specific topic."""
    date = _current_date_str()
    year = _current_year()
    domain_prefix = f"{domain} " if domain else ""

    competition: list[str] = [
        topic,
        f"{topic} {date}",
        f"{topic} 最新",
        f"{topic} 教程",
        f"{topic} 经验分享",
        f"site:xiaohongshu.com {topic}",
        f"site:bilibili.com {topic}",
        f"{domain_prefix}{topic} 内容",
        f"{topic} 怎么做 攻略",
        f"{topic} 热门 {year}",
        f"{topic} 讨论 评论",
        f"{topic} 数据 分析",
        f"{topic} 竞品 对比 {year}",
        f"{domain_prefix}类似选题 爆款",
    ]

    trending: list[str] = [
        f"{topic} 热度 {date}",
        f"{domain_prefix}热搜 相关 {date}",
        f"{topic} 搜索量 趋势",
    ]

    return {"competition": competition, "trending": trending}


def build_distill_queries(blogger: str, domain: str = "") -> dict[str, list[str]]:
    """Build queries for blogger style distillation."""
    content: list[str] = [
        f"{blogger}",
        f"{blogger} 作品 代表作",
        f"{blogger} 视频 内容",
        f"{blogger} 爆款 热门",
        f"site:xiaohongshu.com {blogger}",
        f"site:bilibili.com {blogger}",
        f"{blogger} 风格 特点",
        f"{blogger} 粉丝 数据",
    ]
    if domain:
        content.append(f"{blogger} {domain}")

    profile: list[str] = [
        f"{blogger} 个人介绍",
        f"{blogger} 博主 背景",
        f"{blogger} 创作者 经历",
        f"{blogger} 采访 对话",
    ]

    return {"content": content, "profile": profile}
