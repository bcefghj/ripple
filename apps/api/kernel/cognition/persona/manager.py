"""PersonaManager - 人设的全生命周期管理

API:
- calibrate(user_id, samples): 用样本初始化/校准人设
- ingest(user_id, content): 增量更新 (EMA)
- get(user_id, branch): 获取当前人设
- branch(user_id, name): 开实验分支
- merge(user_id, branch_name): 合并实验回主线
- check_drift(user_id, content): 检查新内容是否漂移
- style_constraint_prompt(persona): 生成风格约束 prompt 注入 LLM
"""

from __future__ import annotations

from typing import List, Optional
from uuid import uuid4

from ...types import PersonaDimensions, PersonaVector
from .extractor import (
    PersonaExtractor, _heuristic_dimensions, _hash_embedding,
    cosine_similarity, ema_update,
)
from .store import PersonaStore, get_persona_store


DRIFT_THRESHOLD = 0.65  # cosine 低于这个就报警
DRIFT_HARD_THRESHOLD = 0.4  # 低于这个直接熔断


class DriftReport:
    def __init__(
        self,
        similarity: float,
        drift_score: float,
        warning: bool,
        block: bool,
        explanation: str,
    ) -> None:
        self.similarity = similarity
        self.drift_score = drift_score
        self.warning = warning
        self.block = block
        self.explanation = explanation


