---
name: persona-aware-writing
description: 基于用户人设向量约束生成内容,保证风格一致性,自动检测漂移
triggers: 写文案, 帮我写, 生成内容, 多版本, 帮我发, 文案, 草稿
tags: generation, persona, writing
version: 1
---

# Persona-Aware Writing Skill

## 适用场景
- 用户要写新内容
- 需要保持人设一致性
- 跨平台改写

## 工作流
1. 调用 `persona.embed` 取出当前人设向量
2. 用 `persona.style_constraint` 生成风格约束 prompt
3. 调用 `script.generate` 生成 3 个版本草稿
4. 调用 `sim.predict` 对 3 版进行虚拟受众赛马
5. 选最优版本进入 `critique.loop` 自我批评闭环
6. 调用 `persona.drift_check` 验证最终稿不偏离
7. 输出最终版本 + 引用 + Drift 报告

## 输出
- 3 版草稿 (可视化 Compare)
- SimPredictor 评分 (各 cohort)
- 最终选定版本
- 修订过程 (Replay 中)
