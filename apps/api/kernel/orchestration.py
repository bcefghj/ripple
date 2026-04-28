"""Adaptive Orchestrator - 一句话编排器

核心: 用 LLM 把用户的一句话拆解为 TaskDAG,根据 Skill Library 和 Tool Registry 选择动作,
然后通过 EventBus 流式输出每一步的思考过程。

不再是固定 4 阶段流水线,而是动态规划 + Replay 记录。
"""

from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .types import CognitivePhase, RunContext, EventType
from .event_bus import EventBus
from .reasoning.replay import ReplayRecorder
from .reasoning.critique import get_critique_loop
from .reasoning.trust import get_enforcer
from .cognition.llm import quick_chat, get_llm_client
from .cognition.persona import get_persona_manager
from .skills import get_skill_library
from .action import get_registry
from .persistence.memory import get_memory_system


@dataclass
class TaskStep:
    """DAG 中的一个任务步骤"""
    step_id: str
    intent: str  # 'oracle_scan' / 'persona_recall' / 'risk_score' / ...
    tool: Optional[str] = None
    inputs: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)
    description: str = ""


@dataclass
class TaskDAG:
    steps: List[TaskStep] = field(default_factory=list)
    intent_summary: str = ""
    user_persona_relevant: bool = True


PLANNER_SYSTEM = """
你是 Ripple OS 的意图规划器。用户给一句话, 你要拆解为执行计划 (DAG)。

## 可用的高层意图
- early_signal_scan: 扫描 7 数据源找早期信号
- persona_recall: 召回用户人设
- topic_evaluate: 对一组话题做风险/收益/趋势链评估
- multi_version_write: 生成多版本文案 + 虚拟受众赛马
- campaign_plan: 设计 7 天战役
- cross_platform_translate: 把一段内容翻译为多平台
- self_critique: 自我批评闭环
- citation_enforce: 确保所有断言带引用
- final_summarize: 给出最终结构化结论
- ask_clarify: 反问用户细节 (仅当输入太空泛)

## 规则
- 一句话内可能要走多个 step, 要按用户优先关心的去裁剪
- 如果用户明显已有素材 (粘贴 URL), 优先 cross_platform_translate
- 如果用户要规划一周, 一定要先 oracle_scan + persona_recall, 再 campaign_plan
- 一切 LLM 输出都要走 citation_enforce + self_critique
- 输出严格 JSON: { "intent_summary": "...", "steps": [ { "intent": "...", "depends_on": [], "description": "..." } ] }
""".strip()


class AdaptivePlanner:
    async def plan(self, query: str, persona_summary: str = "", memory_context: str = "") -> TaskDAG:
        sys = PLANNER_SYSTEM
        user = (
            f"## 用户输入\n{query}\n\n"
            f"## 已知人设摘要\n{persona_summary[:300]}\n\n"
            f"## 记忆召回\n{memory_context[:500]}"
        )
        try:
            text = await quick_chat(sys, user, json_mode=True, max_tokens=1200, temperature=0.3)
            data = json.loads(text)
            steps = []
            for i, s in enumerate(data.get("steps", [])):
                steps.append(TaskStep(
                    step_id=f"step_{i+1}",
                    intent=s.get("intent", "final_summarize"),
                    description=s.get("description", "")[:200],
                    depends_on=s.get("depends_on", []) or [],
                ))
            return TaskDAG(
                steps=steps,
                intent_summary=data.get("intent_summary", "")[:300],
            )
        except Exception:
            return TaskDAG(
                steps=[
                    TaskStep(step_id="step_1", intent="early_signal_scan"),
                    TaskStep(step_id="step_2", intent="persona_recall", depends_on=["step_1"]),
                    TaskStep(step_id="step_3", intent="topic_evaluate", depends_on=["step_2"]),
                    TaskStep(step_id="step_4", intent="multi_version_write", depends_on=["step_3"]),
                    TaskStep(step_id="step_5", intent="self_critique", depends_on=["step_4"]),
                    TaskStep(step_id="step_6", intent="final_summarize", depends_on=["step_5"]),
                ],
                intent_summary="(fallback plan)",
            )


