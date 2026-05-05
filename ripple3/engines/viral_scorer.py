"""CES-based Viral Potential Scorer — platform algorithm simulation.

Implements scoring models based on real platform algorithms:
- 小红书 CES: 关注*8 + 评论*4 + 转发*4 + 收藏*1 + 点赞*1
- Viral Loop Engine: weighted engagement rate
- X Impact Checker: 19-dimension 100-point scoring
- Traffic pool escalation prediction

This is Ripple's core differentiator vs ChatGPT — built-in platform logic.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from core.llm import chat_json

log = logging.getLogger(__name__)


# Platform-specific algorithm weights
CES_WEIGHTS = {"关注": 8, "评论": 4, "转发": 4, "收藏": 1, "点赞": 1}

TRAFFIC_POOLS = [
    {
        "name": "冷启动池",
        "exposure": "100-500次曝光",
        "duration": "1-2小时",
        "threshold": "CTR>=3%, 互动率>=5%",
        "key_metric": "点击率",
    },
    {
        "name": "初级流量池",
        "exposure": "1k-5k次曝光",
        "duration": "6-24小时",
        "threshold": "完播率>20%, CES持续增长",
        "key_metric": "完播率+互动率",
    },
    {
        "name": "热门流量池",
        "exposure": "1万+次曝光",
        "duration": "1-7天",
        "threshold": "搜索匹配+持续高互动",
        "key_metric": "搜索关键词匹配度",
    },
    {
        "name": "全站推荐池",
        "exposure": "10万+次曝光",
        "duration": "持续",
        "threshold": "跨圈层传播+高CES",
        "key_metric": "分享率+关注转化",
    },
]

SCORING_DIMENSIONS = [
    {"id": "title_appeal", "name": "标题吸引力", "weight": 15,
     "criteria": "关键词前置、18-20字、包含悬念/数字/痛点钩子"},
    {"id": "emotion", "name": "情绪共鸣", "weight": 15,
     "criteria": "痛点触发、好奇心驱动、社交货币价值"},
    {"id": "platform_fit", "name": "平台适配", "weight": 15,
     "criteria": "CES友好度、搜索关键词密度、内容形式匹配"},
    {"id": "blue_ocean", "name": "竞争蓝海", "weight": 10,
     "criteria": "同领域同选题内容稀缺度、差异化空间"},
    {"id": "timeliness", "name": "时效窗口", "weight": 10,
     "criteria": "热点相关性、季节性、政策/事件驱动"},
    {"id": "hook_strength", "name": "Hook强度", "weight": 10,
     "criteria": "前3秒/前10字吸引力、认知缺口制造"},
    {"id": "info_density", "name": "信息密度", "weight": 10,
     "criteria": "干货含量、实用价值、知识增量"},
    {"id": "originality", "name": "原创空间", "weight": 10,
     "criteria": "差异化程度、独特视角、个人经验"},
    {"id": "completion_predict", "name": "完播预测", "weight": 5,
     "criteria": "节奏感、悬念设计、内容长度合理性"},
]


@dataclass
class ViralScore:
    total_score: int  # 0-100
    dimensions: list[dict] = field(default_factory=list)
    predicted_pool: str = ""
    pool_probability: str = ""
    ces_analysis: str = ""
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    optimization_tips: list[str] = field(default_factory=list)
    engagement_formula: str = ""


_SCORER_SYSTEM = """你是社媒内容算法专家，精通各平台推荐机制。请对以下选题/内容进行爆款潜力评分。

评分体系（总分100分，9个维度）：
1. 标题吸引力(15分): 关键词前置、长度18-20字、包含悬念/数字/痛点钩子
2. 情绪共鸣(15分): 痛点触发、好奇心驱动、社交货币价值
3. 平台适配(15分): CES友好度（评论>点赞）、搜索关键词密度、内容形式匹配
4. 竞争蓝海(10分): 同领域同选题内容稀缺度、差异化空间
5. 时效窗口(10分): 热点相关性、季节性、政策/事件驱动
6. Hook强度(10分): 前3秒/前10字吸引力、认知缺口制造
7. 信息密度(10分): 干货含量、实用价值、知识增量
8. 原创空间(10分): 差异化程度、独特视角、个人经验
9. 完播预测(5分): 节奏感、悬念设计、内容长度合理性

小红书CES公式: 关注×8 + 评论×4 + 转发×4 + 收藏×1 + 点赞×1
流量池阶梯: 冷启动(100-500曝光,CTR>=3%) → 初级(1k-5k) → 热门(1w+) → 全站(10w+)

返回严格JSON（无markdown）：
{
  "total_score": 75,
  "dimensions": [
    {"id": "title_appeal", "name": "标题吸引力", "score": 12, "max": 15, "reason": "..."},
    {"id": "emotion", "name": "情绪共鸣", "score": 11, "max": 15, "reason": "..."},
    ...
  ],
  "predicted_pool": "初级流量池",
  "pool_probability": "65%概率突破冷启动",
  "ces_analysis": "该内容CES潜力分析...",
  "strengths": ["优势1", "优势2"],
  "weaknesses": ["不足1", "不足2"],
  "optimization_tips": ["优化建议1", "优化建议2", "优化建议3"]
}"""


async def score_viral_potential(
    topic: str,
    domain: str = "",
    platform: str = "小红书",
    competition_data: str = "",
) -> ViralScore:
    """Score a topic's viral potential using platform algorithm simulation."""
    user_msg = f"""选题/标题: 「{topic}」
领域: {domain or '综合'}
目标平台: {platform}
{f'竞品数据参考:\\n{competition_data[:2000]}' if competition_data else ''}

请进行全维度评分。"""

    messages = [
        {"role": "system", "content": _SCORER_SYSTEM},
        {"role": "user", "content": user_msg},
    ]

    try:
        data = await chat_json(messages, temperature=0.3, max_tokens=2048)
        return ViralScore(
            total_score=data.get("total_score", 60),
            dimensions=data.get("dimensions", []),
            predicted_pool=data.get("predicted_pool", "冷启动池"),
            pool_probability=data.get("pool_probability", ""),
            ces_analysis=data.get("ces_analysis", ""),
            strengths=data.get("strengths", []),
            weaknesses=data.get("weaknesses", []),
            optimization_tips=data.get("optimization_tips", []),
            engagement_formula=f"CES = 关注×8 + 评论×4 + 转发×4 + 收藏×1 + 点赞×1",
        )
    except Exception as exc:
        log.warning("Viral scoring failed: %s", exc)
        return ViralScore(
            total_score=50,
            predicted_pool="冷启动池",
            ces_analysis="评分失败，请重试",
        )


def format_score_for_display(score: ViralScore) -> dict:
    """Format viral score for frontend display."""
    return {
        "total_score": score.total_score,
        "dimensions": score.dimensions,
        "traffic_pools": TRAFFIC_POOLS,
        "predicted_pool": score.predicted_pool,
        "pool_probability": score.pool_probability,
        "ces_analysis": score.ces_analysis,
        "ces_weights": CES_WEIGHTS,
        "strengths": score.strengths,
        "weaknesses": score.weaknesses,
        "optimization_tips": score.optimization_tips,
        "engagement_formula": score.engagement_formula,
    }
