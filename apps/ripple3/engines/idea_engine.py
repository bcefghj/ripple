"""Idea Engine — peer radar + blogger discovery + AI brainstorm.

Two main outputs:
  1. PeerRadarReport — domain ecosystem analysis with blogger profiles
  2. list[TopicIdea]  — 10-20 concrete topic ideas with inspiration sources
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass, field

from adapters.search import (
    search_peers, search_bloggers, search_news,
    SearchResult, NewsResult,
)
from core.llm import chat_json, chat_deep_json, chat_deep_stream

log = logging.getLogger(__name__)


# ── data models ─────────────────────────────────────────────────────────────

@dataclass
class BloggerProfile:
    name: str
    platforms: list[str]
    follower_tier: str
    content_style: str
    signature_works: list[str]
    learning_points: list[str]
    sources: list[str] = field(default_factory=list)


@dataclass
class PeerRadarReport:
    domain: str
    top_bloggers: list[BloggerProfile]
    trending_topics: list[str]
    rising_angles: list[str]
    content_gaps: list[str]
    ecosystem_summary: str
    raw_peer_sources: list[SearchResult] = field(default_factory=list)
    raw_blogger_sources: list[SearchResult] = field(default_factory=list)
    raw_news: list[NewsResult] = field(default_factory=list)


@dataclass
class TopicIdea:
    title: str
    angle: str
    audience: str
    format_suggestion: str
    inspiration_source: str
    raw: dict = field(default_factory=dict)


# ── peer radar ──────────────────────────────────────────────────────────────

_RADAR_SYSTEM = """你是一位懂行的社媒内容顾问，帮 KOC 新手了解领域生态（2026年视角）。

根据搜索数据，输出领域分析 JSON：

1. **top_bloggers**: 5-10位真实博主档案
   每位: name, platforms(含视频号/公众号等腾讯系), follower_tier("头部"/"腰部"/"新锐"), content_style, signature_works, learning_points

2. **trending_topics**: 近期5-8个热门话题（2025-2026年数据）

3. **rising_angles**: 3-5个蓝海角度（有需求但好内容少）

4. **content_gaps**: 3-5个具体可操作的机会

5. **ecosystem_summary**: 200字生态综述（格局+受众+趋势+新手建议）

要求:
- 博主基于搜索数据中的真实人物，不编造
- 优先推荐视频号/公众号/小红书上的创作者
- 趋势结合2025-2026年最新动态
- 蓝海机会要足够具体，新手能直接上手"""


async def scan_radar(domain: str) -> PeerRadarReport:
    """Run the full peer radar: search + LLM analysis → structured report."""
    peer_data = search_peers(domain)
    blogger_data = search_bloggers(domain)
    news_data = search_news(domain)

    peer_text = _format_search_results("同行内容搜索", peer_data[:20])
    blogger_text = _format_search_results("博主/KOL搜索", blogger_data[:20])
    news_text = _format_news_results(news_data[:15])

    user_msg = f"""## 分析领域
{domain}

## 搜索数据

### 同行内容（近期高互动内容）
{peer_text}

### 博主/达人信息
{blogger_text}

### 领域最新动态
{news_text}

## 任务
基于以上真实搜索数据，输出该领域的完整内容生态分析报告。

返回JSON对象，包含:
- top_bloggers: 博主档案数组 (每个含 name, platforms, follower_tier, content_style, signature_works, learning_points)
- trending_topics: 热门话题字符串数组
- rising_angles: 上升角度字符串数组
- content_gaps: 蓝海机会字符串数组
- ecosystem_summary: 生态综述字符串

只返回JSON。"""

    result = await chat_deep_json(
        [
            {"role": "system", "content": _RADAR_SYSTEM},
            {"role": "user", "content": user_msg},
        ],
        max_tokens=6000,
    )

    bloggers = []
    for b in result.get("top_bloggers", []):
        if not isinstance(b, dict):
            continue
        bloggers.append(BloggerProfile(
            name=b.get("name", ""),
            platforms=b.get("platforms", []),
            follower_tier=b.get("follower_tier", ""),
            content_style=b.get("content_style", ""),
            signature_works=b.get("signature_works", []),
            learning_points=b.get("learning_points", []),
        ))

    return PeerRadarReport(
        domain=domain,
        top_bloggers=bloggers,
        trending_topics=result.get("trending_topics", []),
        rising_angles=result.get("rising_angles", []),
        content_gaps=result.get("content_gaps", []),
        ecosystem_summary=result.get("ecosystem_summary", ""),
        raw_peer_sources=peer_data,
        raw_blogger_sources=blogger_data,
        raw_news=news_data,
    )


async def scan_radar_stream(domain: str) -> AsyncIterator[str]:
    """Streaming version — yields markdown analysis as it's generated."""
    peer_data = search_peers(domain)
    blogger_data = search_bloggers(domain)
    news_data = search_news(domain)

    peer_text = _format_search_results("同行内容搜索", peer_data[:20])
    blogger_text = _format_search_results("博主/KOL搜索", blogger_data[:20])
    news_text = _format_news_results(news_data[:15])

    system_msg = """你是一位资深社交媒体行业分析师。请用 Markdown 格式输出领域分析报告，包含以下部分：

## 📊 领域生态综述
（200-300字综述）

## 👤 推荐关注的博主/达人
对每位博主用以下格式：
### 博主名
- **平台**: ...
- **量级**: 头部/腰部/新锐
- **风格**: ...
- **代表作**: ...
- **值得学习**: ...

## 🔥 近期热门话题
（列表）

## 📈 上升趋势（蓝海机会）
（列表，说明为什么是机会）

## 💡 给KOC新手的入场建议
（3-5条具体建议）

## 📰 参考来源
（列出搜索数据中的关键来源URL）

要求：博主推荐基于真实搜索数据，不要编造。分析要具体、有数据支撑。"""

    user_msg = f"""## 分析领域: {domain}

### 同行内容数据
{peer_text}

### 博主/达人数据
{blogger_text}

### 最新动态
{news_text}

请输出完整的领域分析报告（Markdown格式）。"""

    async for chunk in chat_deep_stream(
        [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ],
        max_tokens=6000,
    ):
        yield chunk


