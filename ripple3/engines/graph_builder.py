"""Knowledge graph extraction engine — builds structured graph data from search results.

Uses a **two-pass** LLM pipeline:
  Pass 1: Aggressive entity extraction (150-300 nodes across 14 types).
  Pass 2: Relationship enrichment between all extracted entities (2-4 edges per node).

Outputs force-graph-compatible JSON consumed by the frontend.
"""

from __future__ import annotations

import json
import logging
import re
from collections import Counter
from dataclasses import dataclass, field

from core.llm import chat_deep_json

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Type definitions & color palette
# ---------------------------------------------------------------------------

_ENTITY_TYPES = [
    "person", "topic", "platform", "format",
    "audience", "trend", "strategy", "brand",
    "event", "metric", "keyword", "content",
    "competitor", "channel",
]

_TYPE_COLORS = {
    "person":     "#818cf8",
    "topic":      "#fbbf24",
    "platform":   "#34d399",
    "format":     "#f472b6",
    "audience":   "#22d3ee",
    "trend":      "#a78bfa",
    "strategy":   "#fb923c",
    "brand":      "#f87171",
    "event":      "#38bdf8",
    "metric":     "#4ade80",
    "keyword":    "#06b6d4",
    "content":    "#14b8a6",
    "competitor": "#f59e0b",
    "channel":    "#8b5cf6",
}

# ---------------------------------------------------------------------------
# Pass-1 prompt: aggressive entity extraction
# ---------------------------------------------------------------------------

_PASS1_SYSTEM = """\
你是一个专业的知识图谱实体提取引擎。你的任务是从搜索数据中**尽可能多地**提取实体节点。

## 输出格式（严格 JSON）
{
  "nodes": [
    {
      "id": "唯一英文/拼音ID（不含空格）",
      "name": "中文显示名称",
      "type": "person|topic|platform|format|audience|trend|strategy|brand|event|metric|keyword|content|competitor|channel",
      "val": 10,
      "desc": "20-50字的实质性描述，说明该实体是什么、为什么重要"
    }
  ]
}

## 实体类型详细说明

### person（目标: 15-25个）
博主、KOL、KOC、UP主、达人、行业专家、意见领袖。
- 从搜索结果中提取所有提到的人名、账号名、频道名
- 即使只出现一次也要提取

### topic（目标: 20-30个）
话题、选题方向、内容主题、热搜话题、讨论焦点、细分领域。
- 提取所有核心话题和子话题
- 拆解大话题为具体子话题（如"手机测评"→"手机拍照对比"、"续航测试"、"性价比推荐"）

### platform（目标: 8-12个）
小红书、B站、抖音、视频号、公众号、微博、快手、知乎、YouTube、TikTok、微信搜一搜、今日头条等。
- 搜索数据中提到或暗示的所有平台

### format（目标: 8-12个）
图文、短视频、长视频、直播、清单、微信图文、Vlog、教程、评测视频、合集、问答、信息图等。
- 提取所有内容形式，包括细分格式

### audience（目标: 10-15个）
大学生、宝妈、职场人、Z世代、银发族、新中产、数码发烧友、美妆爱好者等。
- 基于内容推断目标受众群体
- 尽量细分，不要只用"年轻人"这样笼统的分类

### trend（目标: 8-12个）
流行趋势、热门现象、行业动向、新兴概念。
- 提取内容中体现的趋势信号

### strategy（目标: 8-12个）
运营策略、变现模式、增长方法。
- 私域引流、社交裂变、SEO优化、广告投放、直播带货、知识付费、品牌联名等

### brand（目标: 8-12个）
品牌、公司、产品名、App名、工具名。
- 搜索结果中出现的品牌和产品

### event（目标: 5-8个）
活动、事件、节日营销、行业会议、热点事件。

### metric（目标: 5-8个）
关键指标、数据指标。
- 如: 播放量、粉丝数、转化率、ROI、互动率等

### keyword（目标: 15-25个）
搜索关键词、SEO词、长尾词、热搜词、标签。
- 从搜索数据中提取高频关键词和长尾搜索词
- 包括用户常搜的问题词、对比词、推荐词

### content（目标: 10-15个）
具体内容作品、爆款视频、热门文章、代表性笔记。
- 搜索数据中出现的具体内容标题或类型
- 分析其爆款特征

### competitor（目标: 8-12个）
竞品内容、竞争对手、同类产品、同赛道账号。
- 识别同领域的竞争内容和账号
- 标注其差异化特点

### channel（目标: 5-8个）
分发渠道、流量入口、获客通道、搜索入口。
- 内容触达用户的具体渠道路径
- 包括搜索、推荐、社交分享等

## 层次化结构提取
请按照以下层级关系组织提取：**行业 → 赛道 → 话题 → 关键词 → 竞品内容**
- 每个行业下应有多个赛道（topic）
- 每个赛道下应有相关话题和关键词（keyword）
- 每个话题下应关联具体的竞品内容（competitor/content）
- 确保层级间有清晰的父子归属关系

## 关键规则
1. **数量要求: 必须提取 150-300 个节点**，宁多勿少
2. val 值（5-50）代表该实体的估计热度/重要性权重：
   - 行业核心/顶流 → val 35-50
   - 高频出现/重要实体 → val 20-34
   - 中等重要性 → val 12-19
   - 一般实体 → val 5-11
3. 每个 desc 必须有实质内容（20-50字），用户点击节点时会看到
4. 基于实际搜索数据提取，但可以做合理推断（如某话题必然涉及某平台）
5. ID 使用英文或拼音，确保唯一"""

