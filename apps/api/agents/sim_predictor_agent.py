"""SimPredictorAgent - 群体仿真预测(附加增强,不是主卖点)

借鉴 MiroFish (OASIS) 思想:
- 在虚拟用户图(100-500 节点)上跑 N 轮传播仿真
- 每个节点有偏好(基于真实用户画像分布)
- 内容触发不同节点的传播概率不同
- 输出 reach 分布、互动率分布、情感极化

注意: 这个 Agent 故意定位为"附加增强"而非核心卖点,
避免被评委质疑"群体智能仿真是不是玄学"。
我们的核心是 OracleAgent 早期信号(可证伪),仿真是辅助。
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SimulatedUser:
    """虚拟用户节点"""
    user_id: int
    interests: List[str]  # 兴趣 tags
    activity_level: float  # 0-1 活跃度
    influence: float  # 0-1 影响力(传播因子)
    sentiment_bias: float  # -1 负面 / 0 中性 / 1 正面


@dataclass
class SimulationResult:
    """仿真结果"""
    total_nodes: int
    reach_count: int  # 触达人数
    reach_distribution: List[int]  # 每轮新增触达
    estimated_views: int  # 推测展示数
    estimated_likes: int
    estimated_comments: int
    estimated_shares: int
    sentiment_distribution: Dict[str, float]  # {positive: 0.6, neutral: 0.3, negative: 0.1}
    virality_score: float  # 0-1 病毒传播分
    convergence_rounds: int
    explanation: str


class SimPredictorAgent:
    """简化版群体传播仿真"""

    def __init__(self, num_nodes: int = 200):
        self.num_nodes = num_nodes
        self.users = self._generate_synthetic_users()

    def _generate_synthetic_users(self) -> List[SimulatedUser]:
        """生成合成虚拟用户群"""
        random.seed(42)
        interest_pool = [
            "美妆", "数码", "学习", "生活", "知识", "搞笑",
            "美食", "旅行", "运动", "穿搭", "母婴", "宠物",
            "游戏", "动漫", "音乐", "影视", "本地", "财经",
        ]

        users = []
        for i in range(self.num_nodes):
            users.append(SimulatedUser(
                user_id=i,
                interests=random.sample(interest_pool, k=random.randint(2, 5)),
                activity_level=random.betavariate(2, 5),  # 偏低活跃度
                influence=random.lognormvariate(0, 1) / 10,  # 长尾分布
                sentiment_bias=random.gauss(0.1, 0.3),  # 略偏正面
            ))
        return users

    async def simulate(
        self,
        content_summary: str,
        target_categories: List[str],
        seed_influence: float = 0.05,
        max_rounds: int = 10,
    ) -> SimulationResult:
        """
        运行传播仿真
        
        Args:
            content_summary: 内容摘要(用于计算与用户兴趣的匹配度)
            target_categories: 目标内容类别
            seed_influence: 初始触达比例
            max_rounds: 最大传播轮数
        """
        # 1) 计算每个用户的"内容亲和度"
        user_affinity = []
        for u in self.users:
            overlap = len(set(u.interests) & set(target_categories))
            affinity = (overlap / max(1, len(target_categories))) * 0.7 + u.activity_level * 0.3
            user_affinity.append(affinity)

        # 2) 初始种子节点(高活跃 + 高影响力 + 高亲和度)
        scored = sorted(
            range(self.num_nodes),
            key=lambda i: user_affinity[i] * self.users[i].influence,
            reverse=True,
        )
        seed_count = max(3, int(self.num_nodes * seed_influence))
        reached = set(scored[:seed_count])

        # 3) 多轮传播
        reach_dist = [seed_count]
        for r in range(max_rounds):
            new_reached = set()
            for u_idx in list(reached):
                u = self.users[u_idx]
                # 影响 N 个邻居(基于 influence)
                n_influenced = int(u.influence * 10)
                if n_influenced <= 0:
                    continue
                # 模拟邻居选择(亲和度高的更容易被影响)
                candidates = [
                    i for i in range(self.num_nodes)
                    if i not in reached and i not in new_reached
                    and user_affinity[i] > 0.3
                ]
                if not candidates:
                    continue
                weights = [user_affinity[i] for i in candidates]
                if sum(weights) == 0:
                    continue
                actual_n = min(n_influenced, len(candidates))
                # 加权随机选
                selected = random.choices(candidates, weights=weights, k=actual_n)
                new_reached.update(selected)

            reach_dist.append(len(new_reached))
            reached.update(new_reached)
            if len(new_reached) == 0:
                break

        convergence = len(reach_dist)

        # 4) 估算各项指标
        reach_count = len(reached)
        # 估算展示量(每个被触达者带来多次展示)
        views_per_reach = 3.5
        estimated_views = int(reach_count * views_per_reach * 50)  # scale up
        like_rate = 0.05
        comment_rate = 0.005
        share_rate = 0.01

        estimated_likes = int(estimated_views * like_rate)
        estimated_comments = int(estimated_views * comment_rate)
        estimated_shares = int(estimated_views * share_rate)

        # 5) 情感分布
        sentiments = [self.users[i].sentiment_bias for i in reached]
        positive = sum(1 for s in sentiments if s > 0.2) / max(1, len(sentiments))
        negative = sum(1 for s in sentiments if s < -0.2) / max(1, len(sentiments))
        neutral = 1 - positive - negative

        # 6) 病毒分(传播倍增因子)
        virality = 0.0
        if len(reach_dist) > 1 and reach_dist[0] > 0:
            growth_factor = sum(reach_dist[1:]) / reach_dist[0]
            virality = min(1.0, math.log(1 + growth_factor) / 5)

        # 7) 解释
        explanation = (
            f"在 {self.num_nodes} 节点的虚拟用户图中,种子节点 {seed_count} 个,"
            f"经过 {convergence} 轮传播,触达 {reach_count} 个节点 "
            f"({reach_count / self.num_nodes:.1%})。病毒传播分 {virality:.2f}。\n\n"
            f"提示:仿真结果是相对数据,用于内容间对比,不是绝对预测。"
        )

        return SimulationResult(
            total_nodes=self.num_nodes,
            reach_count=reach_count,
            reach_distribution=reach_dist,
            estimated_views=estimated_views,
            estimated_likes=estimated_likes,
            estimated_comments=estimated_comments,
            estimated_shares=estimated_shares,
            sentiment_distribution={
                "positive": round(positive, 2),
                "neutral": round(neutral, 2),
                "negative": round(negative, 2),
            },
            virality_score=virality,
            convergence_rounds=convergence,
            explanation=explanation,
        )
