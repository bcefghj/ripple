"""RiskReviewerAgent - 合规审查

按照中国法规与平台政策审查:
- 《AI 生成合成内容标识办法》(2025-09-01 施行)
- 《互联网信息服务深度合成管理规定》
- 《个人信息保护法》
- 微信视频号 / 公众号运营规范
- 抖音 / 小红书 / B 站社区规范

风险类别:
- 政治宗教暴力
- 医疗承诺
- 财经投资建议
- 虚假宣传
- 未成年人保护
- 版权风险
- AI 标识缺失
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, List, Optional

from loguru import logger


# ============================================================
# 关键词规则库
# ============================================================

POLITICAL_KEYWORDS = ["政府", "中央", "国家领导", "敏感事件"]
MEDICAL_KEYWORDS = ["治愈", "根治", "保证有效", "治病", "治疗", "替代医生", "处方"]
FINANCIAL_KEYWORDS = ["保证收益", "稳赚", "无风险", "翻倍", "100%", "暴富"]
ABSOLUTE_KEYWORDS = ["最", "第一", "唯一", "100%", "绝对", "永远", "完美", "顶级"]
COPYRIGHT_TRIGGERS = ["搬运", "抄袭", "扒"]


@dataclass
class RiskItem:
    """单条风险"""
    category: str  # political/medical/financial/exaggeration/copyright/ai_label/...
    severity: str  # low / medium / high / critical
    matched_text: str
    explanation: str
    suggested_fix: str = ""


@dataclass
class ComplianceReport:
    """合规审查报告"""
    overall_pass: bool
    risks: List[RiskItem] = field(default_factory=list)
    ai_label_required: bool = True
    ai_label_text: str = "本内容由 AI 辅助创作"
    severity_summary: Dict[str, int] = field(default_factory=dict)
    revised_text: str = ""
    must_add_disclaimers: List[str] = field(default_factory=list)


class RiskReviewerAgent:
    """合规审查"""

    def __init__(self, llm_call: Optional[Callable[..., Awaitable[Dict[str, Any]]]] = None):
        self.llm_call = llm_call  # 可选,用于深度审查

    async def review(
        self,
        content: str,
        category: str = "通用",
        platform: str = "channels",
        is_ai_generated: bool = True,
    ) -> ComplianceReport:
        """完整合规审查"""

        # 1) 关键词扫描(快速)
        keyword_risks = self._keyword_scan(content)

        # 2) LLM 深度审查(可选)
        llm_risks = []
        if self.llm_call:
            try:
                llm_risks = await self._llm_review(content, category, platform)
            except Exception as e:
                logger.warning(f"LLM 合规审查失败: {e}")

        all_risks = keyword_risks + llm_risks

        # 3) AI 标识检查
        ai_label_required = is_ai_generated
        if ai_label_required and not self._has_ai_label(content):
            all_risks.append(RiskItem(
                category="ai_label_missing",
                severity="high",
                matched_text="(全文)",
                explanation="《AI 生成合成内容标识办法》要求 AI 生成内容显式标识",
                suggested_fix="在文末或开头添加: 「本内容由 AI 辅助创作」",
            ))

        # 4) 平台特定检查
        platform_risks = self._platform_specific_check(content, platform)
        all_risks.extend(platform_risks)

        # 5) 严重度统计
        severity_summary = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for r in all_risks:
            severity_summary[r.severity] = severity_summary.get(r.severity, 0) + 1

        # 6) 整体结论
        overall_pass = severity_summary["critical"] == 0 and severity_summary["high"] == 0

        # 7) 必须添加的免责声明
        disclaimers = []
        if any(r.category == "medical" for r in all_risks):
            disclaimers.append("本内容仅供参考,不构成医疗建议,请咨询专业医生")
        if any(r.category == "financial" for r in all_risks):
            disclaimers.append("本内容仅供参考,不构成投资建议")
        if ai_label_required:
            disclaimers.append("本内容由 AI 辅助创作")

        return ComplianceReport(
            overall_pass=overall_pass,
            risks=all_risks,
            ai_label_required=ai_label_required,
            severity_summary=severity_summary,
            revised_text=content,  # 实际可加自动修正
            must_add_disclaimers=disclaimers,
        )

    def _keyword_scan(self, content: str) -> List[RiskItem]:
        """关键词扫描"""
        risks = []
        for kw in MEDICAL_KEYWORDS:
            if kw in content:
                risks.append(RiskItem(
                    category="medical",
                    severity="high",
                    matched_text=kw,
                    explanation=f"含医疗承诺关键词「{kw}」,违反广告法",
                    suggested_fix=f"删除或替换为非承诺性表达,如「可能有助于」",
                ))
        for kw in FINANCIAL_KEYWORDS:
            if kw in content:
                risks.append(RiskItem(
                    category="financial",
                    severity="high",
                    matched_text=kw,
                    explanation=f"含财务承诺关键词「{kw}」,违反广告法/证券法",
                    suggested_fix=f"删除或加上「不构成投资建议」",
                ))
        for kw in ABSOLUTE_KEYWORDS:
            if kw in content:
                risks.append(RiskItem(
                    category="exaggeration",
                    severity="medium",
                    matched_text=kw,
                    explanation=f"含绝对化用语「{kw}」,违反广告法第九条",
                    suggested_fix=f"替换为「之一」「较好」「较优」等",
                ))
        for kw in POLITICAL_KEYWORDS:
            if kw in content:
                risks.append(RiskItem(
                    category="political",
                    severity="critical",
                    matched_text=kw,
                    explanation="涉及政治敏感词,需慎重",
                    suggested_fix="人工 review 后再决定",
                ))
        return risks

    def _has_ai_label(self, content: str) -> bool:
        """检查是否有 AI 标识"""
        labels = ["AI 生成", "AI辅助", "AI 创作", "人工智能生成", "本内容由 AI"]
        return any(l in content for l in labels)

    def _platform_specific_check(self, content: str, platform: str) -> List[RiskItem]:
        """平台特定规则"""
        risks = []
        if platform == "wechat" or platform == "channels":
            # 微信生态特别关注
            if "外链" in content or "http://" in content or "https://" in content:
                risks.append(RiskItem(
                    category="platform_rule",
                    severity="medium",
                    matched_text="外部链接",
                    explanation="微信生态对外链有限制,需走小程序或公众号文章",
                    suggested_fix="移除外链或改为微信内页",
                ))
        return risks

    async def _llm_review(
        self,
        content: str,
        category: str,
        platform: str,
    ) -> List[RiskItem]:
        """LLM 深度审查"""
        prompt = f"""你是 Ripple 的「合规审查员」,严格检查内容是否违反中国法规与平台政策。

