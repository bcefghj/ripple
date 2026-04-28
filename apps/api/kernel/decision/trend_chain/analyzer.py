"""TrendChain - 因果链推理

四阶段:
1. capital - 资本/投融资/预测市场
2. international_buzz - 英文社区 (HN/Reddit/X)
3. cn_media - 中文科技媒体/微博
4. mass_meme - 大众化梗 / 短视频玩梗

逻辑:
- 给定种子事件,判断当前在哪个阶段
- 预测下一阶段到达时间窗
- 给 KOC 推荐插入时点 + 角度
"""

from __future__ import annotations

import json
from typing import List, Optional

from ...types import Citation, TrendChain, TrendChainStage
from ...cognition.llm import quick_chat


STAGE_TIMELINES = {
    "capital": (0, 3),
    "international_buzz": (3, 7),
    "cn_media": (7, 14),
    "mass_meme": (14, 30),
}


class TrendChainAnalyzer:
    async def analyze(
        self,
        seed_event: str,
        evidence: Optional[List[Citation]] = None,
        platform_signals: Optional[dict] = None,
    ) -> TrendChain:
        """根据当前信号判断阶段,给出未来传导预测"""
        platform_signals = platform_signals or {}

        sys = (
            "你是趋势分析师,熟悉 '资本-国际-中文-大众' 四阶段传导规律。"
            "给定种子事件 + 当前各源信号强度,判断:\n"
            "1. 当前在哪一阶段 (capital/international_buzz/cn_media/mass_meme)\n"
            "2. 未来 30 天的演化路径与时间窗\n"
            "3. KOC 适合的插入时点 (天数范围) 与角度建议 (科普向/吐槽向/玩梗向/深度向)\n"
            "输出严格 JSON,含字段:\n"
            "current_stage, stages (list of {stage, start_day, end_day, indicators, cn_coverage}),\n"
            "insertion_window (list[int, int]), angles (list of strings),\n"
            "causal_strength (0-1), explanation (50字)\n"
            "仅返回 JSON。"
        )
        user = (
            f"种子事件: {seed_event}\n"
            f"平台信号 (rank/value): {json.dumps(platform_signals, ensure_ascii=False)}\n"
            f"已有证据: {len(evidence or [])} 条"
        )

        try:
            text = await quick_chat(sys, user, json_mode=True, max_tokens=900, temperature=0.4)
            data = json.loads(text)
        except Exception:
            data = self._heuristic_fallback(seed_event, platform_signals)

        stages = []
        for s in data.get("stages", []):
            stages.append(TrendChainStage(
                stage=s.get("stage", "capital"),
                timeframe_days=(int(s.get("start_day", 0)), int(s.get("end_day", 7))),
                indicators=s.get("indicators", []) or [],
                cn_coverage=float(s.get("cn_coverage", 0.0)),
            ))

        if not stages:
            stages = self._default_stages()

        chain = TrendChain(
            seed_event=seed_event,
            stages=stages,
            current_stage=data.get("current_stage", "capital"),
            insertion_window=tuple(data.get("insertion_window", [3, 7])),
            angles=data.get("angles", ["科普向"]),
            causal_strength=float(data.get("causal_strength", 0.5)),
            historical_precedents=evidence or [],
        )
        return chain

    def _heuristic_fallback(self, seed: str, signals: dict) -> dict:
        cn_coverage = sum(1 for k in ["weibo", "douyin", "baidu", "bilibili"] if signals.get(k)) / 4.0
        intl_coverage = sum(1 for k in ["hackernews", "polymarket", "manifold"] if signals.get(k)) / 3.0
        if cn_coverage > 0.5:
            current = "mass_meme" if cn_coverage > 0.75 else "cn_media"
        elif intl_coverage > 0.3:
            current = "international_buzz"
        else:
            current = "capital"
        return {
            "current_stage": current,
            "insertion_window": [3, 7],
            "angles": ["科普向", "吐槽向"],
            "causal_strength": 0.6,
            "explanation": "(启发式回退)",
            "stages": [
                {"stage": "capital", "start_day": 0, "end_day": 3, "indicators": ["polymarket"], "cn_coverage": 0.0},
                {"stage": "international_buzz", "start_day": 3, "end_day": 7, "indicators": ["hackernews"], "cn_coverage": 0.1},
                {"stage": "cn_media", "start_day": 7, "end_day": 14, "indicators": ["weibo"], "cn_coverage": 0.4},
                {"stage": "mass_meme", "start_day": 14, "end_day": 30, "indicators": ["douyin"], "cn_coverage": 0.85},
            ],
        }

    def _default_stages(self) -> List[TrendChainStage]:
        return [
            TrendChainStage(stage="capital", timeframe_days=(0, 3), cn_coverage=0.0),
            TrendChainStage(stage="international_buzz", timeframe_days=(3, 7), cn_coverage=0.1),
            TrendChainStage(stage="cn_media", timeframe_days=(7, 14), cn_coverage=0.4),
            TrendChainStage(stage="mass_meme", timeframe_days=(14, 30), cn_coverage=0.85),
        ]


_singleton: Optional[TrendChainAnalyzer] = None


def get_trend_chain_analyzer() -> TrendChainAnalyzer:
    global _singleton
    if _singleton is None:
        _singleton = TrendChainAnalyzer()
    return _singleton
