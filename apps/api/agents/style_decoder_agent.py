"""StyleDecoderAgent - KOC 风格学习

ICL (In-Context Learning) 模式:
- 输入: 5-10 条 KOC 历史作品
- 输出: 结构化风格卡片 (StyleCard)

字段:
- 句式偏好 (短句 vs 长句)
- 口头禅
- 平均段长
- emoji 使用频率
- 语气倾向 (口语化 / 专业 / 幽默 / 温暖)
- 标志性结尾
- 反问 / 排比 / 比喻 等修辞偏好
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from typing import Any, Awaitable, Callable, Dict, List, Optional

from loguru import logger


@dataclass
class StyleCard:
    """KOC 风格卡片"""
    persona: str  # 一句话人设
    typical_sentence_length: int  # 平均句长
    sentence_length_variance: float  # 句长方差(高方差=风格抖动)
    catchphrases: List[str] = field(default_factory=list)  # 口头禅
    emoji_frequency: float = 0.0  # 每 100 字 emoji 数
    favorite_emojis: List[str] = field(default_factory=list)
    tone: str = "neutral"  # 口语化/专业/幽默/温暖/犀利
    rhetorical_devices: List[str] = field(default_factory=list)  # 反问/比喻/排比
    typical_openings: List[str] = field(default_factory=list)  # 标志性开头
    typical_endings: List[str] = field(default_factory=list)  # 标志性结尾
    forbidden_patterns: List[str] = field(default_factory=list)  # 不要写成的样子
    tags: List[str] = field(default_factory=list)


class StyleDecoderAgent:
    """从历史作品中学习 KOC 风格"""

    def __init__(self, llm_call: Callable[..., Awaitable[Dict[str, Any]]]):
        self.llm_call = llm_call

    async def decode(
        self,
        historical_works: List[Dict[str, Any]],
        koc_context: Optional[str] = None,
    ) -> StyleCard:
        """
        从历史作品中提取风格卡片
        
        Args:
            historical_works: [{title, content, platform, metrics}, ...]
            koc_context: KOC 自我介绍(可选)
        """
        if not historical_works:
            return self._default_style_card()

        # 1) 统计性特征(无需 LLM)
        stats = self._compute_statistics(historical_works)

        # 2) LLM 提取风格特征
        try:
            llm_features = await self._llm_extract_features(historical_works, koc_context)
        except Exception as e:
            logger.warning(f"LLM 风格提取失败: {e},仅使用统计特征")
            llm_features = {}

        return StyleCard(
            persona=llm_features.get("persona", "待定义"),
            typical_sentence_length=stats["avg_sentence_length"],
            sentence_length_variance=stats["sentence_length_variance"],
            catchphrases=llm_features.get("catchphrases", []),
            emoji_frequency=stats["emoji_frequency"],
            favorite_emojis=stats["top_emojis"],
            tone=llm_features.get("tone", "neutral"),
            rhetorical_devices=llm_features.get("rhetorical_devices", []),
            typical_openings=llm_features.get("typical_openings", []),
            typical_endings=llm_features.get("typical_endings", []),
            forbidden_patterns=llm_features.get("forbidden_patterns", []),
            tags=llm_features.get("tags", []),
        )

    def _compute_statistics(self, works: List[Dict[str, Any]]) -> Dict[str, Any]:
        """统计性特征"""
        all_text = ""
        sentence_lengths: List[int] = []
        emoji_count = 0
        emojis: Dict[str, int] = {}

        for w in works:
            text = w.get("content", "") or w.get("title", "")
            all_text += text + "\n"

            # 句子长度
            for s in re.split(r"[。!?\.!?\n]", text):
                s = s.strip()
                if 5 < len(s) < 200:
                    sentence_lengths.append(len(s))

            # emoji 统计
            for char in text:
                code = ord(char)
                if (
                    0x1F300 <= code <= 0x1F9FF
                    or 0x2600 <= code <= 0x27BF
                    or 0x2B00 <= code <= 0x2BFF
                ):
                    emoji_count += 1
                    emojis[char] = emojis.get(char, 0) + 1

        avg_len = sum(sentence_lengths) // len(sentence_lengths) if sentence_lengths else 0
        if sentence_lengths:
            mean = sum(sentence_lengths) / len(sentence_lengths)
            variance = sum((x - mean) ** 2 for x in sentence_lengths) / len(sentence_lengths)
        else:
            variance = 0

        text_len = len(all_text)
        emoji_freq = (emoji_count / text_len * 100) if text_len else 0

        top_emojis = sorted(emojis.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "avg_sentence_length": avg_len,
            "sentence_length_variance": variance,
            "emoji_frequency": round(emoji_freq, 2),
            "top_emojis": [e[0] for e in top_emojis],
        }

    async def _llm_extract_features(
        self,
        works: List[Dict[str, Any]],
        koc_context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """LLM 提取语义级别风格特征"""
        # 拼接最多 5 条最长的作品
        sorted_works = sorted(
            works, key=lambda w: len(w.get("content", "")), reverse=True
        )[:5]

        samples = "\n\n---\n\n".join(
            f"[平台: {w.get('platform', '?')}]\n标题: {w.get('title', '')}\n正文:\n{w.get('content', '')[:1000]}"
            for w in sorted_works
        )

        context_section = f"\nKOC 自述: {koc_context}\n" if koc_context else ""

        prompt = f"""你是 Ripple 的风格分析师。基于以下 KOC 的 {len(sorted_works)} 条历史作品,提取风格特征。
{context_section}
作品样本:
{samples}

