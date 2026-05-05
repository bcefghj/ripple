"""SSE event helpers for structured streaming responses."""

from __future__ import annotations

import json
from typing import Any


def sse_event(event: str, data: Any) -> str:
    """Format a single SSE event string."""
    payload = json.dumps(data, ensure_ascii=False) if not isinstance(data, str) else data
    return f"event: {event}\ndata: {payload}\n\n"


def thinking_event(step: str, detail: str, *, progress: int = 0, agents: list[dict] | None = None) -> str:
    d: dict[str, Any] = {"step": step, "detail": detail, "progress": progress}
    if agents:
        d["agents"] = agents
    return sse_event("thinking", d)


def content_event(delta: str) -> str:
    return sse_event("content", {"delta": delta})


def sources_event(citations: list[dict]) -> str:
    return sse_event("sources", {"citations": citations})


def graph_event(nodes: list[dict], links: list[dict]) -> str:
    return sse_event("graph", {"nodes": nodes, "links": links})


def score_event(data: dict) -> str:
    return sse_event("score", data)


def agent_speak_event(agent: dict, content: str, *, round_num: int = 1) -> str:
    return sse_event("agent_speak", {"agent": agent, "content": content, "round": round_num})


def agent_start_event(agent: dict) -> str:
    return sse_event("agent_start", {"agent": agent})


def arbiter_thinking_event(content: str) -> str:
    return sse_event("arbiter_thinking", {"content": content})


def done_event(*, intent: str = "", domain: str = "", topic: str = "", conversation_id: str = "", next_steps: list[dict] | None = None) -> str:
    d: dict[str, Any] = {"intent": intent, "domain": domain, "topic": topic}
    if conversation_id:
        d["conversation_id"] = conversation_id
    if next_steps:
        d["next_steps"] = next_steps
    return sse_event("done", d)


def search_stats_event(total: int, deduped: int, engines: dict[str, int]) -> str:
    return sse_event("search_stats", {
        "total_raw": total,
        "total_deduped": deduped,
        "engines": engines,
    })


def data_warning_event(message: str) -> str:
    return sse_event("data_warning", {"message": message})


def error_event(message: str) -> str:
    return sse_event("error", {"message": message})


def token_usage_event(
    search_tokens: int = 0,
    llm_tokens: int = 0,
    total_tokens: int = 0,
    search_calls: int = 0,
    agent_rounds: int = 0,
    elapsed_ms: int = 0,
) -> str:
    return sse_event("token_usage", {
        "search_tokens": search_tokens,
        "llm_tokens": llm_tokens,
        "total_tokens": total_tokens,
        "search_calls": search_calls,
        "agent_rounds": agent_rounds,
        "elapsed_ms": elapsed_ms,
    })


def viral_score_event(score_data: dict) -> str:
    return sse_event("viral_score", score_data)


def reflection_event(iteration: int, score: float, action: str) -> str:
    return sse_event("reflection", {
        "iteration": iteration,
        "score": score,
        "action": action,
    })


def deep_research_event(phase: int, total_phases: int, description: str, results_so_far: int = 0) -> str:
    return sse_event("deep_research", {
        "phase": phase,
        "total_phases": total_phases,
        "description": description,
        "results_so_far": results_so_far,
    })


def wechat_strategy_event(strategy: dict) -> str:
    return sse_event("wechat_strategy", strategy)


def koc_growth_event(growth_data: dict) -> str:
    return sse_event("koc_growth", growth_data)
