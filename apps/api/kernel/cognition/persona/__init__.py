"""Persona Vector - KOC 人设向量化

核心创新:
1. 256 维 embedding + 10 维可解释指标
2. EMA 增量更新 (新内容融入旧风格)
3. Drift 熔断 (风格突变报警)
4. Git for Voice (主线 + 实验分支 + merge/rollback)
5. 风格约束生成 (LLM prompt 注入)
"""

from .extractor import PersonaExtractor, extract_dimensions
from .store import PersonaStore, get_persona_store
from .manager import PersonaManager, get_persona_manager

__all__ = [
    "PersonaExtractor", "extract_dimensions",
    "PersonaStore", "get_persona_store",
    "PersonaManager", "get_persona_manager",
]