请输出 JSON,字段:
{{
  "persona": "一句话人设描述",
  "tone": "口语化/专业/幽默/温暖/犀利 之一",
  "catchphrases": ["最常出现的 5 个口头禅或固定表达"],
  "rhetorical_devices": ["反问", "比喻", "排比", "对比" 等使用的修辞"],
  "typical_openings": ["典型开头模式 2-3 个例子"],
  "typical_endings": ["典型结尾 2-3 个例子"],
  "forbidden_patterns": ["这位 KOC 绝对不会写成的样子,如太正式/太书面/太网络化"],
  "tags": ["美妆", "测评型", "理性派" 等关键标签"]
}}

要求:从样本中实际抽取,不要虚构。
"""

        response = await self.llm_call(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500,
            temperature=0.3,
        )
        content = response.get("message", {}).get("content", "")

        # 提取 JSON
        json_match = re.search(r"\{[\s\S]*\}", content)
        if not json_match:
            return {}
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            return {}

    def _default_style_card(self) -> StyleCard:
        return StyleCard(
            persona="新创作者(尚无足够数据学习风格)",
            typical_sentence_length=30,
            sentence_length_variance=100,
            tone="口语化",
        )

    def to_prompt_context(self, card: StyleCard) -> str:
        """将风格卡片转为 LLM Prompt 上下文(供 ScriptWriter 使用)"""
        return f"""# KOC 风格卡片

**人设**: {card.persona}
**语气**: {card.tone}
**典型句长**: 约 {card.typical_sentence_length} 字
**句式抖动**: 方差 {card.sentence_length_variance:.0f}(越高越好,显得更人味)

**常用口头禅**: {', '.join(card.catchphrases) or '无'}
**爱用 emoji**: {''.join(card.favorite_emojis) or '少'} (每 100 字约 {card.emoji_frequency} 个)
**修辞偏好**: {', '.join(card.rhetorical_devices) or '无'}
**典型开头**: {' | '.join(card.typical_openings)}
**典型结尾**: {' | '.join(card.typical_endings)}

**绝不能写成的样子**:
{chr(10).join('- ' + p for p in card.forbidden_patterns) or '- 无明确禁忌'}

**Tags**: {', '.join(card.tags)}
"""
