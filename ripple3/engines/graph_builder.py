"""Knowledge graph extraction engine — builds structured graph data from search results.

Uses LLM to extract entities (people, topics, platforms, formats, audiences)
and relationships from search data, outputting force-graph-compatible JSON.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field

from core.llm import chat_deep_json

log = logging.getLogger(__name__)

_GRAPH_SYSTEM = """你是一个知识图谱构建引擎。从搜索结果中提取实体和关系，构建领域知识图谱。

输出严格 JSON，格式如下：
{
  "nodes": [
    {"id": "唯一ID", "name": "显示名称", "type": "person|topic|platform|format|audience", "val": 10, "desc": "简短描述"}
  ],
  "links": [
    {"source": "源节点ID", "target": "目标节点ID", "label": "关系描述", "strength": 0.8}
  ]
}

节点类型说明：
- person: 博主、KOL、KOC、UP主、达人
- topic: 话题、选题方向、内容主题、热搜话题
- platform: 平台（小红书、B站、抖音、视频号、公众号）
- format: 内容形式（图文、短视频、长视频、直播、清单）
- audience: 受众群体（大学生、宝妈、职场人、Z世代）

关系类型：
- "创作于": person → platform
- "擅长": person → topic
- "讨论": person → topic
- "适合": topic → format
- "面向": topic → audience
- "热门于": topic → platform
- "竞争": person → person
- "合作": person → person
- "衍生": topic → topic

