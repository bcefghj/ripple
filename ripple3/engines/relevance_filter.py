"""Relevance Filter Engine — ensures search results are domain-relevant.

Uses a combination of keyword matching (fast) and LLM batch classification
(accurate) to filter out irrelevant results. This directly addresses the
core problem: searching "数码科技" but getting gaming/entertainment content.

Ripple 6.1: Enhanced with original-query anchoring — extracts key entities
from the user's original input and uses them as primary relevance anchors.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

from core.llm import chat_json

log = logging.getLogger(__name__)


@dataclass
class FilterResult:
    relevant: list  # SearchResult objects that passed
    filtered: list  # SearchResult objects that were removed
    relevance_rate: float  # percentage of relevant results
    diagnostics: str  # human-readable quality assessment


async def filter_by_relevance(
    domain: str,
    results: list,
    threshold: float = 0.5,
    max_batch_size: int = 50,
) -> FilterResult:
    """Filter search results for domain relevance using a two-pass approach.

    Pass 1: Fast keyword-based pre-filter (removes obvious mismatches)
    Pass 2: LLM batch classification for borderline cases

    Ripple 6.1: Uses original query keywords as primary anchors.
    """
    if not results:
        return FilterResult(relevant=[], filtered=[], relevance_rate=0.0, diagnostics="无搜索结果")

    domain_keywords = _extract_domain_keywords(domain)
    core_keywords = _extract_core_entities(domain)

    pass1_relevant = []
    pass1_borderline = []
    pass1_irrelevant = []

    for r in results:
        text = f"{r.title} {r.snippet}".lower()

        # Priority: if ANY core entity from original query appears, it's relevant
        core_match = any(ck.lower() in text for ck in core_keywords if len(ck) >= 2)
        if core_match:
            pass1_relevant.append(r)
            continue

        score = _keyword_relevance_score(text, domain_keywords)
        if score >= 0.6:
            pass1_relevant.append(r)
        elif score >= 0.25:
            pass1_borderline.append(r)
        else:
            pass1_irrelevant.append(r)

    if pass1_borderline and len(pass1_borderline) <= max_batch_size:
        llm_relevant = await _llm_classify_batch(domain, pass1_borderline)
        pass1_relevant.extend(llm_relevant)
        final_filtered = [r for r in pass1_borderline if r not in llm_relevant]
        final_filtered.extend(pass1_irrelevant)
    else:
        final_filtered = pass1_borderline[:10] + pass1_irrelevant
        pass1_relevant.extend(pass1_borderline[10:])

    total = len(results)
    relevant_count = len(pass1_relevant)
    rate = relevant_count / total if total > 0 else 0.0

    diagnostics = (
        f"总结果: {total} | 相关: {relevant_count} ({rate:.0%}) | "
        f"过滤: {len(final_filtered)} | "
        f"核心实体匹配: {sum(1 for r in pass1_relevant if any(ck.lower() in f'{r.title} {r.snippet}'.lower() for ck in core_keywords if len(ck) >= 2))} | "
        f"LLM验证: {len(pass1_borderline)}"
    )

    log.info("Relevance filter [%s]: %s", domain, diagnostics)
    return FilterResult(
        relevant=pass1_relevant,
        filtered=final_filtered,
        relevance_rate=rate,
        diagnostics=diagnostics,
    )


def _extract_core_entities(query: str) -> list[str]:
    """Extract the most important entities from the original user query.

    These serve as hard anchors — any result containing these is considered relevant.
    """
    entities = []

    # Extract location names (city names within the query)
    city_pattern = r'(北京|上海|广州|深圳|成都|杭州|南京|武汉|重庆|西安|长沙|天津|苏州|厦门|青岛)'
    for m in re.finditer(city_pattern, query):
        entities.append(m.group(1))

    # After extracting cities, try to get the person name (text before city or event keyword)
    event_keywords = ["演唱会", "发布会", "比赛", "晚会", "直播", "新歌", "专辑", "电影", "综艺"]
    for kw in event_keywords:
        if kw in query:
            prefix = query.split(kw)[0]
            # Remove city from prefix to get person name
            for m in re.finditer(city_pattern, prefix):
                prefix = prefix.replace(m.group(1), "")
            prefix = prefix.strip()
            if 2 <= len(prefix) <= 4:
                entities.append(prefix)
            entities.append(kw)
            break

    # Split query into meaningful segments (by spaces, punctuation)
    segments = re.split(r'[，。！？、\s]+', query)
    for seg in segments:
        if len(seg) >= 2:
            entities.append(seg)

    # The full query itself is always a core entity
    if len(query) >= 2:
        entities.append(query)

    # Remove duplicates while preserving order
    seen = set()
    unique = []
    for e in entities:
        e_clean = e.strip()
        if e_clean and e_clean not in seen:
            seen.add(e_clean)
            unique.append(e_clean)

    return unique


def _extract_domain_keywords(domain: str) -> list[str]:
    """Extract search keywords from domain name and common synonyms."""
    keywords = [w for w in re.split(r'[\s，。、]+', domain) if len(w) > 1]

    synonym_map = {
        "数码": ["手机", "电脑", "笔记本", "平板", "耳机", "智能", "硬件", "芯片", "处理器",
                 "摄像", "拍照", "屏幕", "电池", "充电", "测评", "评测", "开箱", "体验",
                 "配件", "外设", "显卡", "内存", "存储", "5G", "Wi-Fi", "蓝牙"],
        "科技": ["AI", "人工智能", "技术", "创新", "发布", "新品", "旗舰", "性能",
                 "系统", "软件", "APP", "功能", "升级", "对比", "参数"],
        "美食": ["做饭", "菜谱", "餐厅", "探店", "小吃", "烹饪", "食材", "美味"],
        "穿搭": ["搭配", "服装", "时尚", "潮流", "品牌", "衣服", "鞋", "包"],
        "护肤": ["美妆", "化妆", "面膜", "精华", "防晒", "成分", "肤质"],
        "健身": ["运动", "减脂", "增肌", "训练", "饮食", "体态"],
        "旅行": ["旅游", "攻略", "景点", "打卡", "民宿", "酒店"],
        "职场": ["工作", "效率", "管理", "面试", "简历", "晋升"],
        "演唱会": ["门票", "现场", "歌手", "舞台", "粉丝", "巡演", "安可", "演出"],
        "娱乐": ["明星", "综艺", "八卦", "热搜", "粉丝", "偶像", "选秀"],
    }

    for key, synonyms in synonym_map.items():
        if key in domain:
            keywords.extend(synonyms)

    return list(set(keywords))


def _keyword_relevance_score(text: str, keywords: list[str]) -> float:
    """Quick keyword-based relevance score (0-1)."""
    if not keywords:
        return 0.5
    matches = sum(1 for kw in keywords if kw.lower() in text)
    return min(matches / max(3, len(keywords) * 0.3), 1.0)


async def _llm_classify_batch(domain: str, results: list) -> list:
    """Use LLM to classify borderline results as relevant or not."""
    if not results:
        return []

    items_text = "\n".join(
        f"{i+1}. 标题: {r.title} | 摘要: {r.snippet[:100]}"
        for i, r in enumerate(results[:30])
    )

    messages = [
        {"role": "system", "content": f"""你是内容分类专家。判断以下内容是否属于「{domain}」领域。
返回JSON: {{"relevant": [1, 3, 5, ...]}}（列出相关内容的序号）
判断标准：内容必须与{domain}直接相关，而非其他领域（如游戏、娱乐、八卦等）。"""},
        {"role": "user", "content": items_text},
    ]

    try:
        data = await chat_json(messages, temperature=0.1, max_tokens=512)
        relevant_indices = set(data.get("relevant", []))
        return [r for i, r in enumerate(results[:30]) if (i + 1) in relevant_indices]
    except Exception as exc:
        log.warning("LLM relevance classification failed: %s", exc)
        return results[:15]
