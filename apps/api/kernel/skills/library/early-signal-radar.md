---
name: early-signal-radar
description: 调用 Oracle 早期信号雷达,扫描 7 个真实数据源,识别跨平台时差和资本-舆论传导
triggers: 早期信号, 信号雷达, 提前发现, 还没火, 抢窗口, 跨平台时差, 资本流向, 趋势预测, oracle, 雷达
tags: discovery, oracle, signal
version: 1
---

# Early Signal Radar Skill

## 适用场景
当用户询问以下任何一种,触发本 Skill:
- "什么话题快火了?"
- "下一个爆款会是什么?"
- "我应该提前布局什么?"
- "有哪些刚开始升温的趋势?"

## 工作流
1. 调用 `oracle.scan` 工具并行扫描 7 数据源
2. 调用 `oracle.cross_platform_gap` 找跨平台时差
3. 调用 `oracle.cn_intl_gap` 找国内国际信息差
4. 对每个候选话题调用 `risk.score` 评估风险收益
5. 对 Top 3 话题调用 `trend.chain_predict` 预测因果链
6. 输出结构化报告卡片 (TopicPanel + RiskRewardCard + TrendChain)

## 输出
- 话题清单 (按 confidence 排序)
- 每个话题的窗口期、置信度、推荐角度
- 风险收益评分卡
- 因果链预测

## 引用要求
所有数据点必须带 [source: url, ts] 标注。
