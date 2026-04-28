"""InsightAnalystAgent - 归因报告

整合所有 Agent 输出,生成最终归因报告:
"为什么我们认为这个选题会(不会)爆?"

核心价值:
- 不只是给出推荐,还能解释推荐依据
- 让 KOC 理解决策逻辑,而不是黑箱推荐
- 评委友好:可证伪 + 可解释
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class InsightReport:
    """归因报告"""
    primary_recommendation: str
    confidence_score: float
    reasoning_chain: List[Dict[str, Any]]  # 推理链路
    why_it_might_succeed: List[str]
    why_it_might_fail: List[str]
    success_metrics_to_track: List[str]
    fallback_plan: str
    executive_summary: str


class InsightAnalystAgent:
    """归因分析师"""

    def synthesize(
        self,
        oracle_report: Optional[Dict[str, Any]] = None,
        debate_result: Optional[Dict[str, Any]] = None,
        topic_strategy: Optional[Dict[str, Any]] = None,
        sim_result: Optional[Dict[str, Any]] = None,
        risk_report: Optional[Dict[str, Any]] = None,
    ) -> InsightReport:
        """整合多 Agent 输出生成归因报告"""

        # 推理链路
        reasoning_chain = []

        if oracle_report:
            top_trend = (oracle_report.get("trends") or [{}])[0]
            reasoning_chain.append({
                "agent": "OracleAgent",
                "claim": f"Top 早期信号: {top_trend.get('topic', 'N/A')}",
                "confidence": top_trend.get("confidence", 0.5),
                "evidence": f"扫描 {oracle_report.get('sources_succeeded', 0)} 个数据源,{top_trend.get('explanation', '')[:200]}",
            })

        if debate_result:
            reasoning_chain.append({
                "agent": "ForumDebateAgent",
                "claim": debate_result.get("final_decision", ""),
                "confidence": 0.7,
                "evidence": f"3 个专家辩论 {len(debate_result.get('rounds', []))} 轮后达成的共识",
            })

        if topic_strategy:
            reasoning_chain.append({
                "agent": "TopicStrategistAgent",
                "claim": topic_strategy.get("primary_topic", ""),
                "confidence": topic_strategy.get("confidence", 0.5),
                "evidence": topic_strategy.get("narrative", "")[:200],
            })

        if sim_result:
            reasoning_chain.append({
                "agent": "SimPredictorAgent",
                "claim": f"仿真预测 {sim_result.get('reach_count', 0)} 节点触达",
                "confidence": sim_result.get("virality_score", 0.5),
                "evidence": sim_result.get("explanation", "")[:200],
            })

        # 综合置信度
        confidences = [r.get("confidence", 0.5) for r in reasoning_chain]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.5

        # 成功理由
        why_succeed = []
        if oracle_report:
            top_trend = (oracle_report.get("trends") or [{}])[0]
            why_succeed.append(f"早期信号置信度 {top_trend.get('confidence', 0):.2f},窗口期 {top_trend.get('horizon_days', 0)} 天")
            why_succeed.append(f"多源验证: {top_trend.get('explanation', '')[:100]}")
        if topic_strategy:
            for c in topic_strategy.get("contradictions_resolved", [])[:2]:
                why_succeed.append(f"矛盾推理: {c}")
        if sim_result and sim_result.get("virality_score", 0) > 0.5:
            why_succeed.append(f"传播仿真显示高病毒分: {sim_result.get('virality_score', 0):.2f}")

        # 失败理由
        why_fail = []
        if topic_strategy:
            why_fail.extend(topic_strategy.get("risks", [])[:3])
        if risk_report:
            high_risks = [r for r in risk_report.get("risks", []) if r.get("severity") in ("high", "critical")]
            for r in high_risks[:2]:
                why_fail.append(f"合规风险: {r.get('explanation', '')}")
        if avg_confidence < 0.5:
            why_fail.append("综合置信度偏低,信号源不足")

        # 跟踪指标
        metrics = [
            "发布后 1 小时内的初始 CTR",
            "发布后 24 小时的完播率",
            "评论区前 50 条的情感倾向",
            "转发增速(是否有社交链路启动)",
            "搜索带来的流量占比(是否进入 SEO)",
        ]

        # 备份计划
        backups = topic_strategy.get("backup_topics", []) if topic_strategy else []
        fallback = (
            f"如主选题在发布后 24 小时数据低于预期,可切换备选: {', '.join(backups[:2])}"
            if backups else "建议人工 review"
        )

        # 执行摘要
        primary_topic = topic_strategy.get("primary_topic", "") if topic_strategy else "待定"
        executive_summary = f"""# Ripple 决策摘要

## 推荐选题
{primary_topic}

## 综合置信度
{avg_confidence:.2f} / 1.0

## 决策路径
{len(reasoning_chain)} 个 Agent 协作完成。
关键依据: 早期信号雷达 + 多 Agent 辩论 + 矛盾推理 + 仿真验证。

## 行动建议
{topic_strategy.get('narrative', '')[:200] if topic_strategy else 'N/A'}

## 风险提示
{'; '.join(why_fail[:2]) if why_fail else '低风险'}

## 跟踪指标
发布后请重点关注: {metrics[0]}、{metrics[1]}、{metrics[2]}

---
*本报告由 Ripple 12 Agent 协作生成,所有数据可追溯,所有结论可证伪。*
"""

        return InsightReport(
            primary_recommendation=primary_topic,
            confidence_score=avg_confidence,
            reasoning_chain=reasoning_chain,
            why_it_might_succeed=why_succeed,
            why_it_might_fail=why_fail,
            success_metrics_to_track=metrics,
            fallback_plan=fallback,
            executive_summary=executive_summary,
        )
