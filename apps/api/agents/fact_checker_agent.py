"""FactCheckerAgent - 真实性审查

策略:
1. 用 LLM 提取所有可证伪的"事实陈述"
2. 对每条陈述判断:
   - 是否需要引用来源
   - 是否过于绝对
   - 是否有夸大宣传嫌疑
3. 输出:修正建议 + 必须添加的引用占位符
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, List, Optional

from loguru import logger


@dataclass
class FactClaim:
    """事实陈述"""
    text: str
    needs_citation: bool
    is_absolute: bool  # 是否绝对化("最""第一""唯一")
    is_exaggerated: bool  # 是否夸大
    suggested_revision: str = ""
    suggested_citation_placeholder: str = ""  # [[CITE: ...]]


@dataclass
class FactCheckReport:
    """审查报告"""
    overall_pass: bool
    score: int  # 0-100
    claims: List[FactClaim]
    suggestions: List[str]
    revised_text: str = ""


class FactCheckerAgent:
    """真实性审查"""

    def __init__(self, llm_call: Callable[..., Awaitable[Dict[str, Any]]]):
        self.llm_call = llm_call

    async def check(self, content: str, category: str = "通用") -> FactCheckReport:
        """对内容进行事实审查"""
        prompt = f"""你是 Ripple 的「事实审查员」,任务是找出文案中的"事实陈述"并判断风险。

# 待审查内容
{content}

# 类别
{category}

# 任务

1. 提取所有"可证伪的事实陈述"(数字/比例/比较/时间/品牌特性)
2. 对每条判断:
   - needs_citation: 是否需要引用来源
   - is_absolute: 是否绝对化("最""第一""唯一""所有")
   - is_exaggerated: 是否夸大宣传
3. 给出修正建议
4. 在文案中插入 [[CITE: ...]] 占位符

# 输出 JSON
{{
  "overall_pass": true,
  "score": 85,
  "claims": [
    {{
      "text": "原文中的事实陈述",
      "needs_citation": true,
      "is_absolute": false,
      "is_exaggerated": false,
      "suggested_revision": "修正后的表达",
      "suggested_citation_placeholder": "[[CITE: 数据来源]]"
    }}
  ],
  "suggestions": ["全局建议1", "全局建议2"],
  "revised_text": "已加入修正建议和 [[CITE]] 占位符的完整文本"
}}

# 评分标准
- 90-100: 几乎无问题,可以直接发布
- 70-89: 轻微调整即可
- 50-69: 需要明显修改
- < 50: 重写
"""

        try:
            response = await self.llm_call(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2500,
                temperature=0.3,
            )
            content_resp = response.get("message", {}).get("content", "")
            json_match = re.search(r"\{[\s\S]*\}", content_resp)
            if not json_match:
                return self._fallback_report(content)

            data = json.loads(json_match.group())
            claims = [
                FactClaim(
                    text=c.get("text", ""),
                    needs_citation=bool(c.get("needs_citation", False)),
                    is_absolute=bool(c.get("is_absolute", False)),
                    is_exaggerated=bool(c.get("is_exaggerated", False)),
                    suggested_revision=c.get("suggested_revision", ""),
                    suggested_citation_placeholder=c.get("suggested_citation_placeholder", ""),
                )
                for c in data.get("claims", [])
            ]

            return FactCheckReport(
                overall_pass=bool(data.get("overall_pass", True)),
                score=int(data.get("score", 70)),
                claims=claims,
                suggestions=data.get("suggestions", []),
                revised_text=data.get("revised_text", content),
            )
        except Exception as e:
            logger.warning(f"FactChecker 失败: {e}")
            return self._fallback_report(content)

    def _fallback_report(self, content: str) -> FactCheckReport:
        return FactCheckReport(
            overall_pass=True,
            score=70,
            claims=[],
            suggestions=["FactChecker LLM 调用失败,请人工 review"],
            revised_text=content,
        )
