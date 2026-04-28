"""SimPredictor - 用 LLM 模拟虚拟受众团

核心思想 (Generative Agents 启发):
1. 定义多个虚拟人格卡 (cohort)
2. 让 LLM 扮演每个人格,对内容打分 + 给反馈
3. 聚合分数 + 不确定性区间
4. 用 Platt scaling 做校准 (此处用简易版)
"""

from __future__ import annotations

import asyncio
import json
import statistics
from typing import List, Optional

from ...types import Cohort, CohortAffinity, SimPredictionResult
from ...cognition.llm import quick_chat


DEFAULT_COHORTS: List[Cohort] = [
    Cohort(
        cohort_id="young_female_t2",
        name="25-30 岁二线女性 / 美妆护肤",
        age_range=(25, 30), gender_bias="female", city_tier="2",
        interests=["美妆", "护肤", "测评", "性价比"],
    ),
    Cohort(
        cohort_id="male_student",
        name="20 岁男大学生 / 数码科技",
        age_range=(18, 22), gender_bias="male", city_tier="all",
        interests=["数码", "科技", "游戏", "AI"],
    ),
    Cohort(
        cohort_id="career_woman_t1",
        name="28-35 岁一线职场女性 / 自我成长",
        age_range=(28, 35), gender_bias="female", city_tier="1",
        interests=["职场", "理财", "成长", "高效"],
    ),
    Cohort(
        cohort_id="hobby_uncle",
        name="35-50 岁中产男性 / 兴趣爱好",
        age_range=(35, 50), gender_bias="male", city_tier="2",
        interests=["机械表", "钓鱼", "茶", "汽车"],
    ),
    Cohort(
        cohort_id="mom_t3",
        name="30-40 岁妈妈 / 母婴亲子",
        age_range=(30, 40), gender_bias="female", city_tier="3",
        interests=["育儿", "亲子", "教育", "家庭"],
    ),
]


def _platt_calibrate(raw: float) -> float:
    """简易 Platt 校准 - 未来可换成训好的参数"""
    import math
    a, b = 1.5, -0.75
    z = a * raw + b
    return 1.0 / (1.0 + math.exp(-z))


class SimPredictor:
    """虚拟受众团预测器"""

    def __init__(self, cohorts: Optional[List[Cohort]] = None) -> None:
        self.cohorts = cohorts or DEFAULT_COHORTS

    async def _ask_one_cohort(self, content: str, cohort: Cohort) -> CohortAffinity:
        sys = (
            f"你正在扮演一个真实的内容消费者:{cohort.name}。"
            f"年龄范围 {cohort.age_range},兴趣 {','.join(cohort.interests)}。"
            "你刷到下面这条内容,请像真实人一样反应,严格输出 JSON,字段:"
            "score(0-1, 你看完后的整体喜好), completion_estimate(0-1 你完播/看完概率), "
            "controversy(0-1 你是否觉得它有争议或冒犯), reason(50字以内你的真实感受)。"
            "不要伪装积极,真实即可。仅返回 JSON。"
        )
        user = f"内容:\n{content[:1500]}"
        try:
            text = await quick_chat(sys, user, json_mode=True, max_tokens=400, temperature=0.8)
            data = json.loads(text)
            score = float(data.get("score", 0.5))
            return CohortAffinity(
                cohort_id=cohort.cohort_id,
                affinity_score=_platt_calibrate(score),
                confidence_interval=(max(0.0, score - 0.15), min(1.0, score + 0.15)),
                sample_size=1,
                reasoning=data.get("reason", "")[:200],
            )
        except Exception as e:
            return CohortAffinity(
                cohort_id=cohort.cohort_id,
                affinity_score=0.5,
                confidence_interval=(0.3, 0.7),
                sample_size=0,
                reasoning=f"[fallback: {e}]",
            )

    async def predict(
        self,
        content: str,
        variant_id: str = "v1",
        cohorts: Optional[List[Cohort]] = None,
    ) -> SimPredictionResult:
        """单版本预测 - 跨多个 cohort"""
        use_cohorts = cohorts or self.cohorts
        affinities = await asyncio.gather(*[
            self._ask_one_cohort(content, c) for c in use_cohorts
        ])
        scores = [a.affinity_score for a in affinities]
        overall = statistics.mean(scores) if scores else 0.5
        std = statistics.stdev(scores) if len(scores) > 1 else 0.1
        return SimPredictionResult(
            content_variant_id=variant_id,
            overall_score=overall,
            cohort_breakdown=affinities,
            confidence_interval=(max(0.0, overall - std), min(1.0, overall + std)),
            completion_rate_estimate=overall * 0.85,
            controversy_level=0.0,
            sample_personas_consulted=len(use_cohorts),
        )

    async def race(
        self,
        variants: List[tuple[str, str]],  # [(variant_id, content), ...]
        cohorts: Optional[List[Cohort]] = None,
    ) -> List[SimPredictionResult]:
        """多版本赛马 - 并行评测所有版本"""
        use_cohorts = cohorts or self.cohorts
        results = await asyncio.gather(*[
            self.predict(content, variant_id=vid, cohorts=use_cohorts)
            for vid, content in variants
        ])
        return sorted(results, key=lambda r: r.overall_score, reverse=True)


_singleton: Optional[SimPredictor] = None


def get_sim_predictor() -> SimPredictor:
    global _singleton
    if _singleton is None:
        _singleton = SimPredictor()
    return _singleton
