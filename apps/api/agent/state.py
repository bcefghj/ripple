"""LoopState - 整对象替换的循环状态

借鉴 Claude Code query.ts 的设计:
- 每个 continue 路径都"整对象重建" State,避免半更新 bug
- 显式 Terminal 联合返回类型,10 种结束原因
- 7 类 continue 路径

参考:
- claude-code-from-source/book/ch05-agent-loop.md
- HarrisonSec query loop 深潜
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ContinueReason(str, Enum):
    """循环 continue 路径的语义分类"""
    COLLAPSE_DRAIN_RETRY = "collapse_drain_retry"
    REACTIVE_COMPACT_RETRY = "reactive_compact_retry"
    MAX_OUTPUT_TOKENS_ESCALATE = "max_output_tokens_escalate"
    MAX_OUTPUT_TOKENS_RECOVERY = "max_output_tokens_recovery"
    STOP_HOOK_BLOCKING = "stop_hook_blocking"
    TOKEN_BUDGET_CONTINUATION = "token_budget_continuation"
    NEXT_TURN = "next_turn"


class TerminalReason(str, Enum):
    """循环结束的语义分类(共 10 种)"""
    COMPLETED = "completed"  # 模型主动结束
    MAX_TURNS = "max_turns"  # 达到最大轮数
    PROMPT_TOO_LONG = "prompt_too_long"  # 提示过长无法压缩
    BLOCKING_LIMIT = "blocking_limit"  # 阻塞限制
    MODEL_ERROR = "model_error"  # 模型 API 错误
    ABORTED_STREAMING = "aborted_streaming"  # 流式中断
    ABORTED_TOOLS = "aborted_tools"  # 工具执行中断
    HOOK_STOPPED = "hook_stopped"  # Hook 主动停止
    STOP_HOOK_PREVENTED = "stop_hook_prevented"  # Stop hook 阻止继续
    BUDGET_EXCEEDED = "budget_exceeded"  # 预算超限


@dataclass(frozen=True)
class Transition:
    """单次 continue 的元信息(用于审计与可观测性)"""
    reason: ContinueReason
    detail: Optional[Dict[str, Any]] = None


@dataclass
class Terminal:
    """循环结束的最终结果"""
    reason: TerminalReason
    detail: Dict[str, Any] = field(default_factory=dict)
    final_messages: List[Dict[str, Any]] = field(default_factory=list)

    def is_success(self) -> bool:
        return self.reason == TerminalReason.COMPLETED


@dataclass
class AutoCompactTracking:
    """自动压缩追踪(用于 circuit breaker)"""
    consecutive_failures: int = 0
    compacted_turn_id: Optional[str] = None
    last_trigger_tokens: int = 0
    flag_disabled: bool = False


@dataclass
class ToolUseContext:
    """工具调用上下文(传递给 tool / hook / subagent)"""
    permission_mode: str = "auto"  # auto / ask / bypass
    abort_event: Optional[Any] = None  # asyncio.Event
    read_file_state: Dict[str, Any] = field(default_factory=dict)
    options: Dict[str, Any] = field(default_factory=dict)
    agent_id: Optional[str] = None
    tenant_id: Optional[str] = None  # 多租户隔离
    user_id: Optional[str] = None
    rendered_system_prompt_fingerprint: Optional[str] = None
    local_denial_tracking: Dict[str, int] = field(default_factory=dict)

    def fork_for_subagent(self, agent_id: str) -> "ToolUseContext":
        """子代理上下文 - 选择性共享/克隆(借鉴 createSubagentContext)"""
        return ToolUseContext(
            permission_mode=self.permission_mode,
            abort_event=self.abort_event,
            read_file_state=self.read_file_state,  # 共享
            options=self.options,
            agent_id=agent_id,
            tenant_id=self.tenant_id,
            user_id=self.user_id,
            rendered_system_prompt_fingerprint=self.rendered_system_prompt_fingerprint,
            local_denial_tracking={},  # 子代理新建
        )


@dataclass
class LoopState:
    """
    循环状态对象 - 每次 continue 都"整对象替换"
    
    重要:不要在 continue 之前 mutating 这个对象的字段,
    必须用 dataclasses.replace() 或新建 LoopState 实例。
    """
    messages: List[Dict[str, Any]] = field(default_factory=list)
    tool_use_context: ToolUseContext = field(default_factory=ToolUseContext)
    turn_count: int = 1

    # 压缩相关
    auto_compact_tracking: Optional[AutoCompactTracking] = None
    has_attempted_reactive_compact: bool = False

    # max_output_tokens 阶梯恢复(上限 3)
    max_output_tokens_recovery_count: int = 0
    max_output_tokens_override: Optional[int] = None

    # Stop hook 状态
    stop_hook_active: bool = False

    # 摘要预取(异步)
    pending_tool_use_summary: Optional[Any] = None  # asyncio.Task

    # 上次 transition(用于可观测性)
    transition: Optional[Transition] = None

    # 预算追踪
    tokens_used_total: int = 0
    cost_usd_total: float = 0.0

    def fingerprint(self) -> str:
        """用于日志/trace 的简短指纹"""
        return f"turn={self.turn_count}/msgs={len(self.messages)}/tokens={self.tokens_used_total}"
