---
name: seven-day-campaign
description: 设计 7 天战役内容计划,包含 hook/deepdive/qa/ugc/summary/live/review 全套
triggers: 这周, 一周, 7天, 系列, 内容规划, 战役, campaign, 排期, 节奏
tags: planning, campaign, strategy
version: 1
---

# 7-Day Campaign Skill

## 适用场景
- 用户要规划一周内容
- 需要系列内容感
- 要平衡引流/信任/转化

## 工作流
1. 调用 `persona.embed` 获取人设
2. 调用 `oracle.scan` 找当前可用话题
3. 调用 `campaign.plan` 生成 7 天战役图
4. 对每天调用 `risk.score` 检查
5. 输出 CampaignTimeline 卡片

## 流量结构
默认: 引流 20% / 信任 50% / 转化 30%
可根据用户阶段调整 (千粉冷启动: 引流 40% / 信任 50% / 转化 10%)
