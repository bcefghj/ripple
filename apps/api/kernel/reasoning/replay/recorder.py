"""ReplayRecorder - 在每次 run 中记录决策节点"""

from __future__ import annotations

from typing import Dict, List, Optional

from ...types import CognitivePhase, ReplayNode, RunContext
from .store import ReplayStore, _get_store


def get_replay_store() -> ReplayStore:
    return _get_store()


class ReplayRecorder:
    """单次 run 的 Replay 记录器"""

    def __init__(self, ctx: RunContext, store: Optional[ReplayStore] = None) -> None:
        self.ctx = ctx
        self.store = store or get_replay_store()
        self._last_node_id: Optional[str] = None
        self._nodes: List[ReplayNode] = []
        self.store.start_run(
            run_id=ctx.run_id,
            trace_id=ctx.trace_id,
            user_id=ctx.user_id,
            query=ctx.query,
            project_id=ctx.project_id,
            metadata=ctx.metadata,
        )

    def record(
        self,
        phase: CognitivePhase,
        actor: str,
        input_summary: str = "",
        output_summary: str = "",
        input_hash: str = "",
        rejected_alternatives: Optional[List[str]] = None,
        duration_ms: int = 0,
        parent_ids: Optional[List[str]] = None,
        metadata: Optional[Dict] = None,
    ) -> ReplayNode:
        if parent_ids is None and self._last_node_id is not None:
            parent_ids = [self._last_node_id]

        node = ReplayNode(
            phase=phase,
            actor=actor,
            input_hash=input_hash,
            input_summary=input_summary,
            output_summary=output_summary,
            rejected_alternatives=rejected_alternatives or [],
            duration_ms=duration_ms,
            parent_ids=parent_ids or [],
            metadata=metadata or {},
        )
        self.store.write_node(self.ctx.run_id, node)
        self._nodes.append(node)
        self._last_node_id = node.node_id
        return node

    def record_tool_call(
        self,
        tool_name: str,
        input_hash: str,
        input_summary: str,
        output_summary: str,
        duration_ms: int,
    ) -> ReplayNode:
        return self.record(
            phase=CognitivePhase.ACT,
            actor=tool_name,
            input_hash=input_hash,
            input_summary=input_summary,
            output_summary=output_summary,
            duration_ms=duration_ms,
        )

    def record_thinking(self, actor: str, thought: str) -> ReplayNode:
        return self.record(
            phase=CognitivePhase.THINK,
            actor=actor,
            output_summary=thought[:500],
        )

    def record_plan(self, actor: str, plan: str, alternatives: Optional[List[str]] = None) -> ReplayNode:
        return self.record(
            phase=CognitivePhase.PLAN,
            actor=actor,
            output_summary=plan[:500],
            rejected_alternatives=alternatives or [],
        )

    def record_observation(self, actor: str, observation: str) -> ReplayNode:
        return self.record(
            phase=CognitivePhase.OBSERVE,
            actor=actor,
            output_summary=observation[:500],
        )

    def record_reflection(self, actor: str, reflection: str) -> ReplayNode:
        return self.record(
            phase=CognitivePhase.REFLECT,
            actor=actor,
            output_summary=reflection[:500],
        )

    def finish(self, status: str = "ok") -> None:
        self.store.finish_run(self.ctx.run_id, status)

    def to_dag(self) -> Dict:
        """导出为前端可视化的 DAG 结构"""
        nodes = [
            {
                "id": n.node_id,
                "phase": n.phase.value,
                "actor": n.actor,
                "summary": n.output_summary[:120],
                "duration_ms": n.duration_ms,
                "rejected": n.rejected_alternatives,
                "merkle": n.merkle_hash()[:8],
            }
            for n in self._nodes
        ]
        edges = []
        for n in self._nodes:
            for parent_id in n.parent_ids:
                edges.append({"from": parent_id, "to": n.node_id})
        return {"nodes": nodes, "edges": edges, "run_id": self.ctx.run_id}