# ---------------------------------------------------------------------------
# Pass-2 prompt: relationship enrichment
# ---------------------------------------------------------------------------

_PASS2_SYSTEM = """\
你是一个知识图谱关系挖掘引擎。给定一组已提取的实体节点，你需要发现它们之间**尽可能多**的关系。

## 输出格式（严格 JSON）
{
  "links": [
    {
      "source": "源节点ID",
      "target": "目标节点ID",
      "label": "关系类型",
      "strength": 0.8
    }
  ]
}

## 关系类型库（必须从中选择）

### 层级关系（hierarchy）— 优先提取
- "包含": 父节点 → 子节点（行业包含赛道、赛道包含话题、话题包含关键词）
- "属于": 子节点 → 父节点（反向归属关系）
- "细分为": topic → topic（话题细分为子话题）
- "上级": keyword → topic（关键词归属于话题）

### 人物相关
- "创作于": person → platform（某人在某平台创作）
- "擅长": person → topic（某人擅长某话题）
- "讨论": person → topic（某人讨论了某话题）
- "竞争": person ↔ person（同领域竞争关系）
- "合作": person ↔ person（合作关系）
- "代言": person → brand（代言/推广品牌）
- "面向": person → audience（某人的目标受众）
- "产出": person → content（某人产出了某内容）
- "使用渠道": person → channel（某人使用的分发渠道）

### 话题相关
- "适合": topic → format（话题适合某种内容形式）
- "面向": topic → audience（话题面向的受众）
- "热门于": topic → platform（话题在某平台热门）
- "衍生": topic → topic（话题衍生关系）
- "竞争": topic ↔ topic（话题之间的竞争关系）
- "互补": topic ↔ topic（话题之间互补）
- "演变为": topic → topic（话题演变趋势）
- "体现趋势": topic → trend（话题体现了某趋势）
- "涉及品牌": topic → brand（话题涉及某品牌）
- "关注指标": topic → metric（话题关注的核心指标）
- "关联关键词": topic → keyword（话题关联的搜索关键词）
- "对标竞品": topic → competitor（话题下的竞品内容）

### 平台相关
- "竞争": platform ↔ platform（平台竞争）
- "互补": platform ↔ platform（平台互补）
- "引流至": platform → platform（平台间导流）
- "平台独有": format → platform（某形式为平台独有/特色）
- "受众重叠": platform ↔ platform（受众重叠）
- "主要受众": platform → audience（平台主要用户群）
- "分发通过": content → channel（内容通过某渠道分发）

### 策略相关
- "适用策略": topic → strategy（话题适用的运营策略）
- "裂变通过": strategy → platform（策略通过某平台实现）
- "提升": strategy → metric（策略能提升某指标）
- "影响": trend → strategy（趋势影响策略选择）

### 竞品与内容相关
- "竞品对标": competitor → competitor（竞品之间的对标关系）
- "模仿": content → content（内容之间的模仿/借鉴关系）
- "优于": competitor → competitor（竞品优劣对比）
- "同类": content → content（同类内容）
- "分发于": content → platform（内容发布在某平台）
- "使用关键词": content → keyword（内容使用的关键词）

### 趋势与事件
- "影响": event → topic（事件影响话题热度）
- "影响": trend → topic（趋势影响话题方向）
- "催生": event → trend（事件催生趋势）
- "推动": brand → trend（品牌推动趋势）

## 关键规则
1. **数量要求: 每个节点平均 2-4 条关系**，总计应有 300-600 条关系
2. **优先提取层级关系（hierarchy）**：确保"行业→赛道→话题→关键词→竞品内容"的层次结构清晰
3. 每对重要节点之间应有至少一条关系
4. strength 值（0.1-1.0）代表关系强度：
   - 直接明确关系 → 0.7-1.0
   - 间接推断关系 → 0.4-0.6
   - 弱关联 → 0.1-0.3
5. 确保图谱高度连通，避免孤立节点
6. source 和 target 必须是已提供的节点 ID
7. 同一对节点可以有多条不同 label 的关系"""

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def build_knowledge_graph(
    domain: str,
    search_data: dict,
    *,
    max_nodes: int = 300,
) -> dict:
    """Extract knowledge graph from search results using two-pass LLM pipeline.

    Pass 1 — entity extraction (nodes).
    Pass 2 — relationship enrichment (links) given extracted nodes.
    """
    search_summary = _format_search_for_graph(search_data)
    mention_counts = _count_mentions(search_data)

    # ── Pass 1: Entity extraction ────────────────────────────────────────
    log.info("Graph pass-1: extracting entities for domain=%s", domain)
    nodes = await _extract_entities(domain, search_summary, max_nodes)

    if not nodes:
        log.warning("Pass-1 returned no nodes, using fallback")
        return _fallback_graph(domain, search_data)

    # Adjust val scores based on actual mention frequency
    _adjust_importance(nodes, mention_counts)

    # ── Pass 2: Relationship enrichment ──────────────────────────────────
    log.info("Graph pass-2: enriching relationships (%d nodes)", len(nodes))
    links = await _enrich_relationships(domain, search_summary, nodes)

    graph = _validate_graph({"nodes": nodes, "links": links}, domain)
    log.info(
        "Graph complete: %d nodes, %d links",
        len(graph["nodes"]),
        len(graph["links"]),
    )
    return graph