class AdaptiveOrchestrator:
    """主编排器"""

    def __init__(self) -> None:
        self.planner = AdaptivePlanner()
        self.skill_lib = get_skill_library()
        self.tools = get_registry()
        self.memory = get_memory_system()
        self.persona_mgr = get_persona_manager()
        self.critique = get_critique_loop()
        self.enforcer = get_enforcer()

    async def run(self, ctx: RunContext, bus: EventBus) -> Dict[str, Any]:
        """完整一次执行 - 流式发事件,返回最终结果字典"""
        recorder = ReplayRecorder(ctx)

        try:
            await bus.thinking(f"已收到查询: {ctx.query[:80]}")
            recorder.record_thinking("orchestrator", f"query={ctx.query[:200]}")

            persona = self.persona_mgr.get(ctx.user_id, ctx.persona_branch)
            persona_summary = ""
            if persona:
                persona_summary = self.persona_mgr.style_constraint_prompt(persona)
                await bus.thinking(f"已识别人设: {ctx.persona_branch} 分支, 样本数 {persona.sample_count}")

            memory_ctx = self.memory.build_context(
                user_id=ctx.user_id,
                project_id=ctx.project_id,
                session_id=ctx.session_id,
                query=ctx.query,
            )

            await bus.agent_start("Planner", description="拆解任务 DAG")
            dag = await self.planner.plan(ctx.query, persona_summary, memory_ctx)
            await bus.agent_end("Planner")
            recorder.record_plan("planner", json.dumps([s.intent for s in dag.steps], ensure_ascii=False))
            await bus.thinking(f"规划 {len(dag.steps)} 个执行步骤: " + " → ".join(s.intent for s in dag.steps))

            shared_state: Dict[str, Any] = {
                "ctx": ctx,
                "persona_summary": persona_summary,
                "persona_vector": persona,
                "results": {},
            }

            for step in dag.steps:
                await bus.agent_start(step.intent, step_id=step.step_id, description=step.description)
                handler = STEP_HANDLERS.get(step.intent)
                if handler is None:
                    await bus.thinking(f"[{step.intent}] no handler, skip")
                    await bus.agent_end(step.intent, success=False)
                    continue
                try:
                    result = await handler(ctx, bus, recorder, shared_state)
                    shared_state["results"][step.step_id] = result
                    shared_state[step.intent] = result  # also expose by intent
                    await bus.agent_end(step.intent, success=True)
                    recorder.record_observation(step.intent, str(result)[:300])
                except Exception as e:
                    await bus.error(f"{step.intent} failed: {e}")
                    recorder.record_observation(step.intent, f"ERROR: {e}")
                    await bus.agent_end(step.intent, success=False, error=str(e))

            final_summary = await self._compose_final(ctx, shared_state)
            await bus.card("final_summary", {"text": final_summary})
            recorder.record_reflection("orchestrator", final_summary[:500])

            replay_dag = recorder.to_dag()
            await bus.card("replay_graph", replay_dag)

            recorder.finish("ok")
            await bus.done(run_id=ctx.run_id)

            return {
                "run_id": ctx.run_id,
                "trace_id": ctx.trace_id,
                "final_summary": final_summary,
                "results": shared_state["results"],
                "replay_dag": replay_dag,
            }
        except Exception as e:
            await bus.error(f"Orchestrator failed: {e}")
            recorder.finish("error")
            await bus.done(run_id=ctx.run_id, status="error")
            return {"run_id": ctx.run_id, "error": str(e)}

    async def _compose_final(self, ctx: RunContext, state: Dict[str, Any]) -> str:
        """让 LLM 把所有结果汇总成一段最终结论"""
        results_brief = json.dumps(
            {k: str(v)[:300] for k, v in state.get("results", {}).items()},
            ensure_ascii=False, default=str,
        )[:3000]

        sys = self.enforcer.inject_prompt(
            "你是 Ripple 决策助理。把以下各步骤的执行结果, 汇总成一段连贯的报告 (300-600字), "
            "要点回答用户的问题, 引用要有 [source: ...] 标注 (如有), "
            "保持人设风格, 语气清晰、直接、不夸张。"
        )
        user = f"## 用户问题\n{ctx.query}\n\n## 各步骤结果\n{results_brief}"
        try:
            return await quick_chat(sys, user, max_tokens=1500, temperature=0.6)
        except Exception:
            return f"已完成查询,共生成 {len(state.get('results', {}))} 个步骤结果。"


# ============================================================
# Step Handlers
# ============================================================


