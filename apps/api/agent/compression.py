"""四层上下文压缩管线 + Circuit Breaker

借鉴 Claude Code 的压缩策略:
- Layer 0: applyToolResultBudget (限制单次工具结果大小)
- Layer 1: HISTORY_SNIP (删除无关消息,零成本)
- Layer 2: Microcompact (按 tool_use_id 删冗余)
- Layer 3: Context Collapse (结构化摘要替换片段)
- Layer 4: Auto-compact (全量压缩,最后手段)

Circuit Breaker:
- MAX_CONSECUTIVE_AUTOCOMPACT_FAILURES = 3
- has_attempted_reactive_compact 单次,防死循环
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, List, Optional

from loguru import logger


@dataclass
class CompressionConfig:
    """压缩配置"""
    autocompact_buffer_tokens: int = 13_000  # 距离窗口顶端预留
    manual_compact_buffer_tokens: int = 3_000  # 硬阻塞预留
    max_consecutive_autocompact_failures: int = 3
    max_tool_result_chars: int = 50_000  # 单个 tool result 最大字符数
    pct_override: Optional[float] = None  # CLAUDE_AUTOCOMPACT_PCT_OVERRIDE 等价


# ============================================================
# Token 估算(粗略)
# ============================================================

def estimate_tokens(messages: List[Dict[str, Any]]) -> int:
    """粗略估算 token 数(中文 1 字 ≈ 2 token,英文 1 词 ≈ 1.3 token)"""
    total_chars = 0
    for msg in messages:
        content = msg.get("content", "")
        if isinstance(content, str):
            total_chars += len(content)
        elif isinstance(content, list):
            for part in content:
                if isinstance(part, dict):
                    text = part.get("text", "") or part.get("content", "")
                    total_chars += len(text)
    # 中英混合估算
    return total_chars * 2


# ============================================================
# 压缩管线
# ============================================================


class CompressionPipeline:
    """完整压缩管线"""

    def __init__(
        self,
        cfg: CompressionConfig,
        effective_window_tokens: int,
        summarize_fn: Optional[Callable[[List[Dict[str, Any]]], Awaitable[str]]] = None,
    ):
        self.cfg = cfg
        self.effective_window_tokens = effective_window_tokens
        self.summarize_fn = summarize_fn

    def get_autocompact_threshold(self) -> int:
        """计算 auto-compact 触发阈值"""
        base = self.effective_window_tokens - self.cfg.autocompact_buffer_tokens
        if self.cfg.pct_override is None:
            return base
        pct_thr = int(self.effective_window_tokens * (self.cfg.pct_override / 100.0))
        return min(pct_thr, base)  # 不能高于默认阈值

    def get_blocking_threshold(self) -> int:
        """硬阻塞阈值"""
        return self.effective_window_tokens - self.cfg.manual_compact_buffer_tokens

    async def run_full_pipeline(
        self,
        messages: List[Dict[str, Any]],
        tracking: Optional[Any] = None,  # AutoCompactTracking
    ) -> List[Dict[str, Any]]:
        """完整四层压缩"""
        m = self.apply_tool_result_budget(messages)
        m = self.snip_compact(m)
        m = self.microcompact(m)

        current_tokens = estimate_tokens(m)
        if current_tokens > self.get_autocompact_threshold():
            m = await self.context_collapse(m)
            current_tokens = estimate_tokens(m)
            if current_tokens > self.get_autocompact_threshold():
                m = await self.maybe_autocompact(m, tracking)

        return m

    # --------- Layer 0 ---------

    def apply_tool_result_budget(
        self, messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Layer 0: 截断超大 tool result"""
        result = []
        for msg in messages:
            if msg.get("role") == "tool":
                content = msg.get("content", "")
                if isinstance(content, str) and len(content) > self.cfg.max_tool_result_chars:
                    truncated = (
                        content[: self.cfg.max_tool_result_chars]
                        + f"\n\n[... 已截断,原长度 {len(content)} 字符 ...]"
                    )
                    msg = {**msg, "content": truncated}
            result.append(msg)
        return result

    # --------- Layer 1: HISTORY_SNIP ---------

    def snip_compact(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Layer 1: 删除明显无关的旧消息(零 LLM 成本)
        
        策略:
        - 保留最近 N 条
        - 保留所有 system 消息
        - 删除超过保留窗口的 tool result
        """
        if len(messages) <= 30:
            return messages

        result = []
        recent_count = 0
        max_recent = 25

        # 从后往前保留 max_recent 条非 system 消息
        for msg in reversed(messages):
            role = msg.get("role")
            if role == "system":
                result.insert(0, msg)
            elif recent_count < max_recent:
                result.insert(0, msg)
                recent_count += 1
            else:
                # 旧消息只保留 user/assistant 的简短摘要
                if role in ("user", "assistant"):
                    content = msg.get("content", "")
                    if isinstance(content, str) and len(content) < 200:
                        result.insert(0, msg)
                        recent_count += 1

        if len(result) < len(messages):
            logger.debug(f"snip_compact: {len(messages)} -> {len(result)}")
        return result

    # --------- Layer 2: Microcompact ---------

    def microcompact(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Layer 2: 按 tool_use_id 删除冗余 tool result
        
        若同一 tool_use_id 有多个 result,只保留最新的
        """
        seen_tool_use_ids: Dict[str, int] = {}
        result = list(messages)

        # 倒序遍历,记录最后出现的 tool_use_id
        for i in range(len(result) - 1, -1, -1):
            msg = result[i]
            if msg.get("role") == "tool":
                tool_use_id = msg.get("tool_use_id") or msg.get("tool_call_id")
                if tool_use_id:
                    if tool_use_id in seen_tool_use_ids:
                        # 已有更新的同 ID result,标记本条为待删除
                        result[i] = None  # type: ignore
                    else:
                        seen_tool_use_ids[tool_use_id] = i

        return [m for m in result if m is not None]

    # --------- Layer 3: Context Collapse ---------

    async def context_collapse(
        self, messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Layer 3: 用结构化摘要替换中间消息片段"""
        if len(messages) <= 15:
            return messages

        # 保留 system + 最近 10 条
        system_msgs = [m for m in messages if m.get("role") == "system"]
        non_system = [m for m in messages if m.get("role") != "system"]

        if len(non_system) <= 10:
            return messages

        to_collapse = non_system[: -10]
        keep_recent = non_system[-10:]

        if self.summarize_fn:
            try:
                summary = await self.summarize_fn(to_collapse)
                summary_msg = {
                    "role": "system",
                    "content": f"[Context Collapse 摘要 - 替换 {len(to_collapse)} 条历史消息]\n\n{summary}",
                }
                return system_msgs + [summary_msg] + keep_recent
            except Exception as e:
                logger.warning(f"context_collapse 摘要失败: {e}")

        # 无 summarize_fn,降级为简单合并
        joined = "\n\n".join(
            f"[{m.get('role')}]: {str(m.get('content', ''))[:300]}" for m in to_collapse
        )
        summary_msg = {
            "role": "system",
            "content": f"[Context Collapse - 简单合并 {len(to_collapse)} 条]\n\n{joined}",
        }
        return system_msgs + [summary_msg] + keep_recent

    # --------- Layer 4: Auto-compact ---------

    async def maybe_autocompact(
        self,
        messages: List[Dict[str, Any]],
        tracking: Optional[Any] = None,
    ) -> List[Dict[str, Any]]:
        """Layer 4: 全量摘要压缩(最后手段)
        
        Circuit breaker:连续失败 3 次后停止尝试
        """
        if tracking and getattr(tracking, "flag_disabled", False):
            logger.warning("auto-compact 已被 circuit breaker 禁用")
            return messages

        if tracking and tracking.consecutive_failures >= self.cfg.max_consecutive_autocompact_failures:
            tracking.flag_disabled = True
            logger.error(
                f"auto-compact 连续失败 {tracking.consecutive_failures} 次,触发 circuit breaker"
            )
            return messages

        if not self.summarize_fn:
            return messages

        try:
            summary = await self.summarize_fn(messages)
            new_messages = [
                {
                    "role": "system",
                    "content": f"[Auto-compact 全量摘要 - 替换 {len(messages)} 条对话]\n\n{summary}",
                }
            ]
            if tracking:
                tracking.consecutive_failures = 0
            logger.info(f"auto-compact 成功: {len(messages)} -> {len(new_messages)}")
            return new_messages
        except Exception as e:
            if tracking:
                tracking.consecutive_failures += 1
            logger.error(f"auto-compact 失败 ({tracking.consecutive_failures if tracking else '?'}): {e}")
            return messages
