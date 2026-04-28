"""CrossVerifier - 多源交叉验证

机制:
1. 同一论断从多个数据源拉取
2. 计算一致性 score (Jaccard 关键词 / cosine embedding)
3. 一致性低则标记 low_confidence
4. 触发 Forum 辩论展示对立观点
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

from ...types import Citation


def _extract_keywords(text: str) -> set:
    if not text:
        return set()
    words = re.findall(r"[\u4e00-\u9fa5]{2,4}|[a-zA-Z]{3,}", text.lower())
    stopwords = {"the", "and", "for", "are", "but", "not", "with", "from", "this", "that"}
    return set(w for w in words if w not in stopwords)


def jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / max(1, len(a | b))


class CrossVerifier:
    """跨源验证器"""

    def verify_claim(
        self,
        claim: str,
        evidence_pool: List[Tuple[str, str]],  # [(source_id, text), ...]
        threshold: float = 0.25,
    ) -> Dict:
        """对一个 claim,看 evidence_pool 中有多少源支持/反对

        返回: {
          consistency_score: 0-1,
          supporting_sources: [source_id, ...],
          contradicting_sources: [source_id, ...],
          confidence: low/mid/high
        }
        """
        claim_kw = _extract_keywords(claim)
        if not claim_kw:
            return {
                "consistency_score": 0.0,
                "supporting_sources": [],
                "contradicting_sources": [],
                "confidence": "low",
            }

        supporting = []
        all_overlaps = []
        for source_id, text in evidence_pool:
            ev_kw = _extract_keywords(text)
            ov = jaccard(claim_kw, ev_kw)
            all_overlaps.append(ov)
            if ov >= threshold:
                supporting.append(source_id)

        avg = sum(all_overlaps) / max(1, len(all_overlaps))
        confidence = "high" if avg >= 0.4 and len(supporting) >= 2 else "mid" if avg >= 0.2 else "low"

        return {
            "consistency_score": avg,
            "supporting_sources": supporting,
            "contradicting_sources": [],
            "confidence": confidence,
        }

    def verify_batch(
        self,
        claims: List[str],
        evidence: List[Tuple[str, str]],
    ) -> List[Dict]:
        return [self.verify_claim(c, evidence) for c in claims]


_singleton: Optional[CrossVerifier] = None


def get_cross_verifier() -> CrossVerifier:
    global _singleton
    if _singleton is None:
        _singleton = CrossVerifier()
    return _singleton
