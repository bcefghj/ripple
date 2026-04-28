"""TopicStrategistAgent - 矛盾推理(借鉴 Digital Oracle)

核心思路:
- 不同信号源给出不同信号(可能矛盾)
- 不要简单平均,而要寻找"为什么可以同时正确"
- 用解释性的矛盾推理,告诉 KOC「这个话题在 A 平台火 B 平台不火,适合做差异化切入」

输入: OracleAgent 的早期信号报告 + ForumDebateAgent 的辩论结果
输出: 结构化选题策略 (TopicStrategy)
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, List, Optional

from loguru import logger


@dataclass
class TopicStrategy:
    """选题策略"""
    primary_topic: str  # 主选题
    angle: str  # 切入角度
    narrative: str  # 叙事线
    target_platforms: List[str]  # 目标平台 + 优先级
    target_audience: str  # 目标受众
    publishing_window_days: int  # 建议窗口期
    confidence: float  # 0-1
    contradictions_resolved: List[str]  # 已解决的矛盾
    risks: List[str] = field(default_factory=list)
    backup_topics: List[str] = field(default_factory=list)  # 备选


class TopicStrategistAgent:
    """选题策略师"""

    def __init__(self, llm_call: Callable[..., Awaitable[Dict[str, Any]]]):
        self.llm_call = llm_call

    async def strategize(
        self,
        oracle_report: Dict[str, Any],
        debate_result: Optional[Dict[str, Any]] = None,
        koc_style: Optional[str] = None,
        koc_constraints: Optional[str] = None,
    ) -> TopicStrategy:
        """
        基于 Oracle + Debate 输出最终选题策略
        
        Args:
            oracle_report: OracleAgent 的早期信号报告 (JSON dict)
            debate_result: ForumDebateAgent 的辩论结果(可选)
            koc_style: KOC 风格卡片字符串
            koc_constraints: KOC 的约束(品牌方红线/平台限制)
        """
        # 准备上下文
        oracle_summary = self._summarize_oracle(oracle_report)
        debate_summary = self._summarize_debate(debate_result) if debate_result else "(无辩论数据)"

        prompt = f"""你是 Ripple 的「选题策略师」,借鉴 Digital Oracle 的矛盾推理思想。

# 早期信号报告(来自 OracleAgent)
{oracle_summary}

# 多 Agent 辩论结果
{debate_summary}

# KOC 风格
{koc_style or "(默认风格)"}

# 约束
{koc_constraints or "(无特殊约束)"}

---

# 你的任务

1. **找矛盾,不要回避**: 不同信号源/不同 Agent 可能给出矛盾建议。
   不要简单平均,而要解释"为什么矛盾可以同时正确"。

2. **选定 1 个主选题**: 给出最强的早期信号 + 最适合该 KOC 风格的 angle。

3. **解释 angle 的稀缺性**: 为什么这个角度别人都没做(或做得不好)?

4. **窗口期**: 这个选题应该在几天内执行?为什么?

5. **备选 2-3 个**: 万一主选题翻车,有什么备份?

请输出 JSON:
{{
  "primary_topic": "主选题",
  "angle": "切入角度(50 字内)",
  "narrative": "完整叙事线(200 字内,告诉 KOC 怎么讲这个故事)",
  "target_platforms": ["平台1", "平台2"],
  "target_audience": "目标受众一句话",
  "publishing_window_days": 5,
  "confidence": 0.75,
  "contradictions_resolved": ["矛盾1的解释", "矛盾2的解释"],
  "risks": ["风险1", "风险2"],
  "backup_topics": ["备选1", "备选2"]
}}
"""

        try:
            response = await self.llm_call(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.5,
            )
            content = response.get("message", {}).get("content", "")
            json_match = re.search(r"\{[\s\S]*\}", content)
            if not json_match:
                return self._default_strategy(oracle_report)

            data = json.loads(json_match.group())
            return TopicStrategy(
                primary_topic=data.get("primary_topic", "待定"),
                angle=data.get("angle", ""),
                narrative=data.get("narrative", ""),
                target_platforms=data.get("target_platforms", []),
                target_audience=data.get("target_audience", ""),
                publishing_window_days=int(data.get("publishing_window_days", 7)),
                confidence=float(data.get("confidence", 0.5)),
                contradictions_resolved=data.get("contradictions_resolved", []),
                risks=data.get("risks", []),
                backup_topics=data.get("backup_topics", []),
            )
        except Exception as e:
            logger.warning(f"策略生成失败: {e}")
            return self._default_strategy(oracle_report)

    def _summarize_oracle(self, report: Dict[str, Any]) -> str:
        """简化 Oracle 报告"""
        trends = report.get("trends", [])
        if not trends:
            return "(无早期信号)"
        lines = [f"扫描了 {report.get('sources_succeeded', 0)} 个数据源\n"]
        for i, t in enumerate(trends[:5], 1):
            lines.append(
                f"{i}. {t.get('topic', '')} (置信度 {t.get('confidence', 0):.2f}, 窗口 {t.get('horizon_days', 0)} 天)\n"
                f"   依据: {t.get('explanation', '')[:200]}"
            )
        return "\n".join(lines)

    def _summarize_debate(self, debate: Dict[str, Any]) -> str:
        """简化辩论结果"""
        if not debate:
            return "(无辩论数据)"
        consensus = "; ".join(debate.get("consensus_points", []))
        dissent = "; ".join(debate.get("dissenting_views", []))
        return f"""主持人决策: {debate.get('final_decision', '')}
共识: {consensus}
分歧: {dissent}
建议行动: {debate.get('recommended_action', '')}
"""

    def _default_strategy(self, oracle_report: Dict[str, Any]) -> TopicStrategy:
        trends = oracle_report.get("trends", [])
        primary = trends[0] if trends else {}
        return TopicStrategy(
            primary_topic=primary.get("topic", "待选题"),
            angle="主流跟风(策略生成失败回退)",
            narrative="数据不足,建议人工 review",
            target_platforms=primary.get("best_platforms", ["xhs"]),
            target_audience="通用",
            publishing_window_days=primary.get("horizon_days", 7),
            confidence=primary.get("confidence", 0.3),
            contradictions_resolved=[],
            risks=["策略生成失败,数据不可靠"],
            backup_topics=[t.get("topic", "") for t in trends[1:4]],
        )
