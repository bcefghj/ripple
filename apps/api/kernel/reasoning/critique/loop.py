"""Self-Critique Loop - 生成→批评→修订迭代

仿 SELF-REFINE 论文。停止条件:
1. Critic 给出 0 条建议
2. 达到 max_rounds (默认 3)
3. 风险/可读性能量函数收敛

每轮记录到 ReplayGraph,展示给评委的是最终稿+迭代次数。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import List, Optional

from ...cognition.llm import quick_chat


@dataclass
class CritiqueRound:
    round_index: int
    draft: str
    issues: List[str] = field(default_factory=list)
    revised: str = ""
    energy: float = 1.0


@dataclass
class CritiqueResult:
    final_text: str
    rounds: List[CritiqueRound] = field(default_factory=list)
    total_iterations: int = 0
    converged: bool = False


class SelfCritiqueLoop:
    """生成-批评-修订循环"""

    async def run(
        self,
        initial_draft: str,
        topic: str,
        constraints: str = "",
        max_rounds: int = 3,
        energy_threshold: float = 0.2,
    ) -> CritiqueResult:
        rounds: List[CritiqueRound] = []
        current = initial_draft

        for r in range(max_rounds):
            issues = await self._critique(current, topic, constraints)
            energy = min(1.0, len(issues) / 5.0)

            round_obj = CritiqueRound(
                round_index=r + 1,
                draft=current,
                issues=issues,
                energy=energy,
            )

            if not issues or energy < energy_threshold:
                round_obj.revised = current
                rounds.append(round_obj)
                return CritiqueResult(
                    final_text=current, rounds=rounds,
                    total_iterations=r + 1, converged=True,
                )

            revised = await self._revise(current, issues, topic, constraints)
            round_obj.revised = revised
            rounds.append(round_obj)
            current = revised

        return CritiqueResult(
            final_text=current, rounds=rounds,
            total_iterations=max_rounds, converged=False,
        )

    async def _critique(self, draft: str, topic: str, constraints: str) -> List[str]:
        sys = (
            "你是严格的 KOC 内容审稿人。从下面 5 个维度审视草稿,列出具体问题:\n"
            "1. 风险/合规 (广告法/夸大功效/政治敏感)\n"
            "2. 风格一致性 (是否符合人设)\n"
            "3. 信息密度 (是否冗长或太碎)\n"
            "4. 钩子/吸引力 (前 3 秒是否抓眼球)\n"
            "5. 真实性 (是否有未支持的断言)\n"
            "输出严格 JSON: {issues: [短描述, ...]}. 没问题就返回空列表。\n"
            "注意: 严格,但不要无中生有。"
        )
        user = f"主题: {topic}\n约束: {constraints}\n\n草稿:\n{draft[:2500]}"
        try:
            text = await quick_chat(sys, user, json_mode=True, max_tokens=600, temperature=0.4)
            data = json.loads(text)
            issues = data.get("issues", []) or []
            return [str(i)[:200] for i in issues if i]
        except Exception:
            return []

    async def _revise(
        self, draft: str, issues: List[str], topic: str, constraints: str
    ) -> str:
        if not issues:
            return draft
        sys = (
            "你是 KOC 内容修订专家。根据审稿人的问题清单,修订草稿,只修复明确的问题,"
            "不要扩写或改变核心立场。保持长度在 ±15% 范围内。"
        )
        user = (
            f"主题: {topic}\n约束: {constraints}\n\n"
            f"原稿:\n{draft[:2500]}\n\n"
            f"审稿问题:\n" + "\n".join(f"- {i}" for i in issues)
        )
        try:
            return (await quick_chat(sys, user, max_tokens=2000, temperature=0.5)).strip()
        except Exception:
            return draft


_singleton: Optional[SelfCritiqueLoop] = None


def get_critique_loop() -> SelfCritiqueLoop:
    global _singleton
    if _singleton is None:
        _singleton = SelfCritiqueLoop()
    return _singleton
