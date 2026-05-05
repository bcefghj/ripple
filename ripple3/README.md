# Ripple 6.0 — 开发指南

> `ripple3/` 是 Ripple 项目的 **唯一活跃代码目录**。以下是本地开发所需的全部信息。

---

## 环境要求

- Python >= 3.10
- Node.js >= 18
- 至少一个 LLM API Key（MiniMax 或小米 MiMo）

---

## 安装

```bash
# 后端依赖
pip install -r requirements.txt

# 前端依赖
cd web && npm install && cd ..

# 环境变量
cp .env.example .env
```

编辑 `.env`，至少配置以下必需项之一：

```bash
# 方案 A: 小米 MiMo（推荐，额度充足）
XIAOMI_API_KEY=tp-xxxxxxxx
XIAOMI_API_BASE=https://token-plan-cn.xiaomimomo.com/v1
XIAOMI_MODEL=mimo-v2.5-pro

# 方案 B: MiniMax（内置联网搜索）
MINIMAX_API_KEY=sk-xxxxxxxx
```

完整环境变量说明见 [.env.example](.env.example)。

---

## 运行

### 后端 (FastAPI)

```bash
# 开发模式（热重载）
python -m uvicorn api.main:app --reload --port 8001

# 或通过 CLI 入口
python run.py serve
```

### 前端 (React + Vite)

```bash
cd web
npm run dev
# → http://localhost:5173
```

### 生产构建

```bash
cd web && npm run build && cd ..
# 前端构建产物在 web/dist/，FastAPI 会自动提供静态文件
python -m uvicorn api.main:app --host 0.0.0.0 --port 80
```

---

## 测试

```bash
# 快速搜索测试（仅 MiniMax 搜索验证）
python test_search.py --quick

# 完整搜索测试（所有引擎逐一验证）
python test_search.py

# 端到端测试（意图分类 + 搜索管线 + API 模拟）
python test_e2e.py

# 搜索质量测试
python -m pytest tests/test_search_quality.py -v
```

---

## API 端点

基础路径：`/api`

### 核心

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/health` | 健康检查 |
| `POST` | `/api/chat` | 统一聊天入口（SSE 流式响应） |
| `POST` | `/api/graph/expand` | 知识图谱节点展开 |

### 对话管理

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/conversations` | 获取对话列表（最近 30 条） |
| `GET` | `/api/conversations/{id}` | 获取单个对话详情 |
| `DELETE` | `/api/conversations/{id}` | 删除对话 |

### 用户记忆

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/memory` | 获取用户偏好和记忆 |
| `POST` | `/api/memory` | 更新用户偏好 |

### 数据

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/trends` | 获取全网热搜趋势 |

### `/api/chat` 请求格式

```json
{
  "message": "帮我分析美食探店这个领域",
  "history": [
    {"role": "user", "content": "你好"},
    {"role": "assistant", "content": "你好！我是 Ripple..."}
  ],
  "session": {"domain": "美食探店"},
  "conversation_id": "optional-uuid"
}
```

响应为 SSE（Server-Sent Events）流，事件类型包括：

| 事件 | 说明 |
|------|------|
| `thinking` | AI 思考过程（搜索进度、Agent 状态） |
| `content` | 正文内容（流式 token） |
| `graph` | 知识图谱数据（节点 + 边） |
| `sources` | 引用来源列表 |
| `viral_score` | CES 爆款评分数据 |
| `agent_start` / `agent_speak` | Agent 辩论过程 |
| `search_stats` | 搜索引擎统计 |
| `wechat_strategy` | 微信生态策略 |
| `koc_growth` | KOC 成长规划 |
| `done` | 流结束信号 |

---

## 目录结构

