"""多层记忆系统 - 仿 Claude Code MEMORY.md + Hermes MemoryManager

5 层记忆:
- user: 用户偏好/边界/订阅/付费等级 (永久)
- persona: 人设向量 + 风格样本 (按分支)
- project: 当前营销项目 (项目级)
- session: 当前对话上下文 (短期)
- long_term: 跨项目复用知识 (向量检索)
"""

from .system import MemorySystem, MemoryEntry, get_memory_system
from .layers import (
    UserMemoryLayer, ProjectMemoryLayer, SessionMemoryLayer,
    LongTermMemoryLayer, PersonaMemoryLayer,
)
from .compactor import MemoryCompactor

__all__ = [
    "MemorySystem", "MemoryEntry", "get_memory_system",
    "UserMemoryLayer", "ProjectMemoryLayer", "SessionMemoryLayer",
    "LongTermMemoryLayer", "PersonaMemoryLayer",
    "MemoryCompactor",
]
