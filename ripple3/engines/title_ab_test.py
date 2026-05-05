"""Title A/B Testing Engine.

Generates multiple title variants for content, scores them using AI,
and provides CTR (Click-Through Rate) predictions.
"""

from __future__ import annotations

import logging
from typing import Any

from core.llm import chat_json

log = logging.getLogger(__name__)


async def generate_title_variants(
    topic: str,
    platform: str = "小红书",
    count: int = 10,
    domain_context: str = "",
) -> dict[str, Any]:
    """Generate title variants with predicted CTR scores."""

    messages = [
        {"role": "system", "content": f"""你是一位{platform}爆款标题大师，精通平台算法和用户心理。

## 你的任务：
为给定的选题生成{count}个标题变体，并为每个标题预测CTR（点击率）。

## 标题创作原则（基于10000+爆款分析）：
1. **好奇心缺口**：制造信息差，让用户必须点进来
2. **数字锚定**：具体数字比模糊表述CTR高27%
3. **情绪唤起**：恐惧/惊喜/共鸣三大情绪驱动力
4. **身份认同**：让目标用户感觉"这说的就是我"
5. **利益承诺**：明确告诉用户"看了你能获得什么"
6. **平台原生感**：像朋友分享而非广告推销

## {platform}特殊规则：
- 小红书：标题≤20字，带emoji效果+15%，疑问句互动率高
- 视频号：前15字决定生死，口语化表达优先
- 公众号：可稍长，但前8字必须抓人

严格返回JSON：
{{
  "titles": [
    {{
      "text": "标题文本",
      "strategy": "使用的策略（好奇心/数字/情绪/身份/利益）",
      "predicted_ctr": 0.08,
      "reason": "为什么预测这个CTR",
      "emoji_variant": "带emoji的版本（仅小红书）"
    }}
  ],
  "best_pick": 0,
  "analysis": "整体标题策略分析"
}}
predicted_ctr范围：0.03-0.15（3%-15%点击率）"""},
        {"role": "user", "content": f"选题: {topic}\n平台: {platform}\n领域背景: {domain_context or '通用'}"},
    ]

    try:
        result = await chat_json(messages, temperature=0.8, max_tokens=2500)
        return result
    except Exception as e:
        log.warning("Title A/B test failed: %s", e)
        return {"titles": [], "best_pick": 0, "analysis": "生成失败"}


async def generate_hooks(
    topic: str,
    platform: str = "小红书",
    content_type: str = "短视频",
) -> dict[str, Any]:
    """Generate opening hooks for short-form content."""

    messages = [
        {"role": "system", "content": f"""你是短视频/内容开场 Hook 专家。为{content_type}生成多个强力开场。

## Hook 的核心原理：
用户在前3秒决定是否继续看。好的Hook必须在0.5秒内抓住注意力。

## Hook 类型（按效果排序）：
1. **反直觉声明** (完播率+45%): "所有人都在XXX，但真相是..."
2. **悬念陈列** (完播率+38%): "今天发生了一件让我崩溃的事..."
3. **共鸣痛点** (完播率+32%): "如果你也XXX，一定要看完..."
4. **数据冲击** (完播率+28%): "我用了3年时间发现..."
5. **场景代入** (完播率+25%): 直接展示结果/画面冲突
6. **权威背书** (完播率+20%): "作为XXX年的从业者..."

严格返回JSON：
{{
  "hooks": [
    {{
      "text": "具体的开场文案（适合{content_type}）",
      "type": "Hook类型",
      "estimated_retention_boost": "+30%",
      "delivery_note": "表达方式建议（语气/节奏/配合画面）",
      "first_frame": "推荐的第一帧画面描述"
    }}
  ],
  "strategy_note": "整体Hook策略建议",
  "avoid": ["应该避免的开场方式1", ...]
}}"""},
        {"role": "user", "content": f"选题: {topic}\n平台: {platform}\n内容类型: {content_type}"},
    ]

    try:
        result = await chat_json(messages, temperature=0.85, max_tokens=2000)
        return result
    except Exception as e:
        log.warning("Hook generation failed: %s", e)
        return {"hooks": [], "strategy_note": "生成失败", "avoid": []}
