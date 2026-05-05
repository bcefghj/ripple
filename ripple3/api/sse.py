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


def done_event(*, intent: str = "", domain: str = "", topic: str = "") -> str:
    return sse_event("done", {"intent": intent, "domain": domain, "topic": topic})


def error_event(message: str) -> str:
    return sse_event("error", {"message": message})
