"""TrendScoutAgent - 已爆热点扫描

辅助角色: 不是主卖点(主卖点是 OracleAgent 的早期信号),
但作为对照组,告诉 KOC「现在哪些已经在火」用于参考或避开红海。
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from loguru import logger


@dataclass
class HotTopic:
    """已爆热点"""
    topic: str
    platform: str
    rank: int
    metric_value: float  # 阅读量/讨论数
    age_hours: float  # 已经火多久了
    saturation: float  # 0-1,饱和度(数据来自模拟)
    is_red_ocean: bool  # 是否已是红海


class TrendScoutAgent:
    """已爆热点扫描"""

    async def scan_current_hot(
        self,
        category: Optional[str] = None,
        platforms: Optional[List[str]] = None,
    ) -> List[HotTopic]:
        """扫描当前已爆热点
        
        生产实现需要:
        - 微博热搜爬取(合规第三方 API)
        - 抖音热点宝
        - 小红书热搜
        - B 站排行榜
        - 知乎热榜
        
        当前为演示数据
        """
        platforms = platforms or ["weibo", "xhs", "douyin", "bilibili"]
        await asyncio.sleep(0.5)  # 模拟网络延迟

        # 演示数据
        return [
            HotTopic(
                topic="某明星离婚",
                platform="weibo",
                rank=1,
                metric_value=15_000_000,
                age_hours=18,
                saturation=0.95,
                is_red_ocean=True,
            ),
            HotTopic(
                topic="冬季敏感肌护理大全",
                platform="xhs",
                rank=3,
                metric_value=2_300_000,
                age_hours=72,
                saturation=0.7,
                is_red_ocean=True,
            ),
            HotTopic(
                topic="2026 春招避雷指南",
                platform="bilibili",
                rank=8,
                metric_value=420_000,
                age_hours=48,
                saturation=0.5,
                is_red_ocean=False,
            ),
        ]

    async def is_topic_red_ocean(self, topic: str) -> Dict[str, Any]:
        """判断某话题是否已是红海"""
        # 简化:模糊匹配已爆话题
        all_hot = await self.scan_current_hot()
        for h in all_hot:
            if topic.lower() in h.topic.lower() or h.topic.lower() in topic.lower():
                return {
                    "is_red_ocean": h.is_red_ocean,
                    "saturation": h.saturation,
                    "age_hours": h.age_hours,
                    "warning": "该话题已饱和,跟风风险高" if h.is_red_ocean else "",
                }
        return {
            "is_red_ocean": False,
            "saturation": 0.0,
            "age_hours": 0,
            "warning": "未在已爆热点中检测到该话题(可能是早期信号)",
        }
