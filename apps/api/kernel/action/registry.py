"""Tool Registry - 仿 Claude Code / Hermes Engineer 的工具注册表

设计原则:
- 每个工具有 schema (Pydantic) + 权限级别 + 描述
- Tool 是一等公民,Planner 在 DAG 里组合 tools 而不是 agents
- 工具调用全程审计 (duration / inputs / outputs / errors)
- 支持 sandbox 限制 (write 操作需明确权限)
"""

from __future__ import annotations

import asyncio
import functools
import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, List, Optional, Type

from pydantic import BaseModel

from ..types import (
    Citation, PermissionLevel, ReplayNode, RunContext,
    ToolInput, ToolOutput, ToolSchema, CognitivePhase,
)
from ..event_bus import EventBus


ToolHandler = Callable[..., Awaitable[ToolOutput]]


@dataclass
class Tool:
    """已注册工具的完整描述"""
    name: str
    description: str
    permission_level: PermissionLevel
    handler: ToolHandler
    input_model: Type[BaseModel]
    output_model: Type[BaseModel]
    cost_estimate_ms: int = 1000
    cost_estimate_tokens: int = 0
    tags: List[str] = field(default_factory=list)

    def schema(self) -> ToolSchema:
        return ToolSchema(
            name=self.name,
            description=self.description,
            permission_level=self.permission_level,
            input_schema=self.input_model.model_json_schema(),
            output_schema=self.output_model.model_json_schema(),
            cost_estimate_ms=self.cost_estimate_ms,
            cost_estimate_tokens=self.cost_estimate_tokens,
        )


class ToolRegistry:
    """工具注册表 - 全局单例"""

    def __init__(self) -> None:
        self._tools: Dict[str, Tool] = {}
        self._call_history: List[Dict[str, Any]] = []

    def register(self, tool: Tool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Tool {tool.name} already registered")
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def list_tools(
        self,
        permission_max: Optional[PermissionLevel] = None,
        tag: Optional[str] = None,
    ) -> List[Tool]:
        result = list(self._tools.values())
        if tag:
            result = [t for t in result if tag in t.tags]
        if permission_max:
            order = {
                PermissionLevel.READ: 0,
                PermissionLevel.NETWORK: 1,
                PermissionLevel.GENERATE: 2,
                PermissionLevel.WRITE: 3,
                PermissionLevel.DESTRUCTIVE: 4,
            }
            result = [t for t in result if order[t.permission_level] <= order[permission_max]]
        return result

    def list_names(self) -> List[str]:
        return sorted(self._tools.keys())

    def schemas_for_llm(self) -> List[Dict[str, Any]]:
        """生成 OpenAI function calling 格式的工具描述,供 LLM 工具调用"""
        result = []
        for tool in self._tools.values():
            result.append({
                "type": "function",
                "function": {
                    "name": tool.name.replace(".", "_"),
                    "description": tool.description,
                    "parameters": tool.input_model.model_json_schema(),
                },
            })
        return result

    async def execute(
        self,
        name: str,
        input_data: Dict[str, Any],
        ctx: RunContext,
        bus: Optional[EventBus] = None,
        replay_recorder: Optional["ReplayRecorder"] = None,
    ) -> ToolOutput:
        """执行工具 - 全程审计"""
        tool = self._tools.get(name)
        if tool is None:
            raise ValueError(f"Tool {name} not found")

        validated_input = tool.input_model.model_validate(input_data)
        input_hash = hashlib.sha256(
            json.dumps(input_data, sort_keys=True, default=str).encode()
        ).hexdigest()[:16]

        if bus is not None:
            await bus.tool_call(name, input_data)

        start_time = time.time()
        node = None
        try:
            output = await tool.handler(validated_input, ctx, bus)
            duration_ms = int((time.time() - start_time) * 1000)
            output.duration_ms = duration_ms

            if bus is not None:
                summary = output.model_dump(exclude={"citations"}, mode="json")
                summary_str = json.dumps(summary, ensure_ascii=False, default=str)[:200]
                await bus.tool_result(name, summary_str, duration_ms)

            if replay_recorder is not None:
                node = replay_recorder.record_tool_call(
                    tool_name=name,
                    input_hash=input_hash,
                    input_summary=str(input_data)[:200],
                    output_summary=str(output.model_dump(mode="json"))[:300],
                    duration_ms=duration_ms,
                )
                if bus is not None:
                    await bus.replay_node(node.model_dump(mode="json"))

            self._call_history.append({
                "tool": name, "duration_ms": duration_ms, "success": output.success,
                "trace_id": ctx.trace_id,
            })

            return output

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            error_msg = str(e)
            if bus is not None:
                await bus.tool_result(name, f"ERROR: {error_msg}", duration_ms)

            self._call_history.append({
                "tool": name, "duration_ms": duration_ms, "success": False,
                "error": error_msg, "trace_id": ctx.trace_id,
            })

            return tool.output_model(success=False, error=error_msg, duration_ms=duration_ms)

    def call_history(self, trace_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if trace_id:
            return [c for c in self._call_history if c.get("trace_id") == trace_id]
        return list(self._call_history)


_global_registry: Optional[ToolRegistry] = None


def get_registry() -> ToolRegistry:
    global _global_registry
    if _global_registry is None:
        _global_registry = ToolRegistry()
    return _global_registry


def register_tool(
    name: str,
    description: str,
    input_model: Type[BaseModel],
    output_model: Type[BaseModel],
    permission_level: PermissionLevel = PermissionLevel.READ,
    cost_estimate_ms: int = 1000,
    cost_estimate_tokens: int = 0,
    tags: Optional[List[str]] = None,
) -> Callable[[ToolHandler], ToolHandler]:
    """装饰器: 把异步函数注册为 Tool

    用法:
        @register_tool(
            name="oracle.scan",
            description="扫描 7 数据源,返回早期信号",
            input_model=OracleScanInput,
            output_model=OracleScanOutput,
            permission_level=PermissionLevel.NETWORK,
        )
        async def oracle_scan(input: OracleScanInput, ctx: RunContext, bus: EventBus) -> OracleScanOutput:
            ...
    """
    def decorator(fn: ToolHandler) -> ToolHandler:
        registry = get_registry()
        registry.register(Tool(
            name=name,
            description=description,
            permission_level=permission_level,
            handler=fn,
            input_model=input_model,
            output_model=output_model,
            cost_estimate_ms=cost_estimate_ms,
            cost_estimate_tokens=cost_estimate_tokens,
            tags=tags or [],
        ))

        @functools.wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any) -> ToolOutput:
            return await fn(*args, **kwargs)
        return wrapper
    return decorator


# 防御性: ReplayRecorder 是 forward reference,实际定义在 reasoning/replay
class ReplayRecorder:
    def record_tool_call(self, **kwargs: Any) -> ReplayNode: ...