# ---------------------------------------------------------------------------
# Pass-1: entity extraction
# ---------------------------------------------------------------------------


async def _extract_entities(
    domain: str, search_summary: str, max_nodes: int
) -> list[dict]:
    messages = [
        {"role": "system", "content": _PASS1_SYSTEM},
        {
            "role": "user",
            "content": (
                f"## 领域\n{domain}\n\n"
                f"## 搜索数据\n{search_summary}\n\n"
                f"## 任务\n"
                f"请从以上搜索数据中提取 **150-{max_nodes}** 个实体节点。\n"
                f"覆盖所有 14 种类型（person, topic, platform, format, audience, "
                f"trend, strategy, brand, event, metric, keyword, content, "
                f"competitor, channel），每种类型至少提取 3 个。\n"
                f"注意构建层级关系：行业 → 赛道 → 话题 → 关键词 → 竞品内容。\n"
                f"返回严格 JSON，只包含 nodes 数组。"
            ),
        },
    ]

    try:
        result = await chat_deep_json(messages, temperature=0.3, max_tokens=16384)
        raw_nodes = result if isinstance(result, list) else result.get("nodes", [])
        return [n for n in raw_nodes if isinstance(n, dict) and "id" in n]
    except Exception as exc:
        log.warning("Pass-1 entity extraction failed: %s", exc)
        return []


# ---------------------------------------------------------------------------
# Pass-2: relationship enrichment
# ---------------------------------------------------------------------------


