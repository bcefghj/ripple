"""Risk-Reward Scorer - 双头打分

输入: 选题文本 + 上下文
输出: (爆款潜力, 翻车风险, 监管敏感度, 推荐动作)

特征:
- 早期信号强度 (来自 Oracle)
- 监管敏感词
- 历史同类事故
- 对立叙事密度

实现: LLM 判断 + 关键词权重 + 简易校准
"""

from __future__ import annotations

import json
from typing import List, Literal, Optional

from ...types import RiskRewardScore
from ...cognition.llm import quick_chat


REGULATORY_TRIGGERS = [
    "金融产品", "投资建议", "股票", "期货", "理财", "贷款",
    "医疗", "保健品", "功效", "疗效", "治愈", "包治",
    "政治", "国家", "领导", "党派", "敏感",
    "彩票", "赌博", "博彩",
    "未成年", "色情", "暴力",
]

HIGH_REWARD_SIGNALS = [
    "数据反差", "颠覆认知", "亲身经历", "翻车", "踩雷",
    "对比测评", "性价比", "智商税", "避坑",
    "时差", "国外", "信息差",
]

CONTROVERSY_SIGNALS = [
    "diss", "撕", "骂", "翻车", "对线", "拉踩", "黑",
]


def _calibrate(score: float, gain: float = 1.5, bias: float = 0.0) -> float:
    """Platt 风格简单校准"""
    import math
    z = gain * (score - 0.5) + bias
    return 1.0 / (1.0 + math.exp(-z))


def _keyword_features(text: str) -> dict:
    text_lower = text.lower()
    reg_hits = sum(1 for kw in REGULATORY_TRIGGERS if kw in text_lower)
    reward_hits = sum(1 for kw in HIGH_REWARD_SIGNALS if kw in text_lower)
    controversy_hits = sum(1 for kw in CONTROVERSY_SIGNALS if kw in text_lower)
    return {
        "regulatory_hits": reg_hits,
        "reward_hits": reward_hits,
        "controversy_hits": controversy_hits,
    }


class RiskRewardScorer:
    async def score(
        self,
        topic_text: str,
        signal_strength: float = 0.5,
        platform: str = "general",
        category: str = "general",
    ) -> RiskRewardScore:
        feats = _keyword_features(topic_text)

        sys = (
            "你是 KOC 选题风险评估专家。判断这个选题的'爆款潜力'与'翻车风险'。"
            "输出严格 JSON,字段: potential(0-1 爆款潜力), risk(0-1 翻车风险), "
            "regulatory(low/mid/high 监管敏感度), recommendation(push/hedge/avoid), "
            "reasoning(50字以内说明)。"
            "判断原则: 数据反差/亲身经历/避坑提升潜力; 撕逼/敏感词/夸大功效提升风险。"
        )
        user = (
            f"选题: {topic_text[:500]}\n"
            f"平台: {platform}\n类别: {category}\n"
            f"早期信号强度: {signal_strength:.2f}\n"
            f"关键词命中: 监管={feats['regulatory_hits']} 爆款={feats['reward_hits']} 争议={feats['controversy_hits']}"
        )

        try:
            text = await quick_chat(sys, user, json_mode=True, max_tokens=400)
            data = json.loads(text)
            potential = float(data.get("potential", 0.5))
            risk = float(data.get("risk", 0.5))
            reg = data.get("regulatory", "low")
            rec = data.get("recommendation", "hedge")
            reasoning = data.get("reasoning", "")
        except Exception:
            potential = min(1.0, 0.4 + signal_strength * 0.4 + feats["reward_hits"] * 0.05)
            risk = min(1.0, 0.2 + feats["regulatory_hits"] * 0.15 + feats["controversy_hits"] * 0.1)
            reg = "high" if feats["regulatory_hits"] >= 2 else "mid" if feats["regulatory_hits"] == 1 else "low"
            rec = "avoid" if reg == "high" else "push" if potential > 0.65 and risk < 0.35 else "hedge"
            reasoning = "(基于关键词启发式)"

        cal_potential = _calibrate(potential, gain=1.4)
        cal_risk = _calibrate(risk, gain=1.6)

        if reg == "high":
            rec = "avoid"
        elif cal_potential > 0.7 and cal_risk < 0.4:
            rec = "push"

        return RiskRewardScore(
            potential_score=cal_potential,
            risk_score=cal_risk,
            regulatory_sensitivity=reg if reg in ("low", "mid", "high") else "low",
            recommendation=rec if rec in ("push", "hedge", "avoid") else "hedge",
            reasoning=reasoning,
            calibrated=True,
        )

    async def score_batch(self, topics: List[str], **kwargs) -> List[RiskRewardScore]:
        import asyncio
        return await asyncio.gather(*[self.score(t, **kwargs) for t in topics])


_singleton: Optional[RiskRewardScorer] = None


def get_risk_reward_scorer() -> RiskRewardScorer:
    global _singleton
    if _singleton is None:
        _singleton = RiskRewardScorer()
    return _singleton
