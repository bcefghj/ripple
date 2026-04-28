"""CitationEnforcer - 引用强制层

机制:
1. LLM 生成时,system prompt 强制要求 [source: url, ts] 注释
2. 后处理用正则提取 citation
3. 没有 citation 的 claim 标记 unsupported
4. 输出 Citation 列表 + 标注的文本
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import List, Optional, Tuple

from ...types import Citation


CITATION_PAT = re.compile(
    r"\[source:\s*([^,\]]+)(?:,\s*([^,\]]+))?(?:,\s*ts=([^\]]+))?\]",
    flags=re.IGNORECASE,
)


CITATION_INJECTION_PROMPT = """
## 引用规范 (强制)

凡是含有具体数据/事实/外部论断的句子, 必须在末尾标注来源, 格式:
[source: <url 或来源标识>, <可选标题>, ts=<时间戳>]

例如:
- 黄金价格上周突破 4000 美元 [source: https://bloomberg.com/article/xxx, "金价突破历史", ts=2026-04-29]
- Polymarket 上某事件交易量超百万美元 [source: https://polymarket.com/event/xxx]

如无外部来源, 请以"主观判断" / "推测" 开头, 不能伪装为事实。
""".strip()


class CitationEnforcer:
    def inject_prompt(self, base_prompt: str) -> str:
        """在 system prompt 末尾注入引用规范"""
        return f"{base_prompt}\n\n{CITATION_INJECTION_PROMPT}"

    def extract(self, text: str) -> List[Citation]:
        """从 LLM 输出中提取 citation"""
        result: List[Citation] = []
        for match in CITATION_PAT.finditer(text):
            url = (match.group(1) or "").strip().strip("\"'")
            title = (match.group(2) or "").strip().strip("\"'")
            ts = (match.group(3) or "").strip()
            try:
                retrieved_at = datetime.fromisoformat(ts) if ts else datetime.utcnow()
            except Exception:
                retrieved_at = datetime.utcnow()
            result.append(Citation(
                url=url, title=title,
                source_type="llm_inference" if not url.startswith("http") else "knowledge_base",
                retrieved_at=retrieved_at,
                snippet=match.group(0),
            ))
        return result

    def detect_unsupported_claims(self, text: str) -> List[str]:
        """简单启发式: 含数字 + 没有引用的句子"""
        sentences = re.split(r"[。！？\n]+", text)
        bad: List[str] = []
        for s in sentences:
            if re.search(r"\d+", s) and "source:" not in s.lower() and "推测" not in s and "主观" not in s:
                if any(kw in s for kw in ["%", "倍", "万", "亿", "美元", "元", "排名", "第"]):
                    bad.append(s.strip()[:120])
        return bad

    def annotate(self, text: str) -> Tuple[str, List[Citation], List[str]]:
        """返回 (原文本, citations, unsupported_claims)"""
        cites = self.extract(text)
        unsupported = self.detect_unsupported_claims(text)
        return text, cites, unsupported


_singleton: Optional[CitationEnforcer] = None


def get_enforcer() -> CitationEnforcer:
    global _singleton
    if _singleton is None:
        _singleton = CitationEnforcer()
    return _singleton