async def _enrich_relationships(
    domain: str, search_summary: str, nodes: list[dict]
) -> list[dict]:
    node_summary = json.dumps(
        [{"id": n["id"], "name": n["name"], "type": n.get("type", "topic")}
         for n in nodes],
        ensure_ascii=False,
    )

    messages = [
        {"role": "system", "content": _PASS2_SYSTEM},
        {
            "role": "user",
            "content": (
                f"## 领域\n{domain}\n\n"
                f"## 搜索数据摘要\n{search_summary[:3000]}\n\n"
                f"## 已提取的实体节点\n{node_summary}\n\n"
                f"## 任务\n"
                f"请在以上 {len(nodes)} 个节点之间挖掘 **每个节点 2-4 条关系**（总计 {len(nodes)*2}-{len(nodes)*4} 条）。\n"
                f"优先提取层级关系（包含/属于/细分为），构建清晰的树状层次。\n"
                f"确保每个节点至少有 2 条关系连接，图谱高度连通。\n"
                f"返回严格 JSON，只包含 links 数组。"
            ),
        },
    ]

    try:
        result = await chat_deep_json(messages, temperature=0.3, max_tokens=16384)
        raw_links = result if isinstance(result, list) else result.get("links", [])
        return [lk for lk in raw_links if isinstance(lk, dict)]
    except Exception as exc:
        log.warning("Pass-2 relationship enrichment failed: %s", exc)
        return []


# ---------------------------------------------------------------------------
# Mention-frequency scoring
# ---------------------------------------------------------------------------


def _count_mentions(search_data: dict) -> Counter:
    """Count how many times each term appears across all search results."""
    counter: Counter = Counter()
    for _key, items in search_data.items():
        if not isinstance(items, list):
            continue
        for item in items:
            text = ""
            if isinstance(item, dict):
                text = f"{item.get('title', '')} {item.get('snippet', '')}"
            elif hasattr(item, "title"):
                text = f"{item.title} {getattr(item, 'snippet', '')}"
            for token in re.findall(r"[\u4e00-\u9fff\w]{2,}", text):
                counter[token] += 1
    return counter


def _adjust_importance(nodes: list[dict], mentions: Counter) -> None:
    """Boost or reduce node val based on how often the node name appears."""
    if not mentions:
        return
    for node in nodes:
        name = node.get("name", "")
        freq = sum(mentions.get(tok, 0) for tok in re.findall(r"[\u4e00-\u9fff\w]{2,}", name))
        if freq >= 5:
            node["val"] = max(node.get("val", 10), 25)
        elif freq >= 3:
            node["val"] = max(node.get("val", 10), 18)
        elif freq >= 1:
            node["val"] = max(node.get("val", 10), 10)


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------


def _format_search_for_graph(data: dict) -> str:
    """Format search results into a rich summary for graph extraction."""
    parts = []
    category_labels = [
        ("peers", "同行内容/竞品分析"),
        ("bloggers", "博主/KOL信息"),
        ("news", "行业动态/新闻"),
        ("trending", "热搜/趋势"),
        ("topics", "话题/选题"),
        ("platforms", "平台数据"),
        ("comments", "用户评论"),
        ("products", "产品/品牌"),
    ]

    for key, label in category_labels:
        items = data.get(key, [])
        if not items:
            continue
        lines = []
        for i, item in enumerate(items[:60], 1):
            if isinstance(item, dict):
                title = item.get("title", "")
                snippet = item.get("snippet", "")
                source = item.get("source", "")
            elif hasattr(item, "title"):
                title = item.title
                snippet = getattr(item, "snippet", "")
                source = getattr(item, "source", "")
            else:
                title = str(item)
                snippet = ""
                source = ""
            entry = f"  {i}. {title}"
            if snippet:
                entry += f": {snippet[:150]}"
            if source:
                entry += f" [{source}]"
            lines.append(entry)
        parts.append(f"### {label}\n" + "\n".join(lines))

    return "\n\n".join(parts) if parts else "（无搜索数据）"


# ---------------------------------------------------------------------------
# Validation & normalization
# ---------------------------------------------------------------------------


