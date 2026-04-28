"""PersonaExtractor - 从历史样本提取人设维度

不依赖外部 embedding 服务,用启发式 + LLM 双路:
1. 启发式: 句长、emoji 密度、感叹号频率等可解释维度
2. LLM 抽取: 用 MiMo 抽取风格特征 (formality / humor / professional)
3. 简单 hash embedding: 用字符 n-gram 哈希到 256 维 (作为兜底,后续可换 sentence-transformers)
"""

from __future__ import annotations

import hashlib
import re
import statistics
from typing import List, Optional

from ...types import PersonaDimensions
from ..llm import quick_chat


_EMOJI_PAT = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport
    "\U0001F1E0-\U0001F1FF"  # flags
    "\U00002500-\U00002BEF"
    "\U00002702-\U000027B0"
    "]+",
    flags=re.UNICODE,
)


def _heuristic_dimensions(samples: List[str]) -> PersonaDimensions:
    """启发式抽取可解释维度"""
    if not samples:
        return PersonaDimensions()

    sentences: List[str] = []
    for s in samples:
        sentences.extend(re.split(r"[。！？!?\n]+", s))
    sentences = [s.strip() for s in sentences if s.strip()]

    if not sentences:
        return PersonaDimensions()

    avg_len = statistics.mean(len(s) for s in sentences) if sentences else 30.0
    total_chars = sum(len(s) for s in samples)
    if total_chars == 0:
        return PersonaDimensions()

    emoji_count = sum(len(_EMOJI_PAT.findall(s)) for s in samples)
    exclamation_count = sum(s.count("！") + s.count("!") for s in samples)
    question_count = sum(s.count("？") + s.count("?") for s in samples)
    first_person_count = sum(s.count("我") for s in samples)

    professional_markers = sum(
        s.count(kw) for s in samples
        for kw in ["分析", "评测", "数据", "成分", "原理", "因为", "建议", "结论"]
    )
    humor_markers = sum(
        s.count(kw) for s in samples
        for kw in ["哈哈", "笑死", "绝绝子", "yyds", "蚌埠", "破防", "无语"]
    )
    vulnerability_markers = sum(
        s.count(kw) for s in samples
        for kw in ["其实", "说实话", "我也", "踩雷", "翻车", "失败"]
    )

    return PersonaDimensions(
        formality=min(1.0, professional_markers / max(1, len(samples) * 2)),
        technicality=min(1.0, professional_markers / max(1, len(samples) * 3)),
        humor_density=min(1.0, humor_markers / max(1, len(samples))),
        sentence_length_avg=min(100.0, avg_len),
        emoji_density=min(1.0, emoji_count / max(1, total_chars / 100)),
        first_person_freq=min(1.0, first_person_count / max(1, total_chars / 50)),
        questions_freq=min(1.0, question_count / max(1, len(sentences))),
        exclamation_freq=min(1.0, exclamation_count / max(1, len(sentences))),
        professional_jargon=min(1.0, professional_markers / max(1, total_chars / 100)),
        vulnerability_disclosure=min(1.0, vulnerability_markers / max(1, len(samples))),
    )


def _hash_embedding(samples: List[str], dim: int = 256) -> List[float]:
    """简易 hash embedding - 字符 trigram 哈希到 dim 维空间"""
    text = "\n".join(samples)
    if not text:
        return [0.0] * dim
    vec = [0.0] * dim
    for i in range(len(text) - 2):
        trigram = text[i : i + 3]
        h = int(hashlib.md5(trigram.encode()).hexdigest(), 16)
        idx = h % dim
        vec[idx] += 1.0
    norm = sum(v * v for v in vec) ** 0.5
    if norm > 0:
        vec = [v / norm for v in vec]
    return vec


async def extract_dimensions_with_llm(samples: List[str]) -> Optional[PersonaDimensions]:
    """用 LLM 抽取人设维度 - 更精细"""
    if not samples:
        return None
    sample_text = "\n---\n".join(s[:300] for s in samples[:5])
    sys = (
        "你是 KOC 人设分析师。从给定文案样本中,抽取写作风格的可解释指标。"
        "输出严格 JSON,字段含: formality(0-1), technicality(0-1), humor_density(0-1), "
        "sentence_length_avg(数字), emoji_density(0-1), first_person_freq(0-1), "
        "questions_freq(0-1), exclamation_freq(0-1), professional_jargon(0-1), "
        "vulnerability_disclosure(0-1). 仅返回 JSON,不要解释。"
    )
    user = f"样本:\n{sample_text}"
    try:
        text = await quick_chat(sys, user, json_mode=True, max_tokens=600)
        import json as _json
        data = _json.loads(text)
        return PersonaDimensions(**data)
    except Exception:
        return None


class PersonaExtractor:
    """统一抽取入口"""

    async def extract(
        self,
        samples: List[str],
        use_llm: bool = True,
    ) -> tuple[PersonaDimensions, List[float]]:
        """返回 (维度, embedding)"""
        heuristic = _heuristic_dimensions(samples)
        if use_llm:
            llm_dims = await extract_dimensions_with_llm(samples)
            if llm_dims is not None:
                merged = PersonaDimensions(
                    formality=(heuristic.formality + llm_dims.formality) / 2,
                    technicality=(heuristic.technicality + llm_dims.technicality) / 2,
                    humor_density=(heuristic.humor_density + llm_dims.humor_density) / 2,
                    sentence_length_avg=(heuristic.sentence_length_avg + llm_dims.sentence_length_avg) / 2,
                    emoji_density=(heuristic.emoji_density + llm_dims.emoji_density) / 2,
                    first_person_freq=(heuristic.first_person_freq + llm_dims.first_person_freq) / 2,
                    questions_freq=(heuristic.questions_freq + llm_dims.questions_freq) / 2,
                    exclamation_freq=(heuristic.exclamation_freq + llm_dims.exclamation_freq) / 2,
                    professional_jargon=(heuristic.professional_jargon + llm_dims.professional_jargon) / 2,
                    vulnerability_disclosure=(heuristic.vulnerability_disclosure + llm_dims.vulnerability_disclosure) / 2,
                )
                return merged, _hash_embedding(samples)
        return heuristic, _hash_embedding(samples)


def extract_dimensions(samples: List[str]) -> PersonaDimensions:
    """同步快捷接口 - 仅启发式"""
    return _heuristic_dimensions(samples)


def cosine_similarity(a: List[float], b: List[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    if na * nb == 0:
        return 0.0
    return dot / (na * nb)


def euclidean_distance(a: List[float], b: List[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 1.0
    return sum((x - y) ** 2 for x, y in zip(a, b)) ** 0.5


def ema_update(old_vec: List[float], new_vec: List[float], alpha: float = 0.2) -> List[float]:
    """EMA 增量更新人设向量 - alpha 越大越快忘记历史"""
    if not old_vec:
        return new_vec
    if len(old_vec) != len(new_vec):
        return new_vec
    return [(1 - alpha) * o + alpha * n for o, n in zip(old_vec, new_vec)]
