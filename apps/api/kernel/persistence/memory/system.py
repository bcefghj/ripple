"""MemorySystem - 多层记忆的统一接口"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, ConfigDict

from ..db import get_conn
from .layers import (
    UserMemoryLayer, ProjectMemoryLayer, SessionMemoryLayer,
    LongTermMemoryLayer, PersonaMemoryLayer,
)


MemoryLayer = Literal["user", "project", "session", "long_term", "persona"]


class MemoryEntry(BaseModel):
    """单条记忆"""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    memory_id: str = Field(default_factory=lambda: f"mem_{uuid4().hex[:8]}")
    user_id: str
    project_id: Optional[str] = None
    session_id: Optional[str] = None
    layer: MemoryLayer
    key: str
    content: str
    embedding: Optional[List[float]] = None
    importance: float = 0.5
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MemorySystem:
    """多层记忆系统 - 顶层 API"""

    def __init__(self) -> None:
        self.user = UserMemoryLayer()
        self.project = ProjectMemoryLayer()
        self.session = SessionMemoryLayer()
        self.long_term = LongTermMemoryLayer()
        self.persona = PersonaMemoryLayer()

    def write(
        self,
        layer: MemoryLayer,
        user_id: str,
        key: str,
        content: str,
        importance: float = 0.5,
        project_id: Optional[str] = None,
        session_id: Optional[str] = None,
        embedding: Optional[List[float]] = None,
        metadata: Optional[Dict] = None,
    ) -> MemoryEntry:
        entry = MemoryEntry(
            user_id=user_id,
            project_id=project_id,
            session_id=session_id,
            layer=layer,
            key=key,
            content=content,
            importance=importance,
            embedding=embedding,
            metadata=metadata or {},
        )
        self._persist(entry)
        return entry

    def _persist(self, entry: MemoryEntry) -> None:
        with get_conn() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO memory_entries
                (memory_id, user_id, project_id, session_id, layer, key, content,
                 embedding, importance, access_count, last_accessed,
                 created_at, expires_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    entry.memory_id, entry.user_id, entry.project_id, entry.session_id,
                    entry.layer, entry.key, entry.content,
                    json.dumps(entry.embedding) if entry.embedding else None,
                    entry.importance, entry.access_count,
                    entry.last_accessed.isoformat() if entry.last_accessed else None,
                    entry.created_at.isoformat(),
                    entry.expires_at.isoformat() if entry.expires_at else None,
                    json.dumps(entry.metadata, default=str),
                ),
            )
            conn.commit()

    def recall(
        self,
        user_id: str,
        layers: Optional[List[MemoryLayer]] = None,
        project_id: Optional[str] = None,
        session_id: Optional[str] = None,
        query: str = "",
        top_k: int = 10,
    ) -> List[MemoryEntry]:
        """跨层召回 - 返回综合排序的记忆条目"""
        layers = layers or ["user", "persona", "session", "project", "long_term"]
        result: List[MemoryEntry] = []

        if "user" in layers:
            result.extend(self.user.list(user_id))
        if "persona" in layers:
            result.extend(self.persona.list(user_id))
        if "session" in layers and session_id:
            result.extend(self.session.list(user_id, session_id))
        if "project" in layers and project_id:
            result.extend(self.project.list(user_id, project_id))
        if "long_term" in layers:
            result.extend(self.long_term.search(user_id, query, top_k))

        result.sort(key=lambda e: (e.importance, e.created_at), reverse=True)
        return result[:top_k]

    def build_context(
        self,
        user_id: str,
        project_id: Optional[str] = None,
        session_id: Optional[str] = None,
        query: str = "",
        max_tokens: int = 2000,
    ) -> str:
        """召回 + 拼接为可塞入 prompt 的上下文字符串"""
        entries = self.recall(user_id, project_id=project_id, session_id=session_id, query=query, top_k=20)
        sections: Dict[str, List[str]] = {
            "user": [], "persona": [], "session": [], "project": [], "long_term": [],
        }
        for e in entries:
            sections[e.layer].append(f"[{e.key}] {e.content}")

        labels = {
            "user": "## 用户偏好",
            "persona": "## 人设特征",
            "session": "## 本次对话上下文",
            "project": "## 当前项目",
            "long_term": "## 长期知识",
        }
        parts: List[str] = []
        for layer_key in ["user", "persona", "session", "project", "long_term"]:
            if sections[layer_key]:
                parts.append(labels[layer_key])
                parts.extend(sections[layer_key][:5])
                parts.append("")

        text = "\n".join(parts)
        if len(text) > max_tokens * 3:  # rough char-to-token
            text = text[: max_tokens * 3]
        return text


_singleton: Optional[MemorySystem] = None


def get_memory_system() -> MemorySystem:
    global _singleton
    if _singleton is None:
        _singleton = MemorySystem()
    return _singleton
