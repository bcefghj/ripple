"""ScriptWriterAgent - 多平台多版本文案生成

调 MiniMax M2.7 长上下文,一次性生成 6 个平台的差异化版本
- 视频号 30-60 秒口播
- 微信公众号深度长文
- 小红书图文(标题+正文+tag)
- 抖音 15 秒强冲击
- B 站中长视频
- 微博 140 字
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, List, Optional

from loguru import logger


@dataclass
class PlatformContent:
    """单平台内容"""
    platform: str
    format: str
    title: str = ""
    body: str = ""
    captions: str = ""
    tags: List[str] = field(default_factory=list)
    cover_text: str = ""
    additional: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TitleCandidate:
    """标题候选"""
    text: str
    formula: str  # 数字/否定/反差/时效/痛点/好奇缺口/人设
    platforms: List[str]
    score: float = 0.0  # 0-10 自检分


@dataclass
class ContentPackage:
    """完整内容包"""
    creative_brief: Dict[str, Any]
    platforms: Dict[str, PlatformContent]
    title_candidates: List[TitleCandidate]
    cover_descriptions: List[Dict[str, Any]]


PLATFORM_RULES = {
    "channels": {
        "format": "30-60 秒口播",
        "max_length": 600,
        "key_points": "强社交链路,设计可转发理由,评论区互动",
    },
    "wechat_official": {
        "format": "深度长文 1500-3000 字",
        "max_length": 3500,
        "key_points": "首屏价值高,可加目录,关键词与标题耦合",
    },
    "xhs": {
        "format": "图文 1主图+8副图",
        "max_length": 1000,
        "key_points": "首图+8字标题+第一段必须吸睛,SEO 关键词埋入",
    },
    "douyin": {
        "format": "15-30 秒强冲击",
        "max_length": 400,
        "key_points": "黄金 3 秒钩子,高密度信息,反转在 5-10 秒",
    },
    "bilibili": {
        "format": "5-10 分钟中视频",
        "max_length": 5000,
        "key_points": "开头问题链,中段信息密度,留存曲线",
    },
    "weibo": {
        "format": "140 字 + 图",
        "max_length": 200,
        "key_points": "一句观点+一张可转发图",
    },
}


class ScriptWriterAgent:
    """多平台文案生成"""

    def __init__(self, llm_call: Callable[..., Awaitable[Dict[str, Any]]]):
        self.llm_call = llm_call

    async def generate(
        self,
        topic: str,
        angle: str,
        narrative: str,
        target_platforms: List[str],
        style_card_text: Optional[str] = None,
        target_audience: str = "通用",
    ) -> ContentPackage:
        """生成完整内容包"""

        # 1) 并行生成各平台版本(实际可一次调用 + JSON 输出)
        package_data = await self._generate_full_package(
            topic, angle, narrative, target_platforms, style_card_text, target_audience
        )

        # 2) 构造结构化结果
        platforms_dict = {}
        for plat in target_platforms:
            data = package_data.get("platforms", {}).get(plat, {})
            platforms_dict[plat] = PlatformContent(
                platform=plat,
                format=PLATFORM_RULES.get(plat, {}).get("format", ""),
                title=data.get("title", ""),
                body=data.get("body", ""),
                captions=data.get("captions", ""),
                tags=data.get("tags", []),
                cover_text=data.get("cover_text", ""),
                additional=data.get("additional", {}),
            )

        title_candidates = [
            TitleCandidate(
                text=t.get("text", ""),
                formula=t.get("formula", "未分类"),
                platforms=t.get("platforms", []),
                score=float(t.get("score", 5.0)),
            )
            for t in package_data.get("title_candidates", [])
        ]

        return ContentPackage(
            creative_brief=package_data.get("creative_brief", {}),
            platforms=platforms_dict,
            title_candidates=title_candidates,
            cover_descriptions=package_data.get("cover_descriptions", []),
        )

    async def _generate_full_package(
        self,
        topic: str,
        angle: str,
        narrative: str,
        platforms: List[str],
        style_card: Optional[str],
        audience: str,
    ) -> Dict[str, Any]:
        """LLM 一次生成完整 JSON 包"""
        platforms_spec = "\n".join(
            f"- **{p}**: {PLATFORM_RULES.get(p, {}).get('format', '?')} - {PLATFORM_RULES.get(p, {}).get('key_points', '')}"
            for p in platforms
        )

        style_section = f"\n# KOC 风格卡片\n{style_card}\n" if style_card else ""

        prompt = f"""你是 Ripple 的「多平台文案工厂」。基于以下信息,为 KOC 生成完整可发布内容包。

# 选题
{topic}

# 切入角度
{angle}

# 叙事线
{narrative}

# 目标受众
{audience}

# 目标平台
{platforms_spec}
{style_section}

---

# 任务

为每个目标平台生成:
1. 标题(贴合该平台风格)
2. 正文/脚本(完整可发布)
3. tags(平台特定 SEO 关键词)
4. 封面文字建议(≤5 个词)

并额外生成:
- 10 个标题候选(标注公式:数字/否定/反差/时效/痛点/好奇缺口/人设)
- 5 个封面设计描述(高对比/温和/极简/人脸/无脸)
- 创意 brief(persona/tension/promised_value)

# 风格要求
- 严格匹配 KOC 风格卡片(如有)
- 必须有"线下细节"(具体时间/地点/感受),避免 AI 味
- 句式长度抖动(短句+长句混合)
- 关键数字具体化(避免"显著"等空泛词)

# 输出 JSON
{{
  "creative_brief": {{
    "persona": "...",
    "tension": "...",
    "promised_value": "..."
  }},
  "platforms": {{
    "{platforms[0] if platforms else 'channels'}": {{
      "title": "...",
      "body": "完整文案",
      "captions": "字幕/旁白",
      "tags": ["..."],
      "cover_text": "≤5 字"
    }}
  }},
  "title_candidates": [
    {{"text": "...", "formula": "数字", "platforms": ["xhs"], "score": 8}},
    ...
  ],
  "cover_descriptions": [
    {{"style": "高对比", "main_text": "3字", "color_palette": "红黑", "description": "..."}},
    ...
  ]
}}

仅输出 JSON,不要其他说明。
"""

        try:
            response = await self.llm_call(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=4000,
                temperature=0.7,
            )
            content = response.get("message", {}).get("content", "")
            json_match = re.search(r"\{[\s\S]*\}", content)
            if not json_match:
                logger.warning("ScriptWriter 未返回有效 JSON,返回 fallback")
                return self._fallback_package(topic, platforms)
            return json.loads(json_match.group())
        except Exception as e:
            logger.error(f"ScriptWriter 失败: {e}")
            return self._fallback_package(topic, platforms)

    def _fallback_package(self, topic: str, platforms: List[str]) -> Dict[str, Any]:
        return {
            "creative_brief": {
                "persona": "通用 KOC",
                "tension": f"关于 {topic} 的探讨",
                "promised_value": "提供新视角",
            },
            "platforms": {
                p: {
                    "title": f"关于{topic}的看法",
                    "body": f"[Fallback] 这是关于 {topic} 的内容,生成失败,请重试。",
                    "captions": "",
                    "tags": [topic],
                    "cover_text": topic[:5],
                }
                for p in platforms
            },
            "title_candidates": [
                {"text": f"关于{topic}的5件事", "formula": "数字", "platforms": platforms, "score": 6}
            ],
            "cover_descriptions": [
                {"style": "高对比", "main_text": topic[:3], "color_palette": "红黑", "description": "强冲击主图"}
            ],
        }
