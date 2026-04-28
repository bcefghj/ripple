"""RippleOrchestrator - 12 Agent 主调度

执行流程:
Phase 1 - 信号感知: Oracle + TrendScout + StyleDecoder (并行)
Phase 2 - 决策辩论: ForumDebate → TopicStrategist
Phase 3 - 内容生产: ScriptWriter + VisualProducer + MaterialCurator (并行)
Phase 4 - 审查发布: FactChecker + RiskReviewer + SimPredictor (并行) → InsightAnalyst

输出:
- 完整内容包(标题/封面/多平台脚本)
- 早期信号报告
- 合规审查报告
- 仿真预测
- 归因报告
"""

from __future__ import annotations

import asyncio
import json
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, AsyncIterator, Awaitable, Callable, Dict, List, Optional

from loguru import logger

from .fact_checker_agent import FactCheckerAgent, FactCheckReport
from .forum_debate_agent import DebateResult, ForumDebateAgent
from .insight_analyst_agent import InsightAnalystAgent, InsightReport
from .material_curator_agent import MaterialCuratorAgent
from .oracle_agent import OracleAgent, OracleReport
from .risk_reviewer_agent import ComplianceReport, RiskReviewerAgent
from .script_writer_agent import ContentPackage, ScriptWriterAgent
from .sim_predictor_agent import SimPredictorAgent, SimulationResult
from .style_decoder_agent import StyleCard, StyleDecoderAgent
from .topic_strategist_agent import TopicStrategistAgent, TopicStrategy
from .trend_scout_agent import TrendScoutAgent
from .visual_producer_agent import VisualProducerAgent


@dataclass
class RippleOutput:
    """完整输出"""
    request_id: str
    topic_seed: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_ms: int = 0

    # Phase 1 输出
    oracle_report: Optional[Dict[str, Any]] = None
    style_card: Optional[Dict[str, Any]] = None
    hot_topics: List[Dict[str, Any]] = field(default_factory=list)

    # Phase 2 输出
    debate_result: Optional[Dict[str, Any]] = None
    topic_strategy: Optional[Dict[str, Any]] = None

    # Phase 3 输出
    content_package: Optional[Dict[str, Any]] = None
    cover_images: List[Dict[str, Any]] = field(default_factory=list)
    materials: List[Dict[str, Any]] = field(default_factory=list)

    # Phase 4 输出
    fact_check: Optional[Dict[str, Any]] = None
    compliance: Optional[Dict[str, Any]] = None
    simulation: Optional[Dict[str, Any]] = None
    insight: Optional[Dict[str, Any]] = None

    # 错误
    errors: List[str] = field(default_factory=list)


