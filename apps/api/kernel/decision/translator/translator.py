"""CrossPlatformTranslator - 跨平台改写

输入: 一段源内容 (HN 帖子, 论文摘要, 中文长文)
输出: 多个平台对应的内容包 (小红书 / 视频号 / B 站 / 抖音 / 微信公众号)

每平台模板:
- 钩子句 (前 3 秒抓注意力)
- 主体结构
- 信息密度
- 风险提示
"""

from __future__ import annotations

import asyncio
import json
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from ...cognition.llm import quick_chat


PLATFORM_GRAMMARS = {
    "xhs": {
        "name": "小红书",
        "structure": "封面文字钩子 + 信息图清单 + 评论区引导",
        "tone": "亲切真诚, emoji 适度, 第一人称, 段落短",
        "length": "300-600 字",
        "first_3s": "封面金句 + 大字感叹",
        "taboos": ["硬广", "夸大功效", "过度营销"],
    },
    "douyin": {
        "name": "抖音",
        "structure": "15s 钩子 + 反转 + 信息密度 + CTA",
        "tone": "口语化, 节奏快, 信息冲击",
        "length": "60-100 字脚本",
        "first_3s": "强反差金句 + 视觉冲击",
        "taboos": ["冗长解释", "无视觉钩子"],
    },
    "wechat_video": {
        "name": "视频号",
        "structure": "信任开场 + 慢节奏讲解 + 熟人圈推荐感",
        "tone": "稳重靠谱, 故事感, 适度专业",
        "length": "90-180s 脚本",
        "first_3s": "你身边可能也有...的故事",
        "taboos": ["浮夸", "贩卖焦虑"],
    },
    "bilibili": {
        "name": "B站",
        "structure": "标题党钩子 + 系统讲解 + 弹幕引导 + 信息丰富",
        "tone": "深度专业, 适度玩梗, 学术气质",
        "length": "5-15 分钟脚本",
        "first_3s": "几乎没人讨论...其实背后是...",
        "taboos": ["碎片化", "不严谨"],
    },
    "wechat_official": {
        "name": "微信公众号",
        "structure": "新闻钩子 + 多段深度 + 配图 + 总结",
        "tone": "正式严谨, 数据论证",
        "length": "1500-3000 字",
        "first_3s": "标题 + 副标题 + 第一段引语",
        "taboos": ["碎片化", "无数据", "口语化"],
    },
    "weibo": {
        "name": "微博",
        "structure": "话题标签 + 短论断 + @相关账号",
        "tone": "话题感, 议题驱动",
        "length": "140-300 字",
        "first_3s": "#话题# 开头钩子",
        "taboos": ["太长", "无话题标签"],
    },
}


class PlatformPack(BaseModel):
    """单平台内容包"""
    platform: str
    title: str
    content: str
    hook: str = ""
    cta: str = ""
    taboos_check: List[str] = Field(default_factory=list)
    estimated_length: int = 0
    raw_source_url: str = ""


class CrossPlatformTranslator:
    async def translate(
        self,
        source_text: str,
        source_url: str = "",
        target_platforms: Optional[List[str]] = None,
        persona_constraint: str = "",
    ) -> List[PlatformPack]:
        """并行生成多平台版本"""
        platforms = target_platforms or list(PLATFORM_GRAMMARS.keys())
        results = await asyncio.gather(*[
            self._translate_one(source_text, source_url, p, persona_constraint)
            for p in platforms
        ])
        return [r for r in results if r is not None]

    async def _translate_one(
        self,
        source_text: str,
        source_url: str,
        platform: str,
        persona_constraint: str,
    ) -> Optional[PlatformPack]:
        gram = PLATFORM_GRAMMARS.get(platform)
        if not gram:
            return None

        sys = (
            f"你是 {gram['name']} 平台爆款内容专家。把源材料改写为符合该平台特点的内容。\n"
            f"## 平台语法约束\n"
            f"- 结构: {gram['structure']}\n"
            f"- 语气: {gram['tone']}\n"
            f"- 长度: {gram['length']}\n"
            f"- 前 3 秒/首句: {gram['first_3s']}\n"
            f"- 禁忌: 不能 {', '.join(gram['taboos'])}\n"
            "\n## 输出格式 (严格 JSON)\n"
            "{title, hook, content, cta, taboos_check (list of 命中禁忌的短描述,可空)}\n"
            "保持事实准确,做信息再设计而不是翻译。仅返回 JSON。"
        )
        if persona_constraint:
            sys += f"\n\n## 人设约束\n{persona_constraint}"

        user = f"## 源材料 ({source_url})\n{source_text[:2500]}"

        try:
            text = await quick_chat(sys, user, json_mode=True, max_tokens=1500, temperature=0.7)
            data = json.loads(text)
            content = data.get("content", "")
            return PlatformPack(
                platform=platform,
                title=data.get("title", "")[:120],
                content=content,
                hook=data.get("hook", "")[:200],
                cta=data.get("cta", "")[:120],
                taboos_check=data.get("taboos_check", []) or [],
                estimated_length=len(content),
                raw_source_url=source_url,
            )
        except Exception as e:
            return PlatformPack(
                platform=platform,
                title=f"[{gram['name']}] {source_text[:30]}",
                content=source_text[:int(gram.get("length", "300").split("-")[0]) if "-" in gram.get("length", "") else 300],
                hook="",
                cta="",
                taboos_check=[f"fallback: {e}"],
                raw_source_url=source_url,
            )


_singleton: Optional[CrossPlatformTranslator] = None


def get_translator() -> CrossPlatformTranslator:
    global _singleton
    if _singleton is None:
        _singleton = CrossPlatformTranslator()
    return _singleton