要求：
1. 尽可能多地提取节点（50-100个），确保类型多样
2. 提取 80-200 条关系，展现丰富的网络结构
3. val 值代表重要性（1-30），越重要越大
4. strength 值代表关系强度（0.1-1.0）
5. 基于实际搜索数据提取，不编造
6. 确保图谱连通，避免孤立节点
7. 每个节点的 desc 要有实质内容（20-50字），点击时展示给用户"""


async def build_knowledge_graph(
    domain: str,
    search_data: dict,
    *,
    max_nodes: int = 80,
) -> dict:
    """Extract knowledge graph from search results using LLM.

    Args:
        domain: The domain/field being analyzed
        search_data: Dict with keys like 'peers', 'bloggers', 'news', 'trending'
        max_nodes: Maximum number of nodes to extract

    Returns:
        Dict with 'nodes' and 'links' arrays
    """
    search_summary = _format_search_for_graph(search_data)

    messages = [
        {"role": "system", "content": _GRAPH_SYSTEM},
        {"role": "user", "content": f"领域: {domain}\n\n搜索数据:\n{search_summary}\n\n请提取知识图谱（最多{max_nodes}个节点）。"},
    ]

    try:
        result = await chat_deep_json(messages, temperature=0.3, max_tokens=4096)
        graph = _validate_graph(result, domain)
        return graph
    except Exception as exc:
        log.warning("Graph extraction failed: %s, using fallback", exc)
        return _fallback_graph(domain, search_data)


def _format_search_for_graph(data: dict) -> str:
    """Format search results into a concise summary for graph extraction."""
    parts = []

    for key, label in [("peers", "同行内容"), ("bloggers", "博主"), ("news", "动态"), ("trending", "热搜")]:
        items = data.get(key, [])
        if not items:
            continue
        lines = []
        for i, item in enumerate(items[:50], 1):
            title = getattr(item, "title", item.get("title", "")) if isinstance(item, dict) else item.title
            snippet = getattr(item, "snippet", item.get("snippet", "")) if isinstance(item, dict) else item.snippet
            lines.append(f"  {i}. {title}: {snippet[:100]}")
        parts.append(f"[{label}]\n" + "\n".join(lines))

    return "\n\n".join(parts)


_TYPE_COLORS = {
    "person": "#6366f1",
    "topic": "#f59e0b",
    "platform": "#10b981",
    "format": "#ec4899",
    "audience": "#06b6d4",
}


def _validate_graph(data: dict | list, domain: str) -> dict:
    """Validate and normalize graph data."""
    if isinstance(data, list):
        data = {"nodes": data, "links": []}

    nodes = data.get("nodes", [])
    links = data.get("links", [])

    node_ids = set()
    valid_nodes = []
    for n in nodes:
        if not isinstance(n, dict) or "id" not in n:
            continue
        n.setdefault("name", n["id"])
        n.setdefault("type", "topic")
        n.setdefault("val", 5)
        n.setdefault("desc", "")
        n["color"] = _TYPE_COLORS.get(n["type"], "#94a3b8")
        node_ids.add(n["id"])
        valid_nodes.append(n)

    valid_links = []
    for link in links:
        if not isinstance(link, dict):
            continue
        src = link.get("source", "")
        tgt = link.get("target", "")
        if src in node_ids and tgt in node_ids:
            link.setdefault("label", "")
            link.setdefault("strength", 0.5)
            valid_links.append(link)

    if not valid_nodes:
        return _fallback_graph(domain, {})

    return {"nodes": valid_nodes, "links": valid_links}


def _fallback_graph(domain: str, data: dict) -> dict:
    """Generate a minimal graph when LLM extraction fails."""
    nodes = [
        {"id": "domain", "name": domain, "type": "topic", "val": 25, "color": _TYPE_COLORS["topic"], "desc": f"{domain}领域"},
        {"id": "xhs", "name": "小红书", "type": "platform", "val": 15, "color": _TYPE_COLORS["platform"], "desc": "种草平台"},
        {"id": "bili", "name": "B站", "type": "platform", "val": 15, "color": _TYPE_COLORS["platform"], "desc": "视频平台"},
        {"id": "douyin", "name": "抖音", "type": "platform", "val": 15, "color": _TYPE_COLORS["platform"], "desc": "短视频平台"},
        {"id": "wx", "name": "视频号", "type": "platform", "val": 12, "color": _TYPE_COLORS["platform"], "desc": "微信生态"},
        {"id": "video", "name": "短视频", "type": "format", "val": 10, "color": _TYPE_COLORS["format"], "desc": "主流内容形式"},
        {"id": "graphic", "name": "图文", "type": "format", "val": 8, "color": _TYPE_COLORS["format"], "desc": "图文内容"},
        {"id": "young", "name": "年轻用户", "type": "audience", "val": 10, "color": _TYPE_COLORS["audience"], "desc": "18-35岁"},
    ]

    peers = data.get("peers", [])
    for i, p in enumerate(peers[:5]):
        title = getattr(p, "title", "") if hasattr(p, "title") else p.get("title", f"话题{i+1}")
        nodes.append({"id": f"topic_{i}", "name": title[:15], "type": "topic", "val": 8, "color": _TYPE_COLORS["topic"], "desc": title[:50]})

    bloggers = data.get("bloggers", [])
    for i, b in enumerate(bloggers[:5]):
        title = getattr(b, "title", "") if hasattr(b, "title") else b.get("title", f"博主{i+1}")
        name = title.split("_")[0].split("-")[0].split("|")[0][:10]
        nodes.append({"id": f"person_{i}", "name": name, "type": "person", "val": 12, "color": _TYPE_COLORS["person"], "desc": title[:50]})

    links = [
        {"source": "domain", "target": "xhs", "label": "热门于", "strength": 0.8},
        {"source": "domain", "target": "bili", "label": "热门于", "strength": 0.7},
        {"source": "domain", "target": "douyin", "label": "热门于", "strength": 0.7},
        {"source": "domain", "target": "wx", "label": "热门于", "strength": 0.5},
        {"source": "domain", "target": "video", "label": "适合", "strength": 0.6},
        {"source": "domain", "target": "graphic", "label": "适合", "strength": 0.5},
        {"source": "domain", "target": "young", "label": "面向", "strength": 0.6},
    ]

    node_ids = {n["id"] for n in nodes}
    for n in nodes:
        if n["id"].startswith("topic_") and "domain" in node_ids:
            links.append({"source": "domain", "target": n["id"], "label": "衍生", "strength": 0.6})
        if n["id"].startswith("person_"):
            links.append({"source": n["id"], "target": "domain", "label": "擅长", "strength": 0.7})
            links.append({"source": n["id"], "target": "xhs", "label": "创作于", "strength": 0.5})

    return {"nodes": nodes, "links": links}