# ── idea generation ─────────────────────────────────────────────────────────

_IDEA_SYSTEM = """你是一位超有创意的内容策划师，帮 KOC 新手找到好选题（2026年视角）。

选题标准：
- 标题像真正的爆款（数字/反差/悬念/共鸣）
- 标注灵感来自搜索数据中的哪条
- 覆盖不同形式（图文/视频/清单/教程）
- 考虑视频号和小红书的内容偏好
- 避免过时话题，聚焦2025-2026年新趋势

每个选题包含：
- title: 标题（像真实爆款）
- angle: 切入角度（为什么好）
- audience: 目标受众
- format_suggestion: 内容形式
- inspiration_source: 灵感来源（引用搜索数据）"""


async def generate_ideas(
    domain: str,
    *,
    user_context: str = "",
    count: int = 12,
    radar_report: PeerRadarReport | None = None,
) -> list[TopicIdea]:
    """Scan peers + brainstorm topic ideas via LLM."""
    if radar_report:
        peer_data = radar_report.raw_peer_sources
        news_data = radar_report.raw_news
    else:
        peer_data = search_peers(domain)
        news_data = search_news(domain)

    peer_summary = _format_search_results("同行内容", peer_data[:20])
    news_summary = _format_news_results(news_data[:10])

    radar_context = ""
    if radar_report:
        radar_context = f"""
## 领域生态分析
{radar_report.ecosystem_summary}

### 热门话题: {', '.join(radar_report.trending_topics[:5])}
### 上升趋势: {', '.join(radar_report.rising_angles[:5])}
### 蓝海机会: {', '.join(radar_report.content_gaps[:5])}
"""

    user_msg = f"""## 用户领域
{domain}

## 同行雷达扫描结果
{peer_summary}

## 领域最新动态
{news_summary}
{radar_context}"""

    if user_context:
        user_msg += f"\n## 用户补充信息\n{user_context}\n"

    user_msg += f"""
## 任务
基于以上数据，生成{count}个有创意的选题点子。每个选题都要标明灵感来自哪条搜索数据。

以JSON数组格式返回，每个元素包含 title, angle, audience, format_suggestion, inspiration_source 字段。
只返回JSON，不要其他内容。"""

    result = await chat_json(
        [
            {"role": "system", "content": _IDEA_SYSTEM},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.8,
        max_tokens=6000,
    )

    items = result if isinstance(result, list) else result.get("ideas", result.get("topics", []))
    ideas = []
    for item in items:
        if not isinstance(item, dict):
            continue
        ideas.append(TopicIdea(
            title=item.get("title", ""),
            angle=item.get("angle", ""),
            audience=item.get("audience", ""),
            format_suggestion=item.get("format_suggestion", ""),
            inspiration_source=item.get("inspiration_source", ""),
            raw=item,
        ))
    return ideas


async def generate_ideas_stream(
    domain: str,
    *,
    user_context: str = "",
    count: int = 12,
) -> AsyncIterator[str]:
    """Streaming version — yields markdown-formatted ideas as generated."""
    peer_data = search_peers(domain)
    news_data = search_news(domain)

    peer_summary = _format_search_results("同行内容", peer_data[:15])
    news_summary = _format_news_results(news_data[:10])

    system_msg = """你是一位资深社交媒体内容策划专家。请用 Markdown 格式输出选题灵感列表。

对每个选题用以下格式：

### 💡 选题 #N: "标题"
- **切入角度**: ...
- **目标受众**: ...
- **内容形式**: ...
- **灵感来源**: ...（引用搜索数据中的具体内容）
- **为什么值得做**: ...

最后给出一段总结，推荐前3个最值得做的选题及原因。"""

    user_msg = f"""## 领域: {domain}

### 同行内容数据
{peer_summary}

### 最新动态
{news_summary}
"""
    if user_context:
        user_msg += f"\n### 用户补充\n{user_context}\n"
    user_msg += f"\n请生成{count}个选题灵感（Markdown格式）。"

    async for chunk in chat_deep_stream(
        [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ],
        max_tokens=6000,
        temperature=0.8,
    ):
        yield chunk


# ── helpers ─────────────────────────────────────────────────────────────────

def _format_search_results(label: str, results: list[SearchResult]) -> str:
    if not results:
        return f"（{label}：未找到数据）"
    lines = []
    for i, r in enumerate(results, 1):
        lines.append(f"{i}. 【{r.title}】\n   {r.snippet}\n   来源: {r.url}")
    return "\n".join(lines)


def _format_news_results(results: list[NewsResult]) -> str:
    if not results:
        return "（未找到近期新闻动态）"
    lines = []
    for i, r in enumerate(results, 1):
        date_str = f" ({r.date})" if r.date else ""
        lines.append(f"{i}. 【{r.title}】{date_str}\n   {r.snippet}\n   来源: {r.url}")
    return "\n".join(lines)
