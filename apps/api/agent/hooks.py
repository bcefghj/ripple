"""Hooks 系统 - 5 类钩子

借鉴 Claude Code Agent SDK Hooks:
- PreToolUse: 拦截/改输入
- PostToolUse: 审计/追加上下文
- Stop: 收尾(可阻塞继续)
- PreCompact: 压缩前归档
- PermissionRequest: 权限审批

聚合优先级: deny > ask > allow

设计原则:
- Hook 配置快照(冻结后不可改,防 TOCTOU)
- exit 2 = 阻断,1 = 警告(避免噪声)
- API 错误路径不走 Stop hook(防死循环)
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncIterator, Awaitable, Callable, Dict, List, Optional

from loguru import logger


class HookEvent(str, Enum):
    PRE_TOOL_USE = "PreToolUse"
    POST_TOOL_USE = "PostToolUse"
    STOP = "Stop"
    PRE_COMPACT = "PreCompact"
    POST_COMPACT = "PostCompact"
    PERMISSION_REQUEST = "PermissionRequest"
    SESSION_START = "SessionStart"
    USER_PROMPT_SUBMIT = "UserPromptSubmit"


class PermissionDecision(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    ASK = "ask"


@dataclass
class HookResult:
    """Hook 返回值"""
    blocking_error: Optional[str] = None  # 非 None 则阻塞
    permission_decision: Optional[PermissionDecision] = None
    updated_input: Optional[Dict[str, Any]] = None  # 修改 tool 输入
    additional_context: Optional[str] = None  # 注入额外上下文
    prevent_continuation: bool = False  # Stop hook 用


HookFn = Callable[[Dict[str, Any]], Awaitable[HookResult]]


@dataclass
class HookSnapshot:
    """Hook 配置快照(信任后冻结)"""
    handlers: Dict[HookEvent, List[HookFn]] = field(default_factory=dict)
    is_frozen: bool = False


class HookRegistry:
    """Hook 注册中心
    
    使用方式:
        registry = HookRegistry()
        
        @registry.register(HookEvent.PRE_TOOL_USE)
        async def block_dangerous(payload):
            tool_name = payload.get("tool_name")
            if tool_name == "delete_all":
                return HookResult(blocking_error="拒绝执行危险工具")
            return HookResult()
        
        # 主循环中:
        async with registry.emit(HookEvent.SESSION_START, {}) as guards:
            ...
    """

    def __init__(self):
        self._handlers: Dict[HookEvent, List[HookFn]] = {}
        self._snapshot: Optional[HookSnapshot] = None
        self._trust_check: Optional[Callable[[], bool]] = None

    def register(self, event: HookEvent):
        """装饰器:注册 hook"""
        def decorator(fn: HookFn) -> HookFn:
            self._handlers.setdefault(event, []).append(fn)
            return fn
        return decorator

    def add(self, event: HookEvent, fn: HookFn) -> None:
        """直接添加 hook"""
        self._handlers.setdefault(event, []).append(fn)

    def capture_snapshot(self) -> HookSnapshot:
        """冻结当前 hook 配置(防 TOCTOU)"""
        snapshot = HookSnapshot(
            handlers={k: list(v) for k, v in self._handlers.items()},
            is_frozen=True,
        )
        self._snapshot = snapshot
        return snapshot

    def set_trust_check(self, check: Callable[[], bool]) -> None:
        """设置信任检查(返回 False 时所有 hook 跳过)"""
        self._trust_check = check

    def _should_skip(self) -> bool:
        if self._trust_check is None:
            return False
        try:
            return not self._trust_check()
        except Exception:
            return True

    @asynccontextmanager
    async def emit(self, event: HookEvent, payload: Dict[str, Any]) -> AsyncIterator[List[HookResult]]:
        """触发 hook 事件,yield 所有 hook 的结果"""
        if self._should_skip():
            yield []
            return

        snapshot = self._snapshot
        handlers = (snapshot.handlers if snapshot else self._handlers).get(event, [])

        if not handlers:
            yield []
            return

        results = await asyncio.gather(
            *[self._safe_run(h, payload) for h in handlers],
            return_exceptions=False,
        )
        yield list(results)

    async def _safe_run(self, fn: HookFn, payload: Dict[str, Any]) -> HookResult:
        """安全运行 hook,捕获异常"""
        try:
            result = await fn(payload)
            if not isinstance(result, HookResult):
                return HookResult()
            return result
        except Exception as e:
            logger.error(f"Hook 执行失败: {e}")
            return HookResult()  # 失败时不阻塞主流程

    async def execute_pre_tool(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> HookResult:
        """执行 PreToolUse hooks,聚合结果(deny > ask > allow)"""
        payload = {
            "tool_name": tool_name,
            "tool_input": tool_input,
            "context": context or {},
        }

        async with self.emit(HookEvent.PRE_TOOL_USE, payload) as results:
            # 聚合 blocking_error
            for r in results:
                if r.blocking_error:
                    return HookResult(blocking_error=r.blocking_error)

            # 聚合 permission_decision: deny > ask > allow
            decisions = [r.permission_decision for r in results if r.permission_decision]
            if PermissionDecision.DENY in decisions:
                return HookResult(permission_decision=PermissionDecision.DENY)
            if PermissionDecision.ASK in decisions:
                return HookResult(permission_decision=PermissionDecision.ASK)

            # 聚合 updated_input (last-wins)
            updated_input = None
            for r in results:
                if r.updated_input:
                    updated_input = r.updated_input

            # 聚合 additional_context
            contexts = [r.additional_context for r in results if r.additional_context]
            return HookResult(
                updated_input=updated_input,
                additional_context="\n".join(contexts) if contexts else None,
            )

    async def execute_stop(self, payload: Dict[str, Any]) -> HookResult:
        """执行 Stop hooks"""
        async with self.emit(HookEvent.STOP, payload) as results:
            for r in results:
                if r.prevent_continuation:
                    return HookResult(prevent_continuation=True)
                if r.blocking_error:
                    return HookResult(blocking_error=r.blocking_error)
            return HookResult()


# ============================================================
# 默认安全 Hooks(开箱即用)
# ============================================================


async def default_dangerous_tool_blocker(payload: Dict[str, Any]) -> HookResult:
    """阻止危险工具"""
    DANGEROUS = {"system_shell_unrestricted", "rm_rf", "drop_database", "exec_arbitrary"}
    tool_name = payload.get("tool_name", "")
    if tool_name in DANGEROUS:
        return HookResult(
            blocking_error=f"拒绝执行危险工具: {tool_name}",
            permission_decision=PermissionDecision.DENY,
        )
    return HookResult()


async def default_audit_logger(payload: Dict[str, Any]) -> HookResult:
    """审计日志"""
    logger.info(f"[Audit] tool={payload.get('tool_name')} ctx={payload.get('context', {}).get('agent_id')}")
    return HookResult()


def install_default_hooks(registry: HookRegistry) -> None:
    """安装默认安全 hooks"""
    registry.add(HookEvent.PRE_TOOL_USE, default_dangerous_tool_blocker)
    registry.add(HookEvent.POST_TOOL_USE, default_audit_logger)
