"""Content DNA analysis engine — structured extraction of viral content patterns.

Extracts the "DNA" of successful content: title patterns, hook types,
emotional curves, information density, and platform fit scores.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field, asdict
from collections.abc import AsyncIterator

from core.llm import chat, chat_deep_stream
from core.intent import _filter_think_tags

log = logging.getLogger(__name__)


@dataclass
class ContentDNA:
    title_pattern: str = ""
    hook_type: str = ""
    emotion_curve: list[str] = field(default_factory=list)
    info_density: float = 0.0
    cta_strength: float = 0.0
    platform_fit: dict[str, float] = field(default_factory=dict)
    key_elements: list[str] = field(default_factory=list)
    audience_match: str = ""
    virality_score: float = 0.0


DNA_EXTRACTION_PROMPT = """你是内容DNA分析师。你需要分析以下爆款内容样本，提取它们的共同基因。

请以**严格JSON格式**输出分析结果。按以下结构：

```json
{
  "patterns": [
    {
      "title_pattern": "标题公式描述，如'数字+反差+痛点'",
      "hook_type": "Hook类型：提问/反常识/数据/共鸣/争议/故事",
      "emotion_curve": ["高（开头吸引）", "低（制造共鸣）", "高（给出解法）"],
      "info_density": 0.8,
      "cta_strength": 0.7,
      "platform_fit": {"小红书": 0.9, "抖音": 0.7, "B站": 0.6, "视频号": 0.8, "公众号": 0.5},
      "key_elements": ["反差感", "数据支撑", "情绪共鸣"],
      "audience_match": "20-30岁城市白领女性",
      "virality_score": 0.85
    }
  ],
  "common_genes": {
    "dominant_patterns": ["最常见的标题模式"],
    "emotional_anchors": ["最有效的情绪锚点"],
    "structural_formula": "内容结构公式总结",
    "platform_ranking": {"小红书": 0.9, "抖音": 0.8},
    "golden_rules": ["规则1", "规则2", "规则3"]
  },
  "replication_guide": {
    "step1": "具体第一步",
    "step2": "具体第二步",
    "step3": "具体第三步",
    "templates": ["模板1", "模板2"]
  }
}
```

分析要求：
- info_density: 每段落包含的新信息密度 (0-1)
- cta_strength: 行动号召力 (0-1)
- virality_score: 爆款潜力 (0-1)
- platform_fit: 各平台适配度 (0-1)
- 只输出JSON，不要其他文字"""


async def analyze_content_dna(
    content_samples: list[dict],
    domain: str = "",
) -> dict:
    """Analyze content DNA from search results.

    content_samples: list of dicts with title, snippet, url
    Returns structured DNA analysis dict.
    """
    if not content_samples:
        return {"patterns": [], "common_genes": {}, "replication_guide": {}}

    samples_text = "\n\n".join(
        f"---\n标题: {s.get('title', '')}\n内容: {s.get('snippet', '')}\n来源: {s.get('url', '')}"
        for s in content_samples[:20]
    )

    messages = [
        {"role": "system", "content": DNA_EXTRACTION_PROMPT},
        {
            "role": "user",
            "content": f"领域: {domain or '综合'}\n\n以下是 {len(content_samples)} 条爆款内容样本:\n\n{samples_text}",
        },
    ]

    try:
        resp = await chat(messages, temperature=0.2, max_tokens=4000)
        from core.llm import _extract_json
        result = _extract_json(resp.content)
        return result if isinstance(result, dict) else {"patterns": [], "common_genes": {}, "replication_guide": {}}
    except Exception as exc:
        log.warning("Content DNA analysis failed: %s", exc)
        return {"patterns": [], "common_genes": {}, "replication_guide": {}}


async def stream_content_dna_analysis(
    content_samples: list[dict],
    domain: str = "",
) -> AsyncIterator[str]:
    """Stream a human-readable Content DNA analysis report."""
    if not content_samples:
        yield "没有足够的内容样本进行DNA分析。"
        return

    samples_text = "\n\n".join(
        f"- 【{s.get('title', '')}】{s.get('snippet', '')[:100]}"
        for s in content_samples[:15]
    )

    system_msg = f"""你是 Ripple 的内容DNA分析师。你要用结构化的方式分析爆款内容的基因，帮用户理解"为什么这些内容能火"。

请输出以下格式的分析报告：

## 内容DNA图谱

### 标题基因
（分析这批爆款内容的标题模式，提炼出3-5个标题公式）

### Hook基因
（分析它们的开头/Hook是怎么抓住注意力的，归纳为几种类型）

### 情绪曲线
（这些爆款内容的情绪走势有什么共同特点？）

### 信息密度
（每段内容的"新信息"占比如何？干货多还是情绪多？）

### 平台适配DNA
（这些内容基因在不同平台的表现预测）

## 可复用的创作清单
（基于以上DNA分析，给出一份新手可以直接套用的创作检查清单）

## 内容DNA指纹
| 指标 | 得分 | 说明 |
|------|------|------|
（用表格展示关键指标的量化得分）

要求：每个观点用具体的内容样本作为证据。量化指标用0-100分。"""

    user_msg = f"""领域: {domain or '综合'}
内容样本（{len(content_samples)} 条）:
{samples_text}

请输出内容DNA分析报告。"""

    async for chunk in _filter_think_tags(chat_deep_stream(
        [{"role": "system", "content": system_msg}, {"role": "user", "content": user_msg}],
        max_tokens=6000, temperature=0.5,
    )):
        yield chunk
