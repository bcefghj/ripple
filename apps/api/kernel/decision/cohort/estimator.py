"""CohortAffinityEstimator - 内容对人群的吸引力

复用 SimPredictor 的 cohorts,但接口更细粒度:
- 单条内容 × 多 cohort
- 单 cohort × 多内容
- 给出"破圈建议"
"""

from __future__ import annotations

from typing import List, Optional

from ...types import Cohort, CohortAffinity
from ..sim_predictor import get_sim_predictor, DEFAULT_COHORTS


class CohortAffinityEstimator:
    def __init__(self) -> None:
        self.sim = get_sim_predictor()

    async def estimate(
        self,
        content: str,
        cohorts: Optional[List[Cohort]] = None,
    ) -> List[CohortAffinity]:
        result = await self.sim.predict(content, variant_id="estimate", cohorts=cohorts or DEFAULT_COHORTS)
        return result.cohort_breakdown

    def cross_circle_suggestion(self, affinities: List[CohortAffinity]) -> str:
        """根据各 cohort 分数差异,给出破圈建议"""
        if not affinities:
            return "无足够人群数据,建议先做小范围测试。"
        sorted_aff = sorted(affinities, key=lambda a: a.affinity_score, reverse=True)
        top = sorted_aff[0]
        bottom = sorted_aff[-1]
        gap = top.affinity_score - bottom.affinity_score
        if gap < 0.2:
            return f"内容对各人群吸引力均衡 (差距 {gap:.2f}),适合广覆盖。"
        else:
            return (
                f"内容主要吸引 {top.cohort_id} ({top.affinity_score:.2f}), "
                f"在 {bottom.cohort_id} 表现弱 ({bottom.affinity_score:.2f}). "
                f"破圈建议: 加入 {bottom.cohort_id} 共鸣点或换一个开头钩子。"
            )


_singleton: Optional[CohortAffinityEstimator] = None


def get_cohort_estimator() -> CohortAffinityEstimator:
    global _singleton
    if _singleton is None:
        _singleton = CohortAffinityEstimator()
    return _singleton
