"""MemoryCompactor - 后台 Dream 巩固

仿 Claude Code 的多阈值压缩 + 后台合并:
- 多次访问的 session 记忆 → long_term
- 矛盾记忆 → 用 LLM 合并
- 过期记忆 → 删除
- 冗余记忆 → 摘要
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Awaitable, Callable, List, Optional

from ..db import get_conn
from .layers import _row_to_entry


LLMSummarizer = Callable[[str], Awaitable[str]]


class MemoryCompactor:
    """后台 Dream 任务"""

    def __init__(self, llm_summarizer: Optional[LLMSummarizer] = None) -> None:
        self.summarize = llm_summarizer

    def find_compactable_sessions(self, max_age_hours: int = 24) -> List[str]:
        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        with get_conn() as conn:
            rows = conn.execute(
                """SELECT session_id, COUNT(*) as cnt, MIN(created_at) as oldest
                FROM memory_entries 
                WHERE layer = 'session' AND created_at < ?
                GROUP BY session_id HAVING cnt >= 5""",
                (cutoff.isoformat(),),
            ).fetchall()
            return [r["session_id"] for r in rows]

    async def compact_session(self, session_id: str) -> Optional[str]:
        """把 session 记忆压缩成 1 条 long_term 记忆"""
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM memory_entries WHERE session_id = ? AND layer = 'session' ORDER BY created_at",
                (session_id,),
            ).fetchall()
            if not rows:
                return None
            entries = [_row_to_entry(r) for r in rows]
            user_id = entries[0].user_id

            transcript = "\n".join(
                f"[{e.metadata.get('role','')}] {e.content[:200]}" for e in entries
            )

            if self.summarize is not None:
                try:
                    summary = await self.summarize(transcript)
                except Exception:
                    summary = transcript[:500]
            else:
                summary = transcript[:500]

            from .system import get_memory_system
            ms = get_memory_system()
            ms.write(
                layer="long_term",
                user_id=user_id,
                key=f"session_summary:{session_id}",
                content=summary,
                importance=0.7,
                metadata={"compacted_from": session_id, "turn_count": len(entries)},
            )

            with get_conn() as conn2:
                conn2.execute(
                    "DELETE FROM memory_entries WHERE session_id = ? AND layer = 'session'",
                    (session_id,),
                )
                conn2.commit()

            return summary

    def cleanup_expired(self) -> int:
        now = datetime.utcnow().isoformat()
        with get_conn() as conn:
            cur = conn.execute(
                "DELETE FROM memory_entries WHERE expires_at IS NOT NULL AND expires_at < ?",
                (now,),
            )
            conn.commit()
            return cur.rowcount or 0
