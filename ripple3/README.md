# Ripple 6.0 — KOC 决策智能平台

> **腾讯 PCG 校园 AI 产品创意大赛 · 赛道5：AI + 社媒流量增长，连接 KOC 成长**

Ripple 是一款 KOC 决策智能平台，通过 **9层搜索矩阵** 聚合全网实时数据，结合 **多Agent辩论**、**CES爆款预测** 和 **内容DNA分析** 等能力，帮助 KOC 完成从选题到创作的全流程决策。

## 核心创新（区别于 ChatGPT/Gemini）

### 1. 9层搜索矩阵 — 1000+ 条实时数据
不是简单的"搜索+总结"，而是 15 个引擎并行扇出：
- **Layer 0 MiniMax联网搜索**：Token Plan 450次/日免费，实时性最强
- **LLM联网搜索**：腾讯混元/阿里千问原生搜索增强
- **搜索API**：Serper/Tavily/Exa/You.com/Brave
- **免费搜索库**：百度搜索/Google搜索/DuckDuckGo
- **平台直连**：微博/B站/知乎/百度热搜 Web API
- **热搜聚合**：40+ 平台实时热榜 (DailyHotApi)
- **元搜索**：SearXNG 70+ 引擎聚合
- **Jina AI**：搜索 + 全文提取

### 2. CES 爆款预测评分
- 小红书官方 CES 公式内置: `关注*8 + 评论*4 + 转发*4 + 收藏*1 + 点赞*1`
- 19维100分评分体系（标题吸引力/情绪共鸣/平台适配/竞争蓝海...）
- 流量池阶梯预测: 冷启动池 → 初级池 → 热门池

### 3. 多Agent辩论 — 贯穿所有功能
- **探索领域**：数据分析师 + 内容策划师 + 平台专家 三方讨论
- **评估选题**：7位AI专家 + 仲裁者 两轮辩论
- **创作内容**：路人评审团模拟真实反应
- **风格蒸馏**：语言学家 + 心理学家 协作解构

### 4. 内容DNA分析 + A/B标题模拟
结构化提取爆款基因，用5种用户画像模拟点击行为。

### 5. 自改进反射循环
- 搜索反射: 相关性不足 → 自动重写查询 → 重搜
- 搜索质量自测: 4维度评分，不达标自动重试

## 技术架构

```
用户输入 → 智能意图引擎 (自动引导 + 流式衔接)
              ↓
    话题分解引擎 → 30+ 精准子查询
              ↓
    ┌──────────────────────────────────────────┐
    │ 9层搜索矩阵 (并行, Semaphore=30)          │
    │ MiniMax | 混元 | Tavily | Exa | Serper   │
    │ DDG | 百度 | DailyHot | 社交平台API        │
    └──────────────────────────────────────────┘
              ↓
    相关性双重过滤 (关键词 + LLM分类) → >80%相关
              ↓
    搜索质量自测 (4维度) → 不达标自动重搜
              ↓
    ┌──────────────────────────────────────────┐
    │ 5+1 Agent 2轮辩论                         │
    │ 数据分析师 | 内容策划师 | 平台专家          │
    │ 用户画像师 | 趋势研究员 | 仲裁者            │
    └──────────────────────────────────────────┘
              ↓
    CES 爆款评分 + 反射循环自改进
              ↓
    流式 SSE → React 前端 (Token可视化 + 爆款评分面板)
```

## 快速开始

### 环境要求
- Python 3.10+
- Node.js 18+

### 安装

```bash
cd ripple3

# 后端依赖
pip install -r requirements.txt

# 前端依赖
cd web && npm install && cd ..

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入 MINIMAX_API_KEY（必需）
```

### 运行

```bash
# 启动后端
python -m uvicorn api.main:app --reload --port 8001

# 启动前端（新终端）
cd web && npm run dev

# 访问 http://localhost:5173
```

### 测试搜索

```bash
# 快速测试（含 MiniMax 搜索验证）
python test_search.py --quick

# 完整测试（包含所有引擎）
python test_search.py

# 端到端测试（意图分类 + 搜索管线 + API模拟）
python test_e2e.py
```

## 功能模块

| 功能 | 说明 | 创新点 | 输入示例 |
|------|------|--------|----------|
| **领域雷达** | 分析内容生态 + 知识图谱 + 内容DNA | 多Agent讨论 + DNA分析 | "帮我分析美食探店这个领域" |
| **选题灵感** | AI 生成 10-15 个创意选题 | 创意人 vs 风控人 对抗 | "帮我想10个职场效率类选题" |
| **爆款预测** | 7位AI专家辩论 + CES 19维评分 | 两轮辩论 + 流量池预测 | "评估这个选题的爆款潜力" |
| **内容创作** | 完整内容包 + 多平台版本 | A/B标题模拟 + 路人评审 | "帮我写一篇小红书笔记" |
| **风格蒸馏** | 五层认知蒸馏方法论 | 语言学家+心理学家 协作 | "分析一下影视飓风的创作风格" |
| **热搜仪表盘** | 全网热搜趋势图表 | 40+ 平台实时数据 | 点击右上角图表按钮 |

## 项目结构

```
ripple3/
├── api/               # FastAPI 后端
│   ├── routes.py      # SSE 流式端点 + 统一聊天
│   └── sse.py         # SSE 事件格式化
├── web/src/           # React 前端
│   ├── components/    # UI组件 (图谱/评分/Agent面板等)
│   ├── hooks/         # 状态管理
│   └── lib/           # API 客户端
├── adapters/          # 搜索适配器（9层15引擎）
│   ├── search.py      # 并行扇出协调器
│   ├── minimax_search.py  # MiniMax Coding Plan 搜索
│   ├── query_builder.py   # 4层查询策略生成器
│   └── ...            # 其他引擎适配器
├── engines/           # 功能引擎
│   ├── topic_decomposer.py  # 话题分解
│   ├── multi_agent.py       # 多Agent辩论
│   ├── viral_scorer.py      # CES爆款评分
│   ├── relevance_filter.py  # 相关性过滤
│   ├── search_validator.py  # 搜索质量验证
│   ├── reflection.py        # 自改进反射循环
│   ├── content_dna.py       # 内容DNA分析
│   └── title_ab_test.py     # A/B标题模拟
├── core/              # 核心模块
│   ├── config.py      # 配置管理
│   ├── llm.py         # LLM 网关 (MiniMax/MiMo)
│   ├── intent.py      # 意图识别
│   └── store.py       # 数据存储
├── test_search.py     # 搜索系统测试
├── test_e2e.py        # 端到端测试
├── requirements.txt   # Python 依赖
└── .env.example       # 环境变量模板
```

## License

MIT
