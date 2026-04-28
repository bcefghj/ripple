"""ForumDebateAgent - 多 Agent 论坛辩论

借鉴 BettaFish ForumEngine:
- 1 主持人(Host) + 3 专家 Agent
- 主持人发起话题 → 专家各自陈述 → 互相反驳 → 主持人裁判
- 通过"思维碰撞"减少单模型同质化偏见

3 个专家角色:
- 数据派(Data): 引用具体数字与历史案例
- 创意派(Creative): 关注独特角度与差异化
- 风险派(Risk): 找潜在合规/版权/同质化风险
"""

from __future__ import annotations

import asyncio
import json
import re
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, List, Optional

from loguru import logger


@dataclass
class DebateRound:
    """单轮辩论"""
    round_no: int
    host_prompt: str
    speaker_responses: Dict[str, str] = field(default_factory=dict)  # speaker_role -> content


@dataclass
class DebateResult:
    """辩论结果"""
    topic: str
    rounds: List[DebateRound]
    final_decision: str
    consensus_points: List[str]
    dissenting_views: List[str]
    recommended_action: str


SPEAKER_PROMPTS = {
    "data_expert": """你是 Ripple 多 Agent 辩论的「数据派专家」。
你的发言风格:
- 必须引用具体数字、历史案例、平台规律
- 反对空泛的"我觉得",必须给出可验证依据
- 用 KOC 真实痛点(参考 36 氪/克劳锐报告)
- 倾向「过去类似的话题/选题在 X 平台的表现是 Y」
""",

    "creative_expert": """你是 Ripple 多 Agent 辩论的「创意派专家」。
你的发言风格:
- 关注内容的独特角度、差异化切入
- 反对"跟风模板"和"安全选择"
- 倾向「这个角度可以做出与众不同的内容」
- 善用反差、隐喻、跨界类比
""",

    "risk_expert": """你是 Ripple 多 Agent 辩论的「风险派专家」。
你的发言风格:
- 必须指出潜在的合规/版权/平台政策风险
- 关注 AI 标识、敏感词、虚假宣传等红线
- 倾向「先把风险讲清楚再谈机会」
- 引用《AI 生成合成内容标识办法》《深度合成管理规定》等
""",
}


class ForumDebateAgent:
    """多 Agent 论坛辩论"""

    def __init__(self, llm_call: Callable[..., Awaitable[Dict[str, Any]]]):
        self.llm_call = llm_call

    async def debate(
        self,
        topic: str,
        context: Optional[str] = None,
        max_rounds: int = 2,
    ) -> DebateResult:
        """
        发起辩论
        
        Args:
            topic: 待辩论的话题(如"为美妆 KOC 推荐选题:珂润洗颜泡沫")
            context: 背景信息(如 OracleAgent 的早期信号报告)
            max_rounds: 最大辩论轮数
        """
        rounds: List[DebateRound] = []
        speakers = list(SPEAKER_PROMPTS.keys())

        # Round 1: 各自独立发表观点(并行)
        round_1_prompt = f"""【辩论开场】

议题: {topic}

{f'背景: {context}' if context else ''}

请独立发表你的核心观点(150-250 字)。基于你的角色定位,
给出明确立场:支持 / 反对 / 有条件支持。
"""

        responses_r1 = await asyncio.gather(*[
            self._speaker_speak(role, round_1_prompt)
            for role in speakers
        ])

        rounds.append(DebateRound(
            round_no=1,
            host_prompt=round_1_prompt,
            speaker_responses=dict(zip(speakers, responses_r1)),
        ))

        # Round 2 - N: 互相反驳
        for r in range(2, max_rounds + 1):
            other_views = "\n\n".join(
                f"【{role}】: {resp}"
                for role, resp in zip(speakers, responses_r1)
            )

            round_n_prompt = f"""【辩论第 {r} 轮】

上一轮各方观点:
{other_views}

请回应其他专家的观点:
1. 同意哪些(具体说明)
2. 反对哪些(给出反驳理由)
3. 你认为最终应该如何决策
"""

            responses_rn = await asyncio.gather(*[
                self._speaker_speak(role, round_n_prompt)
                for role in speakers
            ])

            rounds.append(DebateRound(
                round_no=r,
                host_prompt=round_n_prompt,
                speaker_responses=dict(zip(speakers, responses_rn)),
            ))

        # 主持人裁判
        all_views = "\n\n".join(
            f"### Round {rnd.round_no}\n" + "\n\n".join(
                f"**{role}**: {resp}" for role, resp in rnd.speaker_responses.items()
            )
            for rnd in rounds
        )

        host_decision = await self._host_decide(topic, all_views)

        return DebateResult(
            topic=topic,
            rounds=rounds,
            final_decision=host_decision.get("decision", ""),
            consensus_points=host_decision.get("consensus", []),
            dissenting_views=host_decision.get("dissent", []),
            recommended_action=host_decision.get("action", ""),
        )

    async def _speaker_speak(self, role: str, prompt: str) -> str:
        """单个 speaker 发言"""
        system_prompt = SPEAKER_PROMPTS.get(role, "")
        try:
            response = await self.llm_call(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=500,
                temperature=0.7,
            )
            return response.get("message", {}).get("content", "")
        except Exception as e:
            logger.warning(f"Speaker {role} 发言失败: {e}")
            return f"[{role} 暂时无法发言]"

    async def _host_decide(self, topic: str, all_views: str) -> Dict[str, Any]:
        """主持人最终裁判"""
        prompt = f"""你是 Ripple 多 Agent 辩论的主持人。基于以下三方专家的辩论,做最终裁决。

议题: {topic}

辩论记录:
{all_views}

请输出 JSON:
{{
  "decision": "最终决策(一句话)",
  "consensus": ["所有方都同意的关键点 3-5 条"],
  "dissent": ["仍有分歧的点 1-3 条 + 简要说明"],
  "action": "给 KOC 的具体行动建议(不超过 100 字)"
}}

要求:做"裁判",而不是简单求同存异。
"""
        try:
            response = await self.llm_call(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.4,
            )
            content = response.get("message", {}).get("content", "")
            json_match = re.search(r"\{[\s\S]*\}", content)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            logger.warning(f"主持人裁判失败: {e}")

        return {
            "decision": "辩论结果不明确,建议人工 review",
            "consensus": [],
            "dissent": [],
            "action": "等待更多数据",
        }