class PersonaManager:
    def __init__(self, store: Optional[PersonaStore] = None) -> None:
        self.store = store or get_persona_store()
        self.extractor = PersonaExtractor()

    async def calibrate(
        self,
        user_id: str,
        samples: List[str],
        branch: str = "main",
        notes: str = "",
        use_llm: bool = True,
    ) -> PersonaVector:
        """用 5+ 历史样本初始化人设"""
        if not samples:
            raise ValueError("Need at least 1 sample to calibrate")

        for s in samples:
            self.store.add_sample(user_id, s, platform="onboarding")

        dims, embedding = await self.extractor.extract(samples, use_llm=use_llm)
        vec = PersonaVector(
            user_id=user_id,
            branch=branch,
            embedding=embedding,
            dimensions=dims,
            sample_count=len(samples),
            notes=notes or "Initial calibration",
        )
        return self.store.upsert(vec)

    async def ingest(
        self,
        user_id: str,
        new_content: str,
        branch: str = "main",
        alpha: float = 0.15,
    ) -> tuple[PersonaVector, DriftReport]:
        """新内容增量更新 - 同时检测漂移"""
        existing = self.store.get(user_id, branch)
        if existing is None:
            return await self.calibrate(user_id, [new_content], branch=branch), DriftReport(
                similarity=1.0, drift_score=0.0, warning=False, block=False,
                explanation="首次入库, 已初始化人设。",
            )

        if existing.locked:
            drift = await self.check_drift(user_id, new_content, branch=branch)
            return existing, drift

        new_dims, new_emb = await self.extractor.extract([new_content], use_llm=False)
        sim = cosine_similarity(existing.embedding, new_emb)
        drift_score = 1.0 - sim
        warning = sim < DRIFT_THRESHOLD
        block = sim < DRIFT_HARD_THRESHOLD

        if block:
            explanation = f"新内容与人设相似度 {sim:.2f} 低于硬熔断阈值 {DRIFT_HARD_THRESHOLD},已拒绝合入主线。"
            return existing, DriftReport(
                similarity=sim, drift_score=drift_score,
                warning=True, block=True, explanation=explanation,
            )

        merged_emb = ema_update(existing.embedding, new_emb, alpha=alpha)
        merged_dims = PersonaDimensions(
            formality=(1 - alpha) * existing.dimensions.formality + alpha * new_dims.formality,
            technicality=(1 - alpha) * existing.dimensions.technicality + alpha * new_dims.technicality,
            humor_density=(1 - alpha) * existing.dimensions.humor_density + alpha * new_dims.humor_density,
            sentence_length_avg=(1 - alpha) * existing.dimensions.sentence_length_avg + alpha * new_dims.sentence_length_avg,
            emoji_density=(1 - alpha) * existing.dimensions.emoji_density + alpha * new_dims.emoji_density,
            first_person_freq=(1 - alpha) * existing.dimensions.first_person_freq + alpha * new_dims.first_person_freq,
            questions_freq=(1 - alpha) * existing.dimensions.questions_freq + alpha * new_dims.questions_freq,
            exclamation_freq=(1 - alpha) * existing.dimensions.exclamation_freq + alpha * new_dims.exclamation_freq,
            professional_jargon=(1 - alpha) * existing.dimensions.professional_jargon + alpha * new_dims.professional_jargon,
            vulnerability_disclosure=(1 - alpha) * existing.dimensions.vulnerability_disclosure + alpha * new_dims.vulnerability_disclosure,
        )

        existing.embedding = merged_emb
        existing.dimensions = merged_dims
        existing.sample_count += 1
        existing.drift_score = drift_score
        explanation = (
            f"已增量更新 (alpha={alpha}). 新样本相似度 {sim:.2f}." +
            (" [WARNING] 偏离主线请关注。" if warning else "")
        )
        self.store.add_sample(user_id, new_content)
        return self.store.upsert(existing), DriftReport(
            similarity=sim, drift_score=drift_score,
            warning=warning, block=False, explanation=explanation,
        )

    def get(self, user_id: str, branch: str = "main") -> Optional[PersonaVector]:
        return self.store.get(user_id, branch)

    def list_branches(self, user_id: str) -> List[str]:
        return self.store.list_branches(user_id)

    def branch(self, user_id: str, branch_name: str, parent: str = "main") -> PersonaVector:
        """从 parent 分支创建新分支"""
        parent_vec = self.store.get(user_id, parent)
        if parent_vec is None:
            raise ValueError(f"Parent branch {parent} not found")
        new_vec = PersonaVector(
            user_id=user_id,
            branch=branch_name,
            parent_branch=parent,
            embedding=list(parent_vec.embedding),
            dimensions=parent_vec.dimensions.model_copy(),
            sample_count=parent_vec.sample_count,
            notes=f"Branch from {parent}",
        )
        return self.store.upsert(new_vec)

    def merge(
        self,
        user_id: str,
        from_branch: str,
        into_branch: str = "main",
        alpha: float = 0.3,
    ) -> PersonaVector:
        """合并分支 - alpha 控制实验风格融入比例"""
        src = self.store.get(user_id, from_branch)
        dst = self.store.get(user_id, into_branch)
        if src is None or dst is None:
            raise ValueError("Branches not found")
        merged_emb = ema_update(dst.embedding, src.embedding, alpha=alpha)
        dst.embedding = merged_emb
        dst.notes = f"{dst.notes} | merged {from_branch}@v{src.version}"
        return self.store.upsert(dst)

    async def check_drift(
        self,
        user_id: str,
        content: str,
        branch: str = "main",
    ) -> DriftReport:
        """只检查不更新 - 用于发布前预检"""
        existing = self.store.get(user_id, branch)
        if existing is None:
            return DriftReport(1.0, 0.0, False, False, "尚无人设基线,跳过检查")

        new_dims, new_emb = await self.extractor.extract([content], use_llm=False)
        sim = cosine_similarity(existing.embedding, new_emb)
        drift_score = 1.0 - sim
        warning = sim < DRIFT_THRESHOLD
        block = sim < DRIFT_HARD_THRESHOLD
        explanation = (
            f"相似度 {sim:.2f} (阈值 warn={DRIFT_THRESHOLD}, block={DRIFT_HARD_THRESHOLD}). " +
            ("[BLOCK] 严重偏离人设,建议拒绝。" if block else "[WARN] 偏离主线。" if warning else "符合人设主线。")
        )
        return DriftReport(sim, drift_score, warning, block, explanation)

    def style_constraint_prompt(self, persona: PersonaVector) -> str:
        """生成 LLM 风格约束 prompt - 注入 system 消息"""
        d = persona.dimensions

        def level(v: float, low: str, mid: str, high: str) -> str:
            return high if v > 0.66 else mid if v > 0.33 else low

        return (
            "## 人设约束 (严格遵守)\n"
            f"- 正式度: {level(d.formality, '口语化随意', '半正式', '正式严谨')}\n"
            f"- 专业度: {level(d.technicality, '科普向通俗', '专业但易懂', '深度专业')}\n"
            f"- 幽默感: {level(d.humor_density, '严肃克制', '适度幽默', '轻松搞笑')}\n"
            f"- 平均句长: 约 {int(d.sentence_length_avg)} 字\n"
            f"- emoji 使用: {level(d.emoji_density, '少用或不用', '适度', '密集使用')}\n"
            f"- 第一人称频率: {level(d.first_person_freq, '少用我', '正常', '高频用我')}\n"
            f"- 自我袒露度: {level(d.vulnerability_disclosure, '保留克制', '适度分享', '坦诚大方')}\n"
            f"\n## 注意\n生成内容必须保持以上风格,与历史样本一致。如检测到风格偏离,请自我纠正。"
        )


_manager_singleton: Optional[PersonaManager] = None


def get_persona_manager() -> PersonaManager:
    global _manager_singleton
    if _manager_singleton is None:
        _manager_singleton = PersonaManager()
    return _manager_singleton