```
ripple3/
├── api/                    # FastAPI 后端
│   ├── main.py             # 应用入口 + 静态文件挂载
│   ├── routes.py           # SSE 流式端点 + 统一聊天路由
│   └── sse.py              # SSE 事件格式化工具
│
├── core/                   # 核心模块
│   ├── config.py           # 配置管理（环境变量加载）
│   ├── llm.py              # LLM 网关（MiniMax / MiMo / 通用 OpenAI 兼容）
│   ├── intent.py           # 意图识别引擎（6 类意图分类）
│   ├── store.py            # 数据存储（SQLite, 对话 + 记忆）
│   ├── citations.py        # 引用来源管理
│   └── image_gen.py        # 图片生成（MiniMax Image API）
│
├── engines/                # AI 功能引擎
│   ├── multi_agent.py      # 7 位 AI 专家辩论系统
│   ├── viral_scorer.py     # CES 19维爆款评分
│   ├── viral_predictor.py  # 流量池阶梯预测
│   ├── graph_builder.py    # 知识图谱构建
│   ├── topic_decomposer.py # 话题分解（→30+ 子查询）
│   ├── relevance_filter.py # 相关性双重过滤
│   ├── search_validator.py # 搜索质量自测（4 维度）
│   ├── reflection.py       # 自改进反射循环
│   ├── content_create.py   # 内容创作引擎
│   ├── content_dna.py      # 内容 DNA 分析
│   ├── title_ab_test.py    # A/B 标题模拟测试
│   ├── style_distill.py    # 风格蒸馏
│   └── idea_engine.py      # 选题灵感引擎
│
├── adapters/               # 9 层搜索矩阵适配器
│   ├── search.py           # 并行扇出协调器
│   ├── query_builder.py    # 4 层查询策略生成器
│   ├── minimax_search.py   # L0: MiniMax 联网搜索
│   ├── hunyuan_search.py   # L1: 腾讯混元搜索
│   ├── qwen_search.py      # L1: 阿里千问搜索
│   ├── tavily_adapter.py   # L2: Tavily AI 搜索
│   ├── exa_adapter.py      # L2: Exa 语义搜索
│   ├── serper_adapter.py   # L2: Serper (Google SERP)
│   ├── brave_adapter.py    # L2: Brave Search
│   ├── you_adapter.py      # L2: You.com
│   ├── ddgs_adapter.py     # L3: DuckDuckGo
│   ├── baidu_adapter.py    # L3: 百度搜索
│   ├── google_adapter.py   # L3: Google 搜索
│   ├── platform_apis.py    # L4: 社交平台直连
│   ├── dailyhot_adapter.py # L5: 热搜聚合
│   ├── hot_trends.py       # L5: 热搜数据处理
│   ├── searxng_adapter.py  # L6: SearXNG 元搜索
│   └── jina_adapter.py     # L7: Jina AI 搜索 + Reader
│
├── web/                    # React 19 前端
│   ├── src/
│   │   ├── components/     # UI 组件
│   │   │   ├── KnowledgeGraph3D.tsx   # 3D 知识图谱
│   │   │   ├── SearchRadar.tsx        # 搜索雷达动画
│   │   │   ├── MultiAgentPanel.tsx    # Agent 辩论面板
│   │   │   ├── ViralScorePanel.tsx    # 爆款评分仪表盘
│   │   │   ├── WeChatEcosystemPanel.tsx # 微信生态面板
│   │   │   ├── KOCGrowthDashboard.tsx # KOC 成长仪表盘
│   │   │   └── ...
│   │   ├── hooks/          # 状态管理
│   │   └── lib/            # API 客户端
│   └── package.json
│
├── cli/                    # CLI 命令行入口
│   └── main.py             # Typer CLI (run.py 调用)
│
├── tests/                  # 测试
│   └── test_search_quality.py
├── test_search.py          # 搜索系统测试
├── test_e2e.py             # 端到端测试
├── run.py                  # 入口脚本
├── requirements.txt        # Python 依赖
├── .env.example            # 环境变量模板（带详细注释）
└── ripple.command           # macOS 双击启动脚本
```

---

## 环境变量速查

| 变量 | 必需 | 说明 |
|------|------|------|
| `XIAOMI_API_KEY` | 二选一 | 小米 MiMo API Key |
| `MINIMAX_API_KEY` | 二选一 | MiniMax API Key（内置联网搜索） |
| `SERPER_API_KEY` | 可选 | Google SERP 搜索（免费 2500 次/月） |
| `TAVILY_API_KEY` | 可选 | AI 优化搜索（免费 1000 次/月） |
| `EXA_API_KEY` | 可选 | 语义搜索（$10 免费额度） |
| `BRAVE_API_KEY` | 可选 | Brave 搜索（$5 免费额度） |
| `YOU_API_KEY` | 可选 | You.com 搜索（$100 免费额度） |
| `JINA_API_KEY` | 可选 | Jina AI（10M tokens/月免费） |

配置的搜索引擎越多，9 层搜索矩阵覆盖越广，分析质量越高。不配置则自动降级到免费引擎（DuckDuckGo + 百度 + DailyHot）。
