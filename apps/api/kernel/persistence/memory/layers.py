"""5 层记忆层实现

每层有自己的查询语义:
- UserMemoryLayer: 全局偏好
- PersonaMemoryLayer: 人设相关
- SessionMemoryLayer: 当前对话
- ProjectMemoryLayer: 当前项目
- LongTermMemoryLayer: 跨项目知识 (向量检索)
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from ..db import get_conn

if TYPE_CHECKING:
    from .system import MemoryEntry


def _row_to_entry(row) -> "MemoryEntry":
    from .system import MemoryEntry
    return MemoryEntry(
        memory_id=row["memory_id"],
        user_id=row["user_id"],
        project_id=row["project_id"],
        session_id=row["session_id"],
        layer=row["layer"],
        key=row["key"],
        content=row["content"],
        embedding=json.loads(row["embedding"]) if row["embedding"] else None,
        importance=row["importance"],
        access_count=row["access_count"],
        last_accessed=datetime.fromisoformat(row["last_accessed"]) if row["last_accessed"] else None,
        created_at=datetime.fromisoformat(row["created_at"]),
        expires_at=datetime.fromisoformat(row["expires_at"]) if row["expires_at"] else None,
        metadata=json.loads(row["metadata"]) if row["metadata"] else {},
    )


class UserMemoryLayer:
    """用户级记忆 - 偏好/边界/订阅"""

    def list(self, user_id: str) -> List["MemoryEntry"]:
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM memory_entries WHERE user_id = ? AND layer = 'user' ORDER BY importance DESC, created_at DESC",
                (user_id,),
            ).fetchall()
            return [_row_to_entry(r) for r in rows]

    def get(self, user_id: str, key: str) -> Optional["MemoryEntry"]:
        with get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM memory_entries WHERE user_id = ? AND layer = 'user' AND key = ? LIMIT 1",
                (user_id, key),
            ).fetchone()
            return _row_to_entry(row) if row else None


class PersonaMemoryLayer:
    """人设记忆 - 风格规则、禁忌、口头禅等"""

    def list(self, user_id: str) -> List["MemoryEntry"]:
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM memory_entries WHERE user_id = ? AND layer = 'persona' ORDER BY importance DESC",
                (user_id,),
            ).fetchall()
            return [_row_to_entry(r) for r in rows]


class SessionMemoryLayer:
    """对话级记忆 - 仅当前 session 内有效"""

    def list(self, user_id: str, session_id: str) -> List["MemoryEntry"]:
        with get_conn() as conn:
            rows = conn.execute(
                """SELECT * FROM memory_entries 
                WHERE user_id = ? AND session_id = ? AND layer = 'session' 
                ORDER BY created_at DESC LIMIT 20""",
                (user_id, session_id),
            ).fetchall()
            return [_row_to_entry(r) for r in rows]

    def append_turn(
        self,
        user_id: str,
        session_id: str,
        role: str,
        content: str,
    ) -> None:
        from .system import MemoryEntry
        from ..db import get_conn as _conn
        from uuid import uuid4
        memory_id = f"sess_{uuid4().hex[:8]}"
        with _conn() as conn:
            conn.execute(
                """INSERT INTO memory_entries
                (memory_id, user_id, session_id, layer, key, content,
                 importance, access_count, created_at, metadata)
                VALUES (?, ?, ?, 'session', ?, ?, ?, 0, ?, ?)""",
                (
                    memory_id, user_id, session_id,
                    f"turn:{role}", content, 0.6,
                    datetime.utcnow().isoformat(),
                    json.dumps({"role": role}),
                ),
            )
            conn.commit()


class ProjectMemoryLayer:
    """项目级记忆 - 营销项目/系列内容/历史决策"""

    def list(self, user_id: str, project_id: str) -> List["MemoryEntry"]:
        with get_conn() as conn:
            rows = conn.execute(
                """SELECT * FROM memory_entries 
                WHERE user_id = ? AND project_id = ? AND layer = 'project' 
                ORDER BY importance DESC, created_at DESC""",
                (user_id, project_id),
            ).fetchall()
            return [_row_to_entry(r) for r in rows]


class LongTermMemoryLayer:
    """跨项目长期记忆 - 当前用关键字+importance,可后续接 chromadb 向量检索"""

    def search(self, user_id: str, query: str, top_k: int = 10) -> List["MemoryEntry"]:
        with get_conn() as conn:
            if query:
                pattern = f"%{query}%"
                rows = conn.execute(
                    """SELECT * FROM memory_entries 
                    WHERE user_id = ? AND layer = 'long_term'
                    AND (content LIKE ? OR key LIKE ?)
                    ORDER BY importance DESC, access_count DESC
                    LIMIT ?""",
                    (user_id, pattern, pattern, top_k),
                ).fetchall()
            else:
                rows = conn.execute(
                    """SELECT * FROM memory_entries 
                    WHERE user_id = ? AND layer = 'long_term'
                    ORDER BY importance DESC, access_count DESC
                    LIMIT ?""",
                    (user_id, top_k),
                ).fetchall()
            return [_row_to_entry(r) for r in rows]

    def list(self, user_id: str) -> List["MemoryEntry"]:
        return self.search(user_id, "", 50)
