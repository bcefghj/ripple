"""TAOR 主循环 - Async Generator + while True + Terminal 枚举

借鉴 Claude Code query.ts 的设计:
- 单一权威状态机(SDK/REPL/子代理全复用)
- async generator 提供背压
- 整对象 State 替换
- 多类熔断防"一晚 25 万次 API"环路
- Withhold 机制:可恢复错误先不 yield 给消费方

参考:
- claude-code-from-source/book/ch05-agent-loop.md
- HarrisonSec deep-dive
"""

from __future__ import annotations

import asyncio
from dataclasses import replace
from typing import Any, AsyncIterator, Awaitable, Callable, Dict, List, Optional, Union

from loguru import logger

from .compression import CompressionPipeline, estimate_tokens
from .hooks import HookEvent, HookRegistry, PermissionDecision
from .state import (
    AutoCompactTracking,
    ContinueReason,
    LoopState,
    Terminal,
    TerminalReason,
    ToolUseContext,
    Transition,
)


# Stream event 类型(yield 给消费者)
StreamEvent = Dict[str, Any]


class AgentLoop:
    """
    TAOR 主循环 - 所有 Agent 共用此循环
    
    使用方式:
        loop = AgentLoop(
            llm_call=my_llm_call_fn,
            tools_registry=my_tools,
            hooks=my_hooks,
            compression=my_compression,
            max_turns=20,
        )
        
        async for event in loop.run(initial_state, system_prompt):
            if isinstance(event, Terminal):
                print(f"结束原因: {event.reason}")
                break
            else:
                print(f"事件: {event}")
    """

    def __init__(
        self,
        llm_call: Callable[..., Awaitable[Dict[str, Any]]],
        tools_registry: Optional[Any] = None,
        hooks: Optional[HookRegistry] = None,
        compression: Optional[CompressionPipeline] = None,
        max_turns: Optional[int] = 30,
        budget_tokens: Optional[int] = None,
        budget_cost_usd: Optional[float] = None,
    ):
        self.llm_call = llm_call
        self.tools_registry = tools_registry
        self.hooks = hooks or HookRegistry()
        self.compression = compression
        self.max_turns = max_turns
        self.budget_tokens = budget_tokens
        self.budget_cost_usd = budget_cost_usd

    async def run(
        self,
        initial_state: LoopState,
        system_prompt: str,
        can_use_tool: Optional[Callable[[str, Dict[str, Any]], Awaitable[bool]]] = None,
    ) -> AsyncIterator[Union[StreamEvent, Terminal]]:
        """主循环 - async generator
        
        Yields:
            StreamEvent: 中间事件(供 UI 显示)
            Terminal: 最终结束(必须为 generator 的最后一个 yield)
        """
        state = initial_state
        can_use_tool = can_use_tool or (lambda name, inp: asyncio.coroutine(lambda: True)())

        # Session start hook
        async with self.hooks.emit(HookEvent.SESSION_START, {"state": state}) as _:
            pass

        try:
            while True:
                # 1) 预算与轮数检查
                if self.max_turns is not None and state.turn_count > self.max_turns:
                    yield Terminal(
                        reason=TerminalReason.MAX_TURNS,
                        detail={"turn_count": state.turn_count},
                        final_messages=state.messages,
                    )
                    return

                if self.budget_tokens and state.tokens_used_total > self.budget_tokens:
                    yield Terminal(
                        reason=TerminalReason.BUDGET_EXCEEDED,
                        detail={"tokens": state.tokens_used_total, "limit": self.budget_tokens},
                        final_messages=state.messages,
                    )
                    return

                # 2) 上下文压缩
                if self.compression:
                    messages_for_api = await self.compression.run_full_pipeline(
                        state.messages, state.auto_compact_tracking
                    )
                else:
                    messages_for_api = list(state.messages)

                yield {
                    "type": "turn_start",
                    "turn": state.turn_count,
                    "fingerprint": state.fingerprint(),
                }

                # 3) 调用 LLM
                try:
                    response = await self.llm_call(
                        messages=[{"role": "system", "content": system_prompt}] + messages_for_api,
                        tools=self.tools_registry.tools_schema() if self.tools_registry else None,
                    )
                except Exception as e:
                    logger.error(f"LLM 调用失败: {e}")
                    yield Terminal(
                        reason=TerminalReason.MODEL_ERROR,
                        detail={"error": str(e)},
                        final_messages=state.messages,
                    )
                    return

                # 4) 解析响应
                assistant_message = response.get("message", {})
                tool_calls = response.get("tool_calls", [])
                stop_reason = response.get("stop_reason", "completed")
                usage = response.get("usage", {})

                # 更新预算
                tokens_used = usage.get("total_tokens", 0)
                cost_usd = usage.get("cost_usd", 0)
                state = replace(
                    state,
                    tokens_used_total=state.tokens_used_total + tokens_used,
                    cost_usd_total=state.cost_usd_total + cost_usd,
                )

                yield {
                    "type": "assistant_message",
                    "content": assistant_message.get("content", ""),
                    "tool_calls": tool_calls,
                    "tokens": tokens_used,
                }

                # 5) 没有 tool calls,执行 stop hook
                if not tool_calls:
                    stop_result = await self.hooks.execute_stop({
                        "state": state,
                        "assistant_message": assistant_message,
                    })

                    if stop_result.prevent_continuation:
                        yield Terminal(
                            reason=TerminalReason.STOP_HOOK_PREVENTED,
                            detail={"reason": "Stop hook prevented continuation"},
                            final_messages=state.messages + [assistant_message],
                        )
                        return

                    if stop_result.blocking_error:
                        # Stop hook 注入错误后,继续主循环
                        error_msg = {
                            "role": "user",
                            "content": f"[Stop hook 注入]: {stop_result.blocking_error}",
                        }
                        state = replace(
                            state,
                            messages=state.messages + [assistant_message, error_msg],
                            stop_hook_active=True,
                            transition=Transition(reason=ContinueReason.STOP_HOOK_BLOCKING),
                        )
                        continue

                    # 正常结束
                    yield Terminal(
                        reason=TerminalReason.COMPLETED,
                        detail={"stop_reason": stop_reason},
                        final_messages=state.messages + [assistant_message],
                    )
                    return

                # 6) 执行工具调用
                tool_results = []
                aborted = False

                for tc in tool_calls:
                    tool_name = tc.get("name") or tc.get("function", {}).get("name")
                    tool_input = tc.get("input") or tc.get("arguments", {})
                    tool_call_id = tc.get("id") or tc.get("tool_use_id", "")

                    # PreToolUse hook
                    pre_result = await self.hooks.execute_pre_tool(
                        tool_name=tool_name,
                        tool_input=tool_input,
                        context={"agent_id": state.tool_use_context.agent_id},
                    )

                    if pre_result.blocking_error:
                        tool_results.append({
                            "role": "tool",
                            "tool_use_id": tool_call_id,
                            "content": f"[拦截] {pre_result.blocking_error}",
                            "is_error": True,
                        })
                        continue

                    if pre_result.permission_decision == PermissionDecision.DENY:
                        tool_results.append({
                            "role": "tool",
                            "tool_use_id": tool_call_id,
                            "content": "[Permission denied]",
                            "is_error": True,
                        })
                        continue

                    # 用 hook 修改后的 input
                    actual_input = pre_result.updated_input or tool_input

                    # 执行工具
                    yield {"type": "tool_call_start", "tool": tool_name, "input": actual_input}

                    try:
                        if self.tools_registry:
                            tool_result = await self.tools_registry.execute(tool_name, actual_input)
                        else:
                            tool_result = {"error": "无 tools_registry"}

                        tool_results.append({
                            "role": "tool",
                            "tool_use_id": tool_call_id,
                            "content": str(tool_result),
                        })

                        yield {
                            "type": "tool_call_end",
                            "tool": tool_name,
                            "result_preview": str(tool_result)[:200],
                        }

                        # PostToolUse hook
                        async with self.hooks.emit(
                            HookEvent.POST_TOOL_USE,
                            {
                                "tool_name": tool_name,
                                "tool_input": actual_input,
                                "tool_result": tool_result,
                                "context": {"agent_id": state.tool_use_context.agent_id},
                            },
                        ) as _:
                            pass

                    except asyncio.CancelledError:
                        aborted = True
                        break
                    except Exception as e:
                        logger.error(f"工具执行失败 {tool_name}: {e}")
                        tool_results.append({
                            "role": "tool",
                            "tool_use_id": tool_call_id,
                            "content": f"[工具错误] {e}",
                            "is_error": True,
                        })

                if aborted:
                    yield Terminal(
                        reason=TerminalReason.ABORTED_TOOLS,
                        detail={},
                        final_messages=state.messages + [assistant_message] + tool_results,
                    )
                    return

                # 7) 整对象重建 State,准备下一轮
                state = replace(
                    state,
                    messages=state.messages + [assistant_message] + tool_results,
                    turn_count=state.turn_count + 1,
                    transition=Transition(reason=ContinueReason.NEXT_TURN),
                    has_attempted_reactive_compact=False,
                    max_output_tokens_recovery_count=0,
                    stop_hook_active=False,
                )
                # continue (隐式)

        except asyncio.CancelledError:
            yield Terminal(
                reason=TerminalReason.ABORTED_STREAMING,
                detail={"final_state": state.fingerprint()},
                final_messages=state.messages,
            )
        except Exception as e:
            logger.exception(f"主循环异常: {e}")
            yield Terminal(
                reason=TerminalReason.MODEL_ERROR,
                detail={"error": str(e), "final_state": state.fingerprint()},
                final_messages=state.messages,
            )
