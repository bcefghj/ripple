"""Subagent (Task tool) - 同构子循环

借鉴 Claude Code Task tool:
- Task = 再起一个 query() (同构循环)
- 子代理独立 messages
- 选择性共享/克隆 ToolUseContext
- 权限 bubble 到父进程
- depth 限制(防递归爆栈)
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Awaitable, Callable, Dict, List, Optional

from loguru import logger

from .agent_loop import AgentLoop
from .state import LoopState, Terminal, TerminalReason, ToolUseContext


MAX_SUBAGENT_DEPTH = 3  # 防止无限递归


async def run_subagent(
    parent_loop: AgentLoop,
    parent_state: LoopState,
    subagent_id: str,
    initial_messages: List[Dict[str, Any]],
    system_prompt: str,
    max_turns: int = 10,
    skip_transcript: bool = True,
    inherit_tools: bool = True,
    depth: int = 0,
) -> Terminal:
    """
    运行子代理 - 同构循环
    
    Args:
        parent_loop: 父循环(共享 LLM/Tools/Hooks)
        parent_state: 父状态(用于 fork context)
        subagent_id: 子代理标识(如 "research" / "fact_check")
        initial_messages: 子代理独立的初始消息
        system_prompt: 子代理专属 system prompt
        max_turns: 子代理最大轮数
        skip_transcript: 是否跳过转录(默认 True,只返回结果)
        inherit_tools: 是否继承父工具集
        depth: 当前递归深度
    
    Returns:
        Terminal: 子代理的最终结果
    """
    if depth >= MAX_SUBAGENT_DEPTH:
        return Terminal(
            reason=TerminalReason.MAX_TURNS,
            detail={"error": f"Subagent depth {depth} exceeded max {MAX_SUBAGENT_DEPTH}"},
            final_messages=[],
        )

    # 1) Fork context
    sub_context = parent_state.tool_use_context.fork_for_subagent(subagent_id)

    # 2) 构造子代理初始 state
    sub_state = LoopState(
        messages=initial_messages,
        tool_use_context=sub_context,
        turn_count=1,
        tokens_used_total=0,
        cost_usd_total=0.0,
    )

    # 3) 运行子代理(同构 AgentLoop)
    sub_loop = AgentLoop(
        llm_call=parent_loop.llm_call,
        tools_registry=parent_loop.tools_registry if inherit_tools else None,
        hooks=parent_loop.hooks,  # 共享 hooks
        compression=parent_loop.compression,
        max_turns=max_turns,
        budget_tokens=parent_loop.budget_tokens,
    )

    logger.info(f"[Subagent {subagent_id}] depth={depth} max_turns={max_turns}")

    final_terminal: Optional[Terminal] = None
    async for event in sub_loop.run(sub_state, system_prompt):
        if isinstance(event, Terminal):
            final_terminal = event
            break
        # 默认 skip_transcript,不传播中间事件

    if final_terminal is None:
        return Terminal(
            reason=TerminalReason.MODEL_ERROR,
            detail={"error": "Subagent did not produce Terminal"},
        )

    logger.info(
        f"[Subagent {subagent_id}] terminated: {final_terminal.reason} "
        f"tokens={sum(1 for _ in final_terminal.final_messages)} msgs"
    )
    return final_terminal


async def run_parallel_subagents(
    parent_loop: AgentLoop,
    parent_state: LoopState,
    tasks: List[Dict[str, Any]],
) -> List[Terminal]:
    """并行运行多个子代理(用于 Orchestrator-Workers 模式)
    
    Args:
        tasks: List of dicts with keys: subagent_id, initial_messages, system_prompt, max_turns
    """
    import asyncio

    coroutines = [
        run_subagent(
            parent_loop=parent_loop,
            parent_state=parent_state,
            **task,
        )
        for task in tasks
    ]
    return await asyncio.gather(*coroutines, return_exceptions=False)