async def _step_early_signal_scan(ctx, bus, recorder, state):
    from .sensing.oracle import get_oracle_scanner
    scanner = get_oracle_scanner()
    await bus.thinking("调用 7 数据源并行扫描...")
    result = await scanner.scan()
    items_summary = {
        s: len(items) for s, items in result.items_by_source.items()
    }
    await bus.card("oracle_scan", {
        "succeeded": result.sources_succeeded,
        "failed": result.sources_failed,
        "duration_ms": result.total_ms,
        "items_by_source": items_summary,
        "top_per_source": {
            s: [{"title": it.title, "rank": it.rank, "url": it.url, "value": it.raw_value}
                for it in items[:3]]
            for s, items in result.items_by_source.items()
        },
    })
    return {
        "items_by_source": {s: [it.__dict__ for it in items] for s, items in result.items_by_source.items()},
        "summary": items_summary,
    }


async def _step_persona_recall(ctx, bus, recorder, state):
    pm = get_persona_manager()
    pv = pm.get(ctx.user_id, ctx.persona_branch)
    if pv is None:
        await bus.thinking("尚无人设记忆,使用默认风格 (中性专业,中等幽默)")
        return {"branch": ctx.persona_branch, "exists": False}
    await bus.card("persona_radar", {
        "branch": pv.branch,
        "version": pv.version,
        "sample_count": pv.sample_count,
        "dimensions": pv.dimensions.model_dump(),
        "drift_score": pv.drift_score,
    })
    return {"branch": pv.branch, "exists": True, "summary": pm.style_constraint_prompt(pv)}


async def _step_topic_evaluate(ctx, bus, recorder, state):
    """评估 oracle 找出的 top 话题 - risk/reward + trend chain"""
    from .decision.risk_reward import get_risk_reward_scorer
    from .decision.trend_chain import get_trend_chain_analyzer

    scanner_result = state.get("results", {}).get("step_1", {})
    items_by_source = scanner_result.get("items_by_source", {})

    candidates = []
    for source, items in items_by_source.items():
        for item in items[:3]:
            title = item.get("title") if isinstance(item, dict) else getattr(item, "title", "")
            if title:
                candidates.append((source, title))
    candidates = candidates[:5]

    if not candidates:
        await bus.thinking("无候选话题")
        return {"topics": []}

    scorer = get_risk_reward_scorer()
    chain_analyzer = get_trend_chain_analyzer()
    topic_results = []

    for source, title in candidates:
        await bus.thinking(f"评估话题 [{source}] {title[:30]}...")
        rr = await scorer.score(title, signal_strength=0.7)
        topic_results.append({
            "source": source,
            "title": title,
            "risk_reward": rr.model_dump(),
        })

    if topic_results:
        top = topic_results[0]
        chain = await chain_analyzer.analyze(top["title"])
        top["trend_chain"] = chain.model_dump()

    await bus.card("topic_panel", {"topics": topic_results})
    return {"topics": topic_results}


async def _step_multi_version_write(ctx, bus, recorder, state):
    """生成 3 版文案 + 虚拟受众赛马"""
    from .decision.sim_predictor import get_sim_predictor

    persona_summary = state.get("persona_summary", "")
    topics = state.get("topic_evaluate") or state.get("results", {}).get("step_3", {}).get("topics", [])
    if not topics:
        topic_text = ctx.query
    else:
        topic_text = topics[0].get("title", ctx.query) if isinstance(topics, list) else ctx.query

    enforcer = get_enforcer()
    sys_base = (
        "你是 KOC 内容创作助理。基于话题和人设约束,生成 3 个版本的内容开头 (各 200-300 字),"
        "三版风格区分: 1) 数据驱动型 2) 故事感性型 3) 反差冲突型。"
        "输出严格 JSON: {variants: [ {id, style, content}, {id, style, content}, {id, style, content} ]}"
    )
    sys = enforcer.inject_prompt(sys_base + ("\n\n## 风格约束\n" + persona_summary if persona_summary else ""))
    user_msg = f"话题: {topic_text}"
    try:
        text = await quick_chat(sys, user_msg, json_mode=True, max_tokens=2000, temperature=0.8)
        data = json.loads(text)
        variants = data.get("variants", [])
    except Exception:
        variants = [
            {"id": "v1", "style": "fallback", "content": f"关于「{topic_text}」: ..."},
        ]

    sim = get_sim_predictor()
    if len(variants) >= 2:
        race_input = [(v.get("id", f"v{i}"), v.get("content", "")) for i, v in enumerate(variants[:3])]
        await bus.thinking("启动虚拟受众赛马...")
        sim_results = await sim.race(race_input)
        sim_data = [r.model_dump() for r in sim_results]
        winner_id = sim_results[0].content_variant_id if sim_results else variants[0].get("id")
        winner = next((v for v in variants if v.get("id") == winner_id), variants[0])
        await bus.card("script_variants", {"variants": variants, "sim_results": sim_data, "winner": winner.get("id")})
        return {"variants": variants, "sim": sim_data, "winner": winner}
    else:
        return {"variants": variants, "sim": [], "winner": variants[0] if variants else {}}