# 待审查内容
{content}

# 类别
{category}

# 平台
{platform}

# 请检查以下风险类别:
1. 政治宗教 / 暴力恐怖
2. 医疗健康承诺
3. 财经投资建议
4. 虚假宣传 / 夸大效果
5. 未成年人保护
6. 版权 / 抄袭嫌疑
7. 隐私 / 敏感个人信息
8. 平台特定红线

# 输出 JSON
{{
  "risks": [
    {{
      "category": "...",
      "severity": "low|medium|high|critical",
      "matched_text": "原文中的相关片段",
      "explanation": "为什么是风险",
      "suggested_fix": "如何修正"
    }}
  ]
}}

如无风险,返回 {{"risks": []}}
"""
        try:
            response = await self.llm_call(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.2,
            )
            content_resp = response.get("message", {}).get("content", "")
            json_match = re.search(r"\{[\s\S]*\}", content_resp)
            if not json_match:
                return []
            data = json.loads(json_match.group())
            return [
                RiskItem(
                    category=r.get("category", "unknown"),
                    severity=r.get("severity", "low"),
                    matched_text=r.get("matched_text", ""),
                    explanation=r.get("explanation", ""),
                    suggested_fix=r.get("suggested_fix", ""),
                )
                for r in data.get("risks", [])
            ]
        except Exception as e:
            logger.warning(f"LLM 审查失败: {e}")
            return []
