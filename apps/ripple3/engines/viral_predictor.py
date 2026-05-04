"""Viral Predictor — multi-dimensional scoring with reasoning chains.

Core innovation: productising the methodology used by top content teams
(e.g. 影视飓风's HKRR model + AI click-rate prediction) so that every KOC
can benefit from data-driven topic selection.

Each dimension score includes:
  - numeric score 0-100
  - reasoning chain explaining why
  - evidence from search data
  - improvement suggestions
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass, field

from adapters.search import search_competition, SearchResult
from core.llm import chat_deep_json, chat_deep_stream
from engines.idea_engine import TopicIdea

log = logging.getLogger(__name__)


@dataclass
class DimensionScore:
    name: str
    score: int
    reasoning: str
    evidence: list[str] = field(default_factory=list)
    improvement: str = ""


@dataclass
class ViralScore:
    topic_heat: DimensionScore
    competition: DimensionScore
    emotion_resonance: DimensionScore
    practical_value: DimensionScore
    title_hook: DimensionScore
    platform_fit: DimensionScore
    originality_space: DimensionScore
    timing_window: DimensionScore
    hkrr_happiness: DimensionScore
    hkrr_knowledge: DimensionScore
    hkrr_resonance: DimensionScore
    hkrr_rhythm: DimensionScore
    total: int = 0
    star_rating: str = ""
    verdict: str = ""
    overall_suggestion: str = ""
    competitor_analysis: str = ""

    def __post_init__(self):
        core_dims = [
            self.topic_heat, self.competition, self.emotion_resonance,
            self.practical_value, self.title_hook, self.platform_fit,
            self.originality_space, self.timing_window,
        ]
        hkrr_dims = [
            self.hkrr_happiness, self.hkrr_knowledge,
            self.hkrr_resonance, self.hkrr_rhythm,
        ]
        core_avg = sum(d.score for d in core_dims) / len(core_dims)
        hkrr_avg = sum(d.score for d in hkrr_dims) / len(hkrr_dims)
        self.total = round(core_avg * 0.6 + hkrr_avg * 0.4)

        if self.total >= 90:
            self.star_rating = "★★★★★"
        elif self.total >= 75:
            self.star_rating = "★★★★☆"
        elif self.total >= 60:
            self.star_rating = "★★★☆☆"
        elif self.total >= 40:
            self.star_rating = "★★☆☆☆"
        else:
            self.star_rating = "★☆☆☆☆"

    @property
    def all_dimensions(self) -> list[DimensionScore]:
        return [
            self.topic_heat, self.competition, self.emotion_resonance,
            self.practical_value, self.title_hook, self.platform_fit,
            self.originality_space, self.timing_window,
            self.hkrr_happiness, self.hkrr_knowledge,
            self.hkrr_resonance, self.hkrr_rhythm,
        ]


@dataclass
class PredictedIdea:
    idea: TopicIdea
    score: ViralScore
    competition_data: list[SearchResult] = field(default_factory=list)


_SYSTEM_PROMPT = """你是一位数据驱动的内容分析师，用12维度模型预测爆款潜力（2026年视角）。

**8基础维度 + 影视飓风HKRR 4维度**：
1. topic_heat: 当前热度和搜索趋势
2. competition: 蓝海度（新鲜角度→高分）
3. emotion_resonance: 情绪共鸣力
4. practical_value: 实用价值
5. title_hook: 标题吸引力（好奇心缺口）
6. platform_fit: 平台适配（含视频号/小红书偏好）
7. originality_space: 原创空间
8. timing_window: 时效窗口
9. hkrr_happiness (H): 观看愉悦度
10. hkrr_knowledge (K): 知识可带走度
11. hkrr_resonance (R): 情感代入度
12. hkrr_rhythm (R): 节奏张弛度

评分输出：每个维度含 score(0-100), reasoning, evidence(引用搜索数据), improvement。
额外输出：competitor_analysis, overall_suggestion, verdict(🔥/✅/⚠️/❌)

分数要有区分度，reasoning 引用真实竞品数据。"""


async def predict_viral(
    ideas: list[TopicIdea],
    domain: str,
    *,
    target_platform: str = "小红书",
) -> list[PredictedIdea]:
    """Score each idea with deep reasoning. Returns sorted by total desc."""
    if not ideas:
        return []

    all_competition: dict[int, list[SearchResult]] = {}
    for i, idea in enumerate(ideas):
        comp = search_competition(idea.title)
        all_competition[i] = comp

    comp_text_parts = []
    for i, idea in enumerate(ideas):
        comp = all_competition[i]
        comp_lines = "\n".join(
            f"  - {r.title}: {r.snippet[:80]}" for r in comp[:5]
        ) or "  （未找到直接竞品）"
        comp_text_parts.append(f"[选题{i+1}] {idea.title}\n{comp_lines}")

    ideas_text = "\n\n".join(
        f"[{i+1}] {idea.title}\n"
        f"    角度: {idea.angle}\n"
        f"    受众: {idea.audience}\n"
        f"    形式: {idea.format_suggestion}\n"
        f"    灵感: {idea.inspiration_source}"
        for i, idea in enumerate(ideas)
    )

    competition_text = "\n\n".join(comp_text_parts)

    user_msg = f"""## 领域
{domain}

## 目标平台
{target_platform}

## 待评估选题列表
{ideas_text}

## 各选题的竞品搜索数据
{competition_text}

## 任务
对以上每个选题进行12维度（8基础+4 HKRR）深度评分。