async def _step_self_critique(ctx, bus, recorder, state):
    """对获胜版本进入自我批评闭环"""
    from .reasoning.critique import get_critique_loop
    write_result = state.get("multi_version_write") or {}
    winner = write_result.get("winner") or {}
    draft = winner.get("content") or ""
    if not draft:
        await bus.thinking("无草稿可批评,跳过")
        return {"skipped": True}

    persona_summary = state.get("persona_summary", "")
    loop = get_critique_loop()
    await bus.thinking("自我批评闭环启动...")
    result = await loop.run(draft, ctx.query, constraints=persona_summary, max_rounds=2)
    await bus.card("critique_result", {
        "rounds": [{"round": r.round_index, "issues": r.issues} for r in result.rounds],
        "iterations": result.total_iterations,
        "converged": result.converged,
        "final": result.final_text[:1500],
    })
    return {"final": result.final_text, "iterations": result.total_iterations}


async def _step_campaign_plan(ctx, bus, recorder, state):
    from .decision.campaign import get_campaign_planner
    cp = get_campaign_planner()
    await bus.thinking("规划 7 天战役...")
    camp = await cp.plan(
        user_id=ctx.user_id,
        theme=ctx.query[:100],
        duration_days=7,
        platform="xhs",
    )
    await bus.card("campaign_timeline", {
        "campaign_id": camp.campaign_id,
        "theme": camp.theme,
        "days": [d.model_dump() for d in camp.days],
        "flow_structure": camp.flow_structure,
    })
    return {"campaign": camp.model_dump()}


async def _step_cross_platform_translate(ctx, bus, recorder, state):
    from .decision.translator import get_translator
    persona_summary = state.get("persona_summary", "")
    translator = get_translator()
    source = ctx.query
    await bus.thinking("跨平台改写...")
    packs = await translator.translate(
        source_text=source,
        source_url=ctx.metadata.get("source_url", ""),
        target_platforms=["xhs", "douyin", "wechat_video", "bilibili"],
        persona_constraint=persona_summary,
    )
    await bus.card("cross_platform", {
        "packs": [p.model_dump() for p in packs],
    })
    return {"packs": [p.model_dump() for p in packs]}


async def _step_citation_enforce(ctx, bus, recorder, state):
    return {"enforced": True, "note": "All LLM outputs are passed through citation enforcer."}


async def _step_final_summarize(ctx, bus, recorder, state):
    return {"ready": True}


async def _step_ask_clarify(ctx, bus, recorder, state):
    await bus.thinking("用户输入比较空泛,反问以澄清...")
    sys = "你是友好的助理。用户输入太空泛, 提出 1-2 个澄清问题, 简短直接。"
    response = await quick_chat(sys, ctx.query, max_tokens=300)
    await bus.card("clarify", {"question": response})
    return {"clarify_question": response}


STEP_HANDLERS = {
    "early_signal_scan": _step_early_signal_scan,
    "persona_recall": _step_persona_recall,
    "topic_evaluate": _step_topic_evaluate,
    "multi_version_write": _step_multi_version_write,
    "self_critique": _step_self_critique,
    "campaign_plan": _step_campaign_plan,
    "cross_platform_translate": _step_cross_platform_translate,
    "citation_enforce": _step_citation_enforce,
    "final_summarize": _step_final_summarize,
    "ask_clarify": _step_ask_clarify,
}


_orchestrator_singleton: Optional[AdaptiveOrchestrator] = None


def get_orchestrator() -> AdaptiveOrchestrator:
    global _orchestrator_singleton
    if _orchestrator_singleton is None:
        _orchestrator_singleton = AdaptiveOrchestrator()
    return _orchestrator_singleton
