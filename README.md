# Ripple — AI 深度研究引擎 for KOC 增长

> 腾讯 PCG 校园 AI 产品创意大赛 · 赛题5：AI + 社媒流量增长，连接 KOC 成长

<p align="center">
  <img src="https://img.shields.io/badge/React-19-blue?logo=react" />
  <img src="https://img.shields.io/badge/Three.js-3D-black?logo=three.js" />
  <img src="https://img.shields.io/badge/FastAPI-async-green?logo=fastapi" />
  <img src="https://img.shields.io/badge/腾讯混元-Powered-blue" />
  <img src="https://img.shields.io/badge/搜索引擎-15+-orange" />
</p>

## 产品定位

**一句话**：告诉 Ripple 你想做什么内容，它帮你深度分析全网数据、构建知识图谱、预测爆款潜力，输出可直接使用的内容方案。

**目标用户**：新手 KOC（关键意见消费者），在小红书/视频号/公众号刚起步，不知道做什么内容、怎么涨粉。

## 核心创新

| 创新点 | 说明 |
|--------|------|
| **深度研究引擎** | 不是简单问答，而是 AI 深度研究——自动规划搜索策略、迭代检索、交叉验证 |
| **实时思维链可视化** | React Flow 节点图实时展示 AI 的每一步思考和决策过程 |
| **3D 知识图谱** | 200+ 节点的 WebGL 力导向图谱，可交互探索内容生态 |
| **7 位 AI 专家圆桌** | 数据分析师、内容策划师、心理学家等多角色辩论，量化评分 |
| **微信生态深度策略** | 基于搜一搜 Peoplerank 算法和视频号推荐机制的具体可执行建议 |
| **腾讯技术栈** | 混元大模型 + 腾讯联网搜索 API + MCP 趋势聚合 |

## 技术架构

```
┌─────────────────────────────────────────────────────────────────┐
│                   Frontend (React 19 + Three.js)                  │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────┐  │
│  │ Galaxy 粒子背景│  │React Flow 思维│  │ 3D 知识图谱 + Bloom   │  │
│  │  (R3F Shader) │  │  链节点图     │  │  后处理 + 交互探索    │  │
│  └──────────────┘  └──────────────┘  └───────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                       SSE Streaming API                           │
├─────────────────────────────────────────────────────────────────┤
│                   Backend (FastAPI + Async)                       │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │            9 Layer Deep Search Matrix                      │   │
│  │  L0: MiniMax  L1: 腾讯混元/千问  L2: 腾讯联网搜索API     │   │
│  │  L3: Serper/Tavily/Exa  L4: Platform APIs  L5: DailyHot  │   │
│  │  L6: MCP趋势聚合(20+源)  L7: SearXNG  L8: Jina AI       │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌────────────────────┐  ┌────────────────────────────────────┐ │
│  │ Knowledge Graph     │  │  Multi-Agent Debate Engine         │ │
│  │ Builder (2-pass,    │  │  (7 Experts + Arbiter +            │ │
│  │  200-500 nodes)     │  │   Quantified Scoring)              │ │
│  └────────────────────┘  └────────────────────────────────────┘ │
│  ┌────────────────────┐  ┌────────────────────────────────────┐ │
│  │ WeChat Strategy     │  │  Content DNA + Viral Predictor     │ │
│  │ Engine (Peoplerank  │  │  (A/B Title Test + Hook Gen +      │ │
│  │  + 视频号推荐算法)   │  │   CES Score)                      │ │
│  └────────────────────┘  └────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## 快速启动

```bash
# 后端
cd ripple3
cp .env.example .env    # 填入 API Keys
pip install -r requirements.txt
python -m uvicorn api.main:app --reload --port 8001

# 前端
cd ripple3/web
npm install
npm run dev
```

访问 http://localhost:5173

## 项目结构

```
ripple3/
├── api/                    # FastAPI 路由 + SSE 流式接口
├── adapters/               # 搜索引擎适配器 (18 个)
│   ├── search.py           # 并行搜索协调器
│   ├── hunyuan_websearch.py # 腾讯联网搜索 API
│   ├── trend_aggregator.py # MCP 中文趋势聚合
│   ├── minimax_search.py   # MiniMax 联网搜索
│   └── ...                 # Serper/Tavily/Exa/DDG/百度/Google 等
├── engines/                # AI 引擎
│   ├── graph_builder.py    # 知识图谱构建 (2-pass, 200+ nodes)
│   ├── multi_agent.py      # 7 Agent 辩论引擎
│   ├── viral_scorer.py     # CES 爆款评分
│   ├── content_dna.py      # 内容基因分析
│   └── title_ab_test.py    # 标题 A/B 测试
├── core/                   # LLM 封装 + 意图识别 + 配置
├── web/                    # React 前端
│   └── src/
│       ├── components/     # 30+ 组件
│       │   ├── GalaxyBackground.tsx    # R3F Galaxy 粒子背景
│       │   ├── DeepResearchFlow.tsx    # React Flow 思维链
│       │   ├── AgentRoundtable.tsx     # Agent 圆桌动画
│       │   ├── KnowledgeGraph3D.tsx    # 3D 力导向图谱
│       │   └── HeroWelcome.tsx         # 首屏 Hero
│       ├── hooks/          # useChat (SSE) + useDarkMode
│       └── lib/            # API 客户端
└── .env.example            # 环境变量模板
```

## 赛题对齐

| 评分维度 | Ripple 的解决方案 |
|---------|-----------------|
| **赛道适配性** | 专注 KOC 涨粉，深度集成微信视频号/公众号/搜一搜策略，输出基于 Peoplerank 算法的优化建议 |
| **完整性** | 覆盖"选题→分析→创作→预测→发布策略"全链路，Demo 可完整体验 |
| **创新性** | 深度研究引擎 + React Flow 思维链 + 3D 图谱 + 7 Agent 辩论 + 量化评分 |
| **用户洞察** | 以"不知道做什么内容"的新手 KOC 为核心，对话即可获得完整方案 |
| **AI 原生性** | 全程 AI 驱动，透明展示搜索→推理→讨论→生成全过程，腾讯混元 + 联网搜索 |
| **落地可行性** | 可部署到腾讯元器/微信小程序，低 API 成本，MiniMax 免费额度充足 |

## License

本项目为腾讯 PCG 校园 AI 产品创意大赛参赛作品。