class RippleOrchestrator:
    """12 Agent 主调度"""

    def __init__(
        self,
        llm_call: Callable[..., Awaitable[Dict[str, Any]]],
    ):
        self.llm_call = llm_call

        # 初始化所有 Agent
        self.oracle = OracleAgent()
        self.trend_scout = TrendScoutAgent()
        self.style_decoder = StyleDecoderAgent(llm_call)
        self.forum_debate = ForumDebateAgent(llm_call)
        self.topic_strategist = TopicStrategistAgent(llm_call)
        self.script_writer = ScriptWriterAgent(llm_call)
        self.visual_producer = VisualProducerAgent()
        self.material_curator = MaterialCuratorAgent()
        self.fact_checker = FactCheckerAgent(llm_call)
        self.risk_reviewer = RiskReviewerAgent(llm_call)
        self.sim_predictor = SimPredictorAgent()
        self.insight_analyst = InsightAnalystAgent()

    async def run(
        self,
        topic_seed: str,
        category: str = "通用",
        target_platforms: Optional[List[str]] = None,
        koc_works: Optional[List[Dict[str, Any]]] = None,
        koc_context: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> RippleOutput:
        """完整流水线(非流式)"""
        target_platforms = target_platforms or ["channels", "wechat_official", "xhs", "douyin"]
        koc_works = koc_works or []
        request_id = request_id or f"req-{int(time.time())}"

        output = RippleOutput(
            request_id=request_id,
            topic_seed=topic_seed,
            started_at=datetime.now(),
        )

        try:
            # ============ Phase 1 - 并行 ============
            logger.info(f"[{request_id}] Phase 1: 信号感知 (并行)")
            phase1_results = await asyncio.gather(
                self.oracle.scan(topic_seed, category, target_platforms),
                self.trend_scout.scan_current_hot(category, target_platforms),
                self.style_decoder.decode(koc_works, koc_context),
                return_exceptions=True,
            )

            oracle_report = phase1_results[0] if not isinstance(phase1_results[0], Exception) else None
            hot_topics = phase1_results[1] if not isinstance(phase1_results[1], Exception) else []
            style_card = phase1_results[2] if not isinstance(phase1_results[2], Exception) else None

            if oracle_report:
                output.oracle_report = self._to_dict(oracle_report)
            if hot_topics:
                output.hot_topics = [self._to_dict(h) for h in hot_topics]
            if style_card:
                output.style_card = self._to_dict(style_card)

            # ============ Phase 2 - 顺序 ============
            logger.info(f"[{request_id}] Phase 2: 决策辩论")
            top_topic = "未知"
            if oracle_report and oracle_report.trends:
                top_topic = oracle_report.trends[0].topic

            try:
                debate_result = await self.forum_debate.debate(
                    topic=f"为这个 KOC 推荐选题: {top_topic}",
                    context=output.oracle_report.get("trends", [{}])[0].get("explanation", "") if output.oracle_report else "",
                    max_rounds=2,
                )
                output.debate_result = self._to_dict(debate_result)
            except Exception as e:
                output.errors.append(f"Forum debate failed: {e}")
                debate_result = None

            try:
                style_text = self.style_decoder.to_prompt_context(style_card) if style_card else None
                topic_strategy = await self.topic_strategist.strategize(
                    oracle_report=output.oracle_report or {},
                    debate_result=output.debate_result,
                    koc_style=style_text,
                )
                output.topic_strategy = self._to_dict(topic_strategy)
            except Exception as e:
                output.errors.append(f"Topic strategist failed: {e}")
                topic_strategy = None

            # ============ Phase 3 - 并行 ============
            logger.info(f"[{request_id}] Phase 3: 内容生产 (并行)")
            if topic_strategy:
                content_task = self.script_writer.generate(
                    topic=topic_strategy.primary_topic,
                    angle=topic_strategy.angle,
                    narrative=topic_strategy.narrative,
                    target_platforms=target_platforms,
                    style_card_text=self.style_decoder.to_prompt_context(style_card) if style_card else None,
                    target_audience=topic_strategy.target_audience,
                )
                material_task = self.material_curator.search_images(
                    query=topic_strategy.primary_topic,
                    count=10,
                )

                phase3_results = await asyncio.gather(
                    content_task,
                    material_task,
                    return_exceptions=True,
                )

                content_pkg = phase3_results[0] if not isinstance(phase3_results[0], Exception) else None
                materials = phase3_results[1] if not isinstance(phase3_results[1], Exception) else []

                if content_pkg:
                    output.content_package = self._to_dict(content_pkg)
                    # 基于 content_pkg.cover_descriptions 生成封面
                    cover_descs = content_pkg.cover_descriptions[:3]  # 前 3 个
                    if cover_descs:
                        from .visual_producer_agent import CoverDescription
                        cover_descriptions = [
                            CoverDescription(
                                style=c.get("style", "高对比"),
                                main_text=c.get("main_text", ""),
                                color_palette=c.get("color_palette", "红黑"),
                                description=c.get("description", ""),
                            )
                            for c in cover_descs
                        ]
                        try:
                            covers = await self.visual_producer.generate_covers(
                                cover_descriptions, topic_strategy.primary_topic
                            )
                            output.cover_images = [self._to_dict(c) for c in covers]
                        except Exception as e:
                            output.errors.append(f"Cover generation failed: {e}")

                if materials:
                    output.materials = [self._to_dict(m) for m in materials]

            # ============ Phase 4 - 并行审查 ============
            logger.info(f"[{request_id}] Phase 4: 审查发布")
            content_text = ""
            if output.content_package:
                # 取第一个平台的 body 做审查
                platforms_data = output.content_package.get("platforms", {})
                if platforms_data:
                    first_plat = next(iter(platforms_data.values()))
                    content_text = first_plat.get("body", "")

            phase4_tasks = []
            if content_text:
                phase4_tasks.append(self.fact_checker.check(content_text, category))
                phase4_tasks.append(self.risk_reviewer.review(content_text, category, target_platforms[0]))
            if topic_strategy:
                phase4_tasks.append(self.sim_predictor.simulate(
                    content_summary=topic_strategy.primary_topic,
                    target_categories=[category],
                ))

            if phase4_tasks:
                phase4_results = await asyncio.gather(*phase4_tasks, return_exceptions=True)

                if content_text and len(phase4_results) >= 2:
                    if not isinstance(phase4_results[0], Exception):
                        output.fact_check = self._to_dict(phase4_results[0])
                    if not isinstance(phase4_results[1], Exception):
                        output.compliance = self._to_dict(phase4_results[1])
                    if topic_strategy and len(phase4_results) >= 3:
                        if not isinstance(phase4_results[2], Exception):
                            output.simulation = self._to_dict(phase4_results[2])

            # ============ 最终归因 ============
            insight = self.insight_analyst.synthesize(
                oracle_report=output.oracle_report,
                debate_result=output.debate_result,
                topic_strategy=output.topic_strategy,
                sim_result=output.simulation,
                risk_report=output.compliance,
            )
            output.insight = self._to_dict(insight)

        except Exception as e:
            logger.exception(f"[{request_id}] Pipeline failed: {e}")
            output.errors.append(str(e))

        output.completed_at = datetime.now()
        output.duration_ms = int((output.completed_at - output.started_at).total_seconds() * 1000)

        return output

    async def run_streaming(
        self,
        topic_seed: str,
        category: str = "通用",
        target_platforms: Optional[List[str]] = None,
        koc_works: Optional[List[Dict[str, Any]]] = None,
        koc_context: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """流式输出(给 WebSocket 用)
        
        Yields:
            事件 dict: {phase, agent, status, data, ...}
        """
        target_platforms = target_platforms or ["channels", "wechat_official", "xhs", "douyin"]
        koc_works = koc_works or []
        request_id = request_id or f"req-{int(time.time())}"

        yield {"event": "start", "request_id": request_id, "topic_seed": topic_seed}

        # Phase 1
        yield {"event": "phase_start", "phase": "信号感知", "agents": ["Oracle", "TrendScout", "StyleDecoder"]}

        oracle_report = None
        try:
            yield {"event": "agent_start", "agent": "OracleAgent"}
            oracle_report = await self.oracle.scan(topic_seed, category, target_platforms)
            yield {
                "event": "agent_done",
                "agent": "OracleAgent",
                "data": {
                    "trends_count": len(oracle_report.trends),
                    "top_3_topics": [t.topic for t in oracle_report.trends[:3]],
                    "scan_time_ms": oracle_report.scan_time_ms,
                },
            }
        except Exception as e:
            yield {"event": "agent_error", "agent": "OracleAgent", "error": str(e)}

        try:
            yield {"event": "agent_start", "agent": "TrendScoutAgent"}
            hot_topics = await self.trend_scout.scan_current_hot(category, target_platforms)
            yield {
                "event": "agent_done",
                "agent": "TrendScoutAgent",
                "data": {"hot_count": len(hot_topics)},
            }
        except Exception as e:
            yield {"event": "agent_error", "agent": "TrendScoutAgent", "error": str(e)}

        style_card = None
        try:
            yield {"event": "agent_start", "agent": "StyleDecoderAgent"}
            style_card = await self.style_decoder.decode(koc_works, koc_context)
            yield {
                "event": "agent_done",
                "agent": "StyleDecoderAgent",
                "data": {"persona": style_card.persona, "tone": style_card.tone},
            }
        except Exception as e:
            yield {"event": "agent_error", "agent": "StyleDecoderAgent", "error": str(e)}

        # Phase 2
        yield {"event": "phase_start", "phase": "决策辩论"}

        debate_result = None
        if oracle_report and oracle_report.trends:
            try:
                yield {"event": "agent_start", "agent": "ForumDebateAgent"}
                debate_result = await self.forum_debate.debate(
                    topic=f"为这个 KOC 推荐: {oracle_report.trends[0].topic}",
                    context=oracle_report.trends[0].explanation,
                    max_rounds=2,
                )
                yield {
                    "event": "agent_done",
                    "agent": "ForumDebateAgent",
                    "data": {"rounds": len(debate_result.rounds), "decision": debate_result.final_decision[:100]},
                }
            except Exception as e:
                yield {"event": "agent_error", "agent": "ForumDebateAgent", "error": str(e)}

        topic_strategy = None
        try:
            yield {"event": "agent_start", "agent": "TopicStrategistAgent"}
            style_text = self.style_decoder.to_prompt_context(style_card) if style_card else None
            topic_strategy = await self.topic_strategist.strategize(
                oracle_report=self._to_dict(oracle_report) if oracle_report else {},
                debate_result=self._to_dict(debate_result) if debate_result else None,
                koc_style=style_text,
            )
            yield {
                "event": "agent_done",
                "agent": "TopicStrategistAgent",
                "data": {
                    "topic": topic_strategy.primary_topic,
                    "angle": topic_strategy.angle,
                    "confidence": topic_strategy.confidence,
                },
            }
        except Exception as e:
            yield {"event": "agent_error", "agent": "TopicStrategistAgent", "error": str(e)}

        # Phase 3
        yield {"event": "phase_start", "phase": "内容生产"}

        content_pkg = None
        if topic_strategy:
            try:
                yield {"event": "agent_start", "agent": "ScriptWriterAgent"}
                content_pkg = await self.script_writer.generate(
                    topic=topic_strategy.primary_topic,
                    angle=topic_strategy.angle,
                    narrative=topic_strategy.narrative,
                    target_platforms=target_platforms,
                    style_card_text=self.style_decoder.to_prompt_context(style_card) if style_card else None,
                    target_audience=topic_strategy.target_audience,
                )
                yield {
                    "event": "agent_done",
                    "agent": "ScriptWriterAgent",
                    "data": {
                        "platforms_generated": list(content_pkg.platforms.keys()),
                        "title_count": len(content_pkg.title_candidates),
                    },
                }
            except Exception as e:
                yield {"event": "agent_error", "agent": "ScriptWriterAgent", "error": str(e)}

        # Phase 4
        yield {"event": "phase_start", "phase": "审查发布"}

        # 略简版,详细见 run() 方法
        if content_pkg:
            content_text = ""
            for p in content_pkg.platforms.values():
                content_text = p.body
                break

            if content_text:
                try:
                    yield {"event": "agent_start", "agent": "RiskReviewerAgent"}
                    compliance = await self.risk_reviewer.review(content_text, category, target_platforms[0])
                    yield {
                        "event": "agent_done",
                        "agent": "RiskReviewerAgent",
                        "data": {
                            "overall_pass": compliance.overall_pass,
                            "risk_count": len(compliance.risks),
                        },
                    }
                except Exception as e:
                    yield {"event": "agent_error", "agent": "RiskReviewerAgent", "error": str(e)}

        yield {"event": "complete", "request_id": request_id}

    @staticmethod
    def _to_dict(obj: Any) -> Any:
        """转换 dataclass / 其他对象为 dict"""
        if obj is None:
            return None
        try:
            if hasattr(obj, "__dataclass_fields__"):
                return asdict(obj)
            elif isinstance(obj, dict):
                return obj
            elif isinstance(obj, list):
                return [RippleOrchestrator._to_dict(x) for x in obj]
            elif hasattr(obj, "__dict__"):
                return {k: RippleOrchestrator._to_dict(v) for k, v in obj.__dict__.items()}
            elif isinstance(obj, datetime):
                return obj.isoformat()
            else:
                return obj
        except Exception:
            return str(obj)
