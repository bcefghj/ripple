---
name: oracle-early-signal
description: KOC 早期信号雷达 - 从 12 个数据源并行扫描"刚开始升温"的话题,在热搜出现前 7-14 天发现机会
when_to_use: 当 KOC 询问"接下来发什么内容"、"什么话题会火"、"有没有新趋势"等时
allowed_tools:
  - polymarket_search
  - kalshi_search
  - manifold_search
  - weibo_realtime
  - weixin_index
  - baidu_index
  - juliang_trend
  - xhs_inspiration
  - github_trending
  - hn_top
  - reddit_rising
  - x_trending
triggers:
  - 早期信号
  - 趋势预测
  - 选题灵感
  - 什么话题会火
  - 接下来发什么
context_fork: false
---

# Oracle Early Signal Skill

## 灵感来源

借鉴 [Digital Oracle](https://github.com/komako-workshop/digital-oracle) 的核心理念:
**"资本永远先于舆论。当一个人要把自己的钱押在某个结果上时,他会比发一条短视频认真很多。"**

把这个思想从金融领域迁移到 KOC 内容领域:
**真正的早期信号在搜索量、广告投放、预测市场,而不是已经爆的热搜。**

## 工作流程

### 第 1 步:理解问题
拆解 KOC 的需求:
- 赛道(美妆/数码/学习/生活/搞笑/本地)
- 平台(视频号/抖音/小红书/B站/公众号/微博)
- 时间窗口(7 天 / 14 天 / 30 天)
- 偏好(蓝海 vs 安全跟风)

### 第 2 步:选择 3+ 独立信号源
不同类别选不同信号:
- **预测市场**: Polymarket / Kalshi / Manifold (英语圈,适合跨域映射)
- **搜索趋势**: 微信指数 / 百度指数 / 巨量算数 (国内意图先行)
- **平台原生**: 微博实时 / 小红书灵感 / 抖音热点宝
- **海外先行**: HN / GitHub Trending / Reddit / X (科技/文化叙事)

### 第 3 步:并行拉取 (asyncio.gather)
所有数据源并行,容忍部分失败:
```python
results = await asyncio.gather(
    polymarket_search(query),
    weixin_index(query),
    weibo_realtime(query),
    juliang_trend(query),
    return_exceptions=True,
)
```

### 第 4 步:CUSUM 突变检测 + MAD-zscore 异常
对每个信号的时间序列:
```
z = (x - rolling_median) / (1.4826 * MAD)
delta_z = z[t] - z[t-1]
cusum = max(0, cusum_prev + (delta_z - kappa))
alarm = cusum > threshold
```
任何源的 alarm 触发,记为"该话题有信号"。

### 第 5 步:矛盾推理
找不同源之间的"分歧",并解释为什么可以同时正确:
- 微博讨论 +180% 但小红书搜索 +5% → 适合做"破圈解读"内容
- Polymarket 概率 65% 但国内热搜 0 → 跨文化预热,可做"国外都在讨论"切入
- 巨量算数 +120% 但小红书 -10% → 抖音先行,小红书有 3-5 天窗口期

### 第 6 步:输出结构化报告
```json
{
  "trends": [
    {
      "topic": "珂润润浸保湿洗颜泡沫",
      "category": "美妆",
      "confidence": 0.78,
      "horizon_days": 5,
      "evidence": [
        {"source": "weibo_realtime", "value": 1.8, "delta": 0.95},
        {"source": "xhs_search", "value": 2.1, "delta": 0.87},
        {"source": "polymarket", "value": 0.65, "delta": 0.32}
      ],
      "explanation": "微博讨论量 7 天内 +180%,小红书搜索量 +95%,Polymarket 美妆相关合约升温",
      "recommended_angle": "成分党测评 vs 玄学体验",
      "best_platforms": ["xhs", "channels"],
      "risks": ["该话题可能被品牌方快速覆盖,需 3-5 天内行动"]
    }
  ],
  "scan_metadata": {
    "sources_scanned": 12,
    "sources_succeeded": 10,
    "scan_time_ms": 2340
  }
}
```

## 关键原则

1. **保守置信度**: 不确定就标低置信度,宁肯错过也不要误导
2. **可解释性**: 每个预测都要标明依据(哪几个信号源)
3. **时效性**: 高优先级显示"窗口期 X 天"
4. **多源对冲**: 单一信号源永不输出"必爆"判断

## 失败模式

- 单一数据源单点故障 → 容忍,继续用其他源
- 所有数据源都没异常 → 诚实告知"目前没有强信号,建议跟踪现有热点"
- 数据源返回脏数据 → 过滤并记录日志

## 不要做的事

- 不要承诺"100% 会爆"
- 不要根据 1 个信号源就出结论
- 不要忽略平台合规约束(医疗/财经/政治)
- 不要在没有 alarm 时硬凑话题