def _validate_graph(data: dict | list, domain: str) -> dict:
    """Validate, deduplicate, and normalize graph data."""
    if isinstance(data, list):
        data = {"nodes": data, "links": []}

    nodes = data.get("nodes", [])
    links = data.get("links", [])

    # Deduplicate nodes by id
    seen_ids: set[str] = set()
    valid_nodes: list[dict] = []
    for n in nodes:
        if not isinstance(n, dict) or "id" not in n:
            continue
        nid = str(n["id"])
        if nid in seen_ids:
            continue
        seen_ids.add(nid)

        n["id"] = nid
        n.setdefault("name", nid)
        ntype = n.get("type", "topic")
        if ntype not in _TYPE_COLORS:
            ntype = "topic"
        n["type"] = ntype
        n.setdefault("val", 10)
        n["val"] = max(5, min(50, int(n["val"])))
        n.setdefault("desc", "")
        n["color"] = _TYPE_COLORS[ntype]
        valid_nodes.append(n)

    node_ids = {n["id"] for n in valid_nodes}

    # Deduplicate links
    seen_links: set[tuple] = set()
    valid_links: list[dict] = []
    for link in links:
        if not isinstance(link, dict):
            continue
        src = str(link.get("source", ""))
        tgt = str(link.get("target", ""))
        label = link.get("label", "关联")
        if src not in node_ids or tgt not in node_ids or src == tgt:
            continue
        link_key = (src, tgt, label)
        if link_key in seen_links:
            continue
        seen_links.add(link_key)

        link["source"] = src
        link["target"] = tgt
        link["label"] = label
        strength = link.get("strength", 0.5)
        link["strength"] = max(0.1, min(1.0, float(strength)))
        valid_links.append(link)

    if not valid_nodes:
        return _fallback_graph(domain, {})

    return {"nodes": valid_nodes, "links": valid_links}


# ---------------------------------------------------------------------------
# Fallback graph (when LLM fails)
# ---------------------------------------------------------------------------


