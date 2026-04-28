"""CampaignPlanner - 7 天战役图

约束:
- 流量结构 (引流 / 信任 / 转化 比例,默认 0.2/0.5/0.3)
- 拍摄时间窗 (用户每天可投入小时数)
- 内容依赖 (Day3 问答需 Day1 内容铺垫)
- 1 天预留给热点插入

简易求解: 贪心调度 + LLM 起草初稿
"""

from __future__ import annotations

import json
from typing import List, Optional
from uuid import uuid4

from ...types import Campaign, CampaignDay
from ...cognition.llm import quick_chat


DEFAULT_FLOW_STRUCTURE = {"acquire": 0.2, "trust": 0.5, "convert": 0.3}


CAMPAIGN_TEMPLATE = [
    ("hook", "短视频钩子", "完播率 / 转发"),
    ("deepdive", "深度图文", "收藏 / 阅读时长"),
    ("qa", "评论区问答专题", "评论数 / 互动率"),
    ("ugc", "UGC 征集互动", "投稿数 / UGC 互动"),
    ("summary", "盘点合集", "收藏 / 转发"),
    ("live_pre", "直播预告", "预约人数"),
    ("review", "复盘 + 下周预告", "粉丝粘性 / 留存"),
]


class CampaignPlanner:
    async def plan(
        self,
        user_id: str,
        theme: str,
        duration_days: int = 7,
        flow_structure: Optional[dict] = None,
        available_hours_per_day: float = 2.0,
        platform: str = "xhs",
        notes: str = "",
    ) -> Campaign:
        flow = flow_structure or dict(DEFAULT_FLOW_STRUCTURE)

        sys = (
            "你是 KOC 内容运营总监。给定主题与流量结构约束,设计 7 天战役计划。\n"
            "约束:\n"
            "- 7 天必须包含: 钩子(hook)/深度(deepdive)/问答(qa)/UGC 互动(ugc)/盘点(summary)/直播预告(live_pre)/复盘(review)\n"
            "- 至少 1 天预留给突发热点 (role=hotspot_buffer)\n"
            "- 流量结构按比例: 引流(acquire)/信任(trust)/转化(convert)\n"
            "- 必要的依赖: qa 依赖 hook + deepdive\n"
            "输出严格 JSON: { days: [ { day_index, role, topic, platform, content_type, expected_kpi, dependencies (list of int), estimated_effort_hours } ] }"
        )
        user = (
            f"主题: {theme}\n"
            f"持续天数: {duration_days}\n"
            f"流量结构 (acquire/trust/convert): {json.dumps(flow)}\n"
            f"用户每日可投入小时数: {available_hours_per_day}\n"
            f"主平台: {platform}\n"
            f"补充: {notes}"
        )

        try:
            text = await quick_chat(sys, user, json_mode=True, max_tokens=2000, temperature=0.5)
            data = json.loads(text)
            days_raw = data.get("days", [])
            days = []
            for d in days_raw[:duration_days]:
                role = d.get("role", "deepdive")
                if role not in {"hook", "deepdive", "qa", "ugc", "summary", "live_pre", "review", "hotspot_buffer"}:
                    role = "deepdive"
                days.append(CampaignDay(
                    day_index=int(d.get("day_index", 1)),
                    role=role,
                    topic=d.get("topic", "未命名")[:200],
                    platform=d.get("platform", platform),
                    content_type=d.get("content_type", "图文"),
                    expected_kpi=d.get("expected_kpi", "")[:100],
                    dependencies=[int(x) for x in d.get("dependencies", [])][:5],
                    estimated_effort_hours=float(d.get("estimated_effort_hours", 1.5)),
                ))
        except Exception:
            days = self._fallback_plan(theme, duration_days, platform, available_hours_per_day)

        return Campaign(
            user_id=user_id,
            theme=theme,
            days=days[:duration_days],
            flow_structure=flow,
        )

    def _fallback_plan(
        self, theme: str, duration_days: int, platform: str, hours_per_day: float
    ) -> List[CampaignDay]:
        days = []
        template = list(CAMPAIGN_TEMPLATE[: duration_days - 1])
        template.append(("hotspot_buffer", "热点缓冲日", "灵活"))
        for i, (role, ctype, kpi) in enumerate(template[:duration_days]):
            days.append(CampaignDay(
                day_index=i + 1,
                role=role,
                topic=f"{theme} - Day {i+1}",
                platform=platform,
                content_type=ctype,
                expected_kpi=kpi,
                dependencies=[1] if role == "qa" else [],
                estimated_effort_hours=min(hours_per_day, 2.0),
            ))
        return days


_singleton: Optional[CampaignPlanner] = None


def get_campaign_planner() -> CampaignPlanner:
    global _singleton
    if _singleton is None:
        _singleton = CampaignPlanner()
    return _singleton