返回JSON数组，每个元素包含：
- index (对应选题编号1-{len(ideas)})
- topic_heat: {{score, reasoning, evidence, improvement}}
- competition: {{score, reasoning, evidence, improvement}}
- emotion_resonance: {{score, reasoning, evidence, improvement}}
- practical_value: {{score, reasoning, evidence, improvement}}
- title_hook: {{score, reasoning, evidence, improvement}}
- platform_fit: {{score, reasoning, evidence, improvement}}
- originality_space: {{score, reasoning, evidence, improvement}}
- timing_window: {{score, reasoning, evidence, improvement}}
- hkrr_happiness: {{score, reasoning, evidence, improvement}}
- hkrr_knowledge: {{score, reasoning, evidence, improvement}}
- hkrr_resonance: {{score, reasoning, evidence, improvement}}
- hkrr_rhythm: {{score, reasoning, evidence, improvement}}
- competitor_analysis: 字符串，竞争格局分析
- overall_suggestion: 字符串，综合建议
- verdict: "🔥"/"✅"/"⚠️"/"❌"

只返回JSON数组。"""

    result = await chat_deep_json(
        [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        max_tokens=8192,
    )

    scores_list = result if isinstance(result, list) else result.get("scores", [])
    predicted: list[PredictedIdea] = []

    for entry in scores_list:
        if not isinstance(entry, dict):
            continue
        idx = entry.get("index", 0) - 1
        if idx < 0 or idx >= len(ideas):
            continue

        score = ViralScore(
            topic_heat=_parse_dim("话题热度", entry.get("topic_heat", {})),
            competition=_parse_dim("竞争蓝海", entry.get("competition", {})),
            emotion_resonance=_parse_dim("情绪共鸣", entry.get("emotion_resonance", {})),
            practical_value=_parse_dim("实用价值", entry.get("practical_value", {})),
            title_hook=_parse_dim("标题吸引力", entry.get("title_hook", {})),
            platform_fit=_parse_dim("平台适配", entry.get("platform_fit", {})),
            originality_space=_parse_dim("原创空间", entry.get("originality_space", {})),
            timing_window=_parse_dim("时效窗口", entry.get("timing_window", {})),
            hkrr_happiness=_parse_dim("H-快乐", entry.get("hkrr_happiness", {})),
            hkrr_knowledge=_parse_dim("K-知识", entry.get("hkrr_knowledge", {})),
            hkrr_resonance=_parse_dim("R-共鸣", entry.get("hkrr_resonance", {})),
            hkrr_rhythm=_parse_dim("R-节奏", entry.get("hkrr_rhythm", {})),
            verdict=entry.get("verdict", ""),
            overall_suggestion=entry.get("overall_suggestion", ""),
            competitor_analysis=entry.get("competitor_analysis", ""),
        )
        predicted.append(PredictedIdea(
            idea=ideas[idx],
            score=score,
            competition_data=all_competition.get(idx, []),
        ))

    predicted.sort(key=lambda p: p.score.total, reverse=True)
    return predicted


async def predict_single_stream(
    idea: TopicIdea,
    domain: str,
    *,
    target_platform: str = "小红书",
) -> AsyncIterator[str]:
    """Stream a detailed viral prediction report for a single topic."""
    comp_data = search_competition(idea.title)
    comp_text = "\n".join(
        f"- 【{r.title}】{r.snippet[:100]}\n  URL: {r.url}"
        for r in comp_data[:8]
    ) or "（未找到直接竞品内容）"

    system_msg = """你是一位资深社交媒体数据分析师。请对给定选题进行深度爆款潜力预测分析。

用 Markdown 格式输出，结构如下：

## 🎯 选题概览
（简要说明）

## 📊 12维度深度评分

### 基础8维度

#### 1. 话题热度 — XX/100 分
**评分理由**: ...
**数据证据**: ...
**提升建议**: ...

（同样格式分析其余7个维度）

### 🎬 影视飓风HKRR模型

#### H-快乐度 — XX/100 分
...
（同样分析K/R/R）

## 🏆 综合评分: XX/100  评级: ★★★★☆

## 🔍 竞品分析
（分析已有的同类内容，指出竞争格局）

## 💡 差异化建议
（具体的、可操作的建议）

## 📋 参考竞品
（列出搜索到的竞品内容标题和链接）

要求：每个维度的分析必须引用竞品搜索数据中的具体信息。"""

    user_msg = f"""## 选题
标题: {idea.title}
角度: {idea.angle}
受众: {idea.audience}
形式: {idea.format_suggestion}

## 领域: {domain}
## 目标平台: {target_platform}

## 竞品搜索数据
{comp_text}

请输出完整的12维度爆款潜力预测报告（Markdown格式）。"""

    async for chunk in chat_deep_stream(
        [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ],
        max_tokens=6000,
    ):
        yield chunk


def _parse_dim(name: str, data: dict | int | float) -> DimensionScore:
    if isinstance(data, (int, float)):
        return DimensionScore(name=name, score=_clamp(data))
    if not isinstance(data, dict):
        return DimensionScore(name=name, score=50)
    evidence = data.get("evidence", [])
    if isinstance(evidence, str):
        evidence = [evidence] if evidence else []
    return DimensionScore(
        name=name,
        score=_clamp(data.get("score", 50)),
        reasoning=data.get("reasoning", ""),
        evidence=evidence,
        improvement=data.get("improvement", ""),
    )


def _clamp(v: int | float, lo: int = 0, hi: int = 100) -> int:
    return max(lo, min(hi, int(v)))