def _fallback_graph(domain: str, data: dict) -> dict:
    """Generate a reasonable graph when LLM extraction fails."""
    nodes = [
        {"id": "domain", "name": domain, "type": "topic", "val": 28, "color": _TYPE_COLORS["topic"], "desc": f"「{domain}」领域核心话题"},
        {"id": "xhs", "name": "小红书", "type": "platform", "val": 18, "color": _TYPE_COLORS["platform"], "desc": "种草社区，图文与短视频并重"},
        {"id": "bili", "name": "B站", "type": "platform", "val": 18, "color": _TYPE_COLORS["platform"], "desc": "中长视频社区，年轻用户聚集"},
        {"id": "douyin", "name": "抖音", "type": "platform", "val": 20, "color": _TYPE_COLORS["platform"], "desc": "短视频平台，流量最大"},
        {"id": "wx", "name": "视频号", "type": "platform", "val": 14, "color": _TYPE_COLORS["platform"], "desc": "微信生态短视频，私域流量入口"},
        {"id": "weibo", "name": "微博", "type": "platform", "val": 12, "color": _TYPE_COLORS["platform"], "desc": "社交媒体，热搜话题发源地"},
        {"id": "zhihu", "name": "知乎", "type": "platform", "val": 10, "color": _TYPE_COLORS["platform"], "desc": "知识问答社区，长内容平台"},
        {"id": "video_short", "name": "短视频", "type": "format", "val": 15, "color": _TYPE_COLORS["format"], "desc": "1分钟内短视频，当前最热形式"},
        {"id": "video_long", "name": "长视频", "type": "format", "val": 10, "color": _TYPE_COLORS["format"], "desc": "5分钟以上深度视频内容"},
        {"id": "graphic", "name": "图文", "type": "format", "val": 12, "color": _TYPE_COLORS["format"], "desc": "图文笔记、文章类内容"},
        {"id": "live", "name": "直播", "type": "format", "val": 10, "color": _TYPE_COLORS["format"], "desc": "实时互动直播内容"},
        {"id": "young", "name": "Z世代", "type": "audience", "val": 12, "color": _TYPE_COLORS["audience"], "desc": "18-27岁年轻群体"},
        {"id": "office", "name": "职场人", "type": "audience", "val": 10, "color": _TYPE_COLORS["audience"], "desc": "25-40岁职场群体"},
        {"id": "trend_ai", "name": "AI创作", "type": "trend", "val": 14, "color": _TYPE_COLORS["trend"], "desc": "AI辅助内容创作趋势"},
        {"id": "trend_short", "name": "短视频化", "type": "trend", "val": 12, "color": _TYPE_COLORS["trend"], "desc": "各平台内容短视频化趋势"},
        {"id": "strat_private", "name": "私域运营", "type": "strategy", "val": 10, "color": _TYPE_COLORS["strategy"], "desc": "通过私域流量池运营用户"},
        {"id": "strat_seo", "name": "SEO优化", "type": "strategy", "val": 8, "color": _TYPE_COLORS["strategy"], "desc": "搜索引擎/平台搜索优化"},
    ]

    # Add entities from search data
    peers = data.get("peers", [])
    for i, p in enumerate(peers[:8]):
        title = getattr(p, "title", "") if hasattr(p, "title") else p.get("title", f"话题{i+1}")
        snippet = getattr(p, "snippet", "") if hasattr(p, "snippet") else p.get("snippet", "")
        nodes.append({
            "id": f"topic_{i}", "name": title[:15], "type": "topic",
            "val": 8, "color": _TYPE_COLORS["topic"],
            "desc": (snippet or title)[:50],
        })

    bloggers = data.get("bloggers", [])
    for i, b in enumerate(bloggers[:8]):
        title = getattr(b, "title", "") if hasattr(b, "title") else b.get("title", f"博主{i+1}")
        name = title.split("_")[0].split("-")[0].split("|")[0][:10]
        nodes.append({
            "id": f"person_{i}", "name": name, "type": "person",
            "val": 12, "color": _TYPE_COLORS["person"],
            "desc": title[:50],
        })

    links = [
        {"source": "domain", "target": "xhs", "label": "热门于", "strength": 0.8},
        {"source": "domain", "target": "bili", "label": "热门于", "strength": 0.7},
        {"source": "domain", "target": "douyin", "label": "热门于", "strength": 0.9},
        {"source": "domain", "target": "wx", "label": "热门于", "strength": 0.5},
        {"source": "domain", "target": "weibo", "label": "热门于", "strength": 0.5},
        {"source": "domain", "target": "video_short", "label": "适合", "strength": 0.8},
        {"source": "domain", "target": "video_long", "label": "适合", "strength": 0.5},
        {"source": "domain", "target": "graphic", "label": "适合", "strength": 0.6},
        {"source": "domain", "target": "young", "label": "面向", "strength": 0.7},
        {"source": "domain", "target": "office", "label": "面向", "strength": 0.5},
        {"source": "xhs", "target": "douyin", "label": "竞争", "strength": 0.7},
        {"source": "bili", "target": "douyin", "label": "竞争", "strength": 0.6},
        {"source": "xhs", "target": "graphic", "label": "平台独有", "strength": 0.7},
        {"source": "douyin", "target": "video_short", "label": "平台独有", "strength": 0.9},
        {"source": "bili", "target": "video_long", "label": "平台独有", "strength": 0.8},
        {"source": "wx", "target": "xhs", "label": "引流至", "strength": 0.4},
        {"source": "trend_ai", "target": "domain", "label": "影响", "strength": 0.6},
        {"source": "trend_short", "target": "video_short", "label": "影响", "strength": 0.8},
        {"source": "strat_private", "target": "wx", "label": "裂变通过", "strength": 0.7},
        {"source": "strat_seo", "target": "zhihu", "label": "裂变通过", "strength": 0.5},
        {"source": "xhs", "target": "bili", "label": "受众重叠", "strength": 0.5},
    ]

    node_ids = {n["id"] for n in nodes}
    for n in nodes:
        if n["id"].startswith("topic_") and "domain" in node_ids:
            links.append({"source": "domain", "target": n["id"], "label": "衍生", "strength": 0.6})
            links.append({"source": n["id"], "target": "douyin", "label": "热门于", "strength": 0.5})
        if n["id"].startswith("person_"):
            links.append({"source": n["id"], "target": "domain", "label": "擅长", "strength": 0.7})
            links.append({"source": n["id"], "target": "xhs", "label": "创作于", "strength": 0.5})
            links.append({"source": n["id"], "target": "young", "label": "面向", "strength": 0.4})

    return {"nodes": nodes, "links": links}
