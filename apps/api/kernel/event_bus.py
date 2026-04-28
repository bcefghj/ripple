"""统一事件总线 - 前后端通过 SSE 传输

用法:
    bus = EventBus(trace_id="trace_abc")
    await bus.thinking("正在分析意图...")
    await bus.tool_call("oracle.scan", {...})
    async for event in bus.stream():
        yield event.to_sse()
"""

from __future__ import annotations

import asyncio
from typing import Any, AsyncIterator, Callable, Dict, List, Optional

from .types import EventType, StreamEvent


class EventBus:
    """单次运行的事件总线 - 异步队列 + 多消费者支持"""

    def __init__(self, trace_id: str = "", buffer_size: int = 1000) -> None:
        self.trace_id = trace_id
        self._queue: asyncio.Queue[Optional[StreamEvent]] = asyncio.Queue(buffer_size)
        self._closed = False
        self._listeners: List[Callable[[StreamEvent], None]] = []

    async def emit(
        self,
        event_type: EventType,
        payload: Optional[Dict[str, Any]] = None,
    ) -> None:
        if self._closed:
            return
        event = StreamEvent(
            event_type=event_type,
            trace_id=self.trace_id,
            payload=payload or {},
        )
        for listener in self._listeners:
            try:
                listener(event)
            except Exception:
                pass
        await self._queue.put(event)

    def add_listener(self, fn: Callable[[StreamEvent], None]) -> None:
        self._listeners.append(fn)

    async def thinking(self, text: str, **extra: Any) -> None:
        await self.emit(EventType.THINKING, {"text": text, **extra})

    async def agent_start(self, agent: str, **extra: Any) -> None:
        await self.emit(EventType.AGENT_START, {"agent": agent, **extra})

    async def agent_progress(self, agent: str, step: str, **extra: Any) -> None:
        await self.emit(EventType.AGENT_PROGRESS, {"agent": agent, "step": step, **extra})

    async def agent_end(self, agent: str, success: bool = True, **extra: Any) -> None:
        await self.emit(EventType.AGENT_END, {"agent": agent, "success": success, **extra})

    async def tool_call(self, tool: str, inputs: Dict[str, Any]) -> None:
        await self.emit(EventType.TOOL_CALL, {"tool": tool, "inputs": inputs})

    async def tool_result(self, tool: str, summary: str, duration_ms: int = 0) -> None:
        await self.emit(EventType.TOOL_RESULT, {
            "tool": tool, "summary": summary, "duration_ms": duration_ms,
        })

    async def token(self, text: str) -> None:
        await self.emit(EventType.TOKEN, {"text": text})

    async def citation(self, citation: Dict[str, Any]) -> None:
        await self.emit(EventType.CITATION, {"citation": citation})

    async def card(self, card_type: str, data: Dict[str, Any]) -> None:
        await self.emit(EventType.REPORT_CARD, {"card_type": card_type, "data": data})

    async def replay_node(self, node: Dict[str, Any]) -> None:
        await self.emit(EventType.REPLAY_NODE, {"node": node})

    async def error(self, message: str, **extra: Any) -> None:
        await self.emit(EventType.ERROR, {"message": message, **extra})

    async def heartbeat(self) -> None:
        await self.emit(EventType.HEARTBEAT, {})

    async def done(self, **extra: Any) -> None:
        await self.emit(EventType.DONE, extra)
        await self.close()

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        await self._queue.put(None)

    async def stream(self) -> AsyncIterator[StreamEvent]:
        while True:
            event = await self._queue.get()
            if event is None:
                break
            yield event
