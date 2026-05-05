# Ripple 6.0 技术架构文档

## 一、系统总览

Ripple 6.0 是一款面向 KOC（Key Opinion Consumer）的 AI 原生决策智能平台。核心目标是通过深度搜索 + 多 Agent 协作 + 3D 可视化，帮助社媒内容创作者完成从选题到创作的全流程智能决策。

### 技术栈

| 层级 | 技术选型 | 说明 |
|------|----------|------|
| 前端 | React 19 + Vite + TypeScript | SPA，SSE 流式渲染 |
| 3D 可视化 | Three.js + react-force-graph-3d | 知识图谱、粒子效果 |
| 动画 | Framer Motion + GSAP | 过渡动画、时间线 |
| UI | Tailwind CSS 4 | 响应式暗色主题 |
| 后端 | Python 3.10+ FastAPI | 异步 SSE 流 |
| LLM 调用 | 多模型网关 (MiniMax/混元/MiMo) | 按任务选模型 |
| 搜索 | 9 层并行矩阵 | 30+ 并发搜索 |
| 数据存储 | SQLite (aiosqlite) | 会话/记忆/偏好 |
| 部署 | Docker + Nginx | 阿里云 ECS |

---

## 二、核心引擎架构

### 2.1 意图路由 (Intent Router)

```
用户消息 → LLM快速分类 → 5种意图
                ↓ (fallback)
           关键词规则引擎
```

意图类型：
- `radar`: 领域分析（触发搜索+图谱+Agent）
- `idea`: 选题灵感（触发搜索+创意生成）
- `predict`: 爆款预测（触发CES评分）
- `create`: 内容创作（触发多平台适配）
- `distill`: 风格蒸馏（触发博主分析）
- `chat`: 通用对话

### 2.2 9层搜索矩阵

```
                    ┌─ L0: MiniMax联网搜索 ─┐
                    ├─ L1: 腾讯混元搜索增强 ─┤
                    ├─ L2: Tavily + Exa     ─┤
用户查询 → Topic   ├─ L3: Serper (Google)   ─┼→ 去重 → 相关性过滤 → 质量自测
  分解器    →      ├─ L4: DuckDuckGo        ─┤        (LLM分类)     (4维度)
           30+查询  ├─ L5: 百度搜索          ─┤
                    ├─ L6: SearXNG元搜索     ─┤
                    ├─ L7: 平台API           ─┤
                    └─ L8: DailyHot+Jina    ─┘
```

关键设计：
- **并行控制**: asyncio.Semaphore(30) 限制并发
- **错误隔离**: 单源失败不影响整体
- **话题分解**: 宽泛查询 → 4 层子话题树 → 30+ 精准搜索词
- **质量自测**: 相关性/多样性/时效性/深度 4 维度评分，不达标自动重搜

### 2.3 知识图谱构建

```
搜索结果集 → LLM实体抽取 → 节点+关系 → 验证+去重 → 3D可视化
                  ↓
         7种节点类型:
         person | topic | platform | format | audience | trend | strategy

         12种关系类型:
         创作于 | 擅长 | 讨论 | 适合 | 面向 | 热门于 |
         竞争 | 合作 | 衍生 | 引流至 | 适用策略 | 裂变通过
```

前端渲染：
- `react-force-graph-3d` 力导向布局
- Three.js 自定义节点几何体（每种类型不同形状）
- 星空粒子背景 + 星云效果
- 节点脉冲发光 + 轨道环装饰
- 连线粒子流（速度/颜色反映关系强度）
- 点击展开子图（调用 `/api/graph/expand`）

### 2.4 多 Agent 辩论引擎

```
搜索数据 → 7位专家并行分析 → 第1轮独立发言
                              → 第2轮交叉讨论
                              → 仲裁者综合研判 → 最终结论
```

Agent 配置：
| Agent | 角色 | 视角 |
|-------|------|------|
| 📊 数据分析师 | 数据驱动决策 | 流量数据/转化率 |
| 🎨 内容策划师 | 创意和内容质量 | 创意角度/信息密度 |
| 🧠 用户心理专家 | 用户行为洞察 | 动机/情绪/共鸣点 |
| ⚙️ 平台运营 | 平台机制+微信生态 | 算法/视频号/私域 |
| 🛡️ 风险评估师 | 合规和可持续性 | 风险/争议/时效 |
| 🔬 行业研究员 | 宏观趋势 | 竞争格局/天花板 |
| 👤 用户代言人 | 终端用户视角 | 实用性/易操作 |

### 2.5 CES 爆款评分

内置小红书 CES (Content Engagement Score) 算法：
```
CES = 关注*8 + 评论*4 + 转发*4 + 收藏*1 + 点赞*1
```

19 维度评分体系 + 流量池阶梯预测：
- 冷启动池 (200-500 曝光)
- 初级流量池 (1K-5K 曝光)
- 热门流量池 (1W-10W 曝光)
- 爆款池 (10W+ 曝光)

---

## 三、前端组件架构

```
App.tsx
├── RippleBackground (Canvas粒子背景)
├── Sidebar (会话管理)
├── WelcomeCards (首屏引导+热榜)
└── ChatMessage
    ├── ThinkingPanel (思考步骤)
    ├── SearchRadar (9层搜索雷达Canvas动画)
    ├── KnowledgeGraph3D (3D力导向图谱)
    ├── MultiAgentPanel (圆桌会议)
    ├── ScoreAnimation (评分动画)
    ├── ViralScorePanel (爆款仪表盘)
    ├── MarkdownRenderer (流式Markdown)
    ├── TokenUsagePanel (Token消耗)
    └── NextStepButtons (下一步建议)
```

### 数据流

```
用户输入 → POST /api/chat (SSE)
             ↓
        event: thinking → ThinkingPanel + SearchRadar
        event: search_stats → SearchRadar统计
        event: graph → KnowledgeGraph3D
        event: agent_speak → MultiAgentPanel
        event: viral_score → ViralScorePanel
        event: content → MarkdownRenderer
        event: done → NextStepButtons
```

---

## 四、部署架构

```
                Internet
                   ↓
              Nginx (反向代理)
             /          \
    /api/*             /*
       ↓                ↓
  Uvicorn (8000)    Static Files
  FastAPI App       (web/dist/)
       ↓
  External APIs
  (MiniMax/混元/搜索引擎)
```

Docker 部署：
```bash
docker-compose up -d
# 自动构建前端 + 启动后端
```

---

## 五、API 接口清单

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/health | 健康检查 |
| POST | /api/chat | 主对话流 (SSE) |
| POST | /api/graph/expand | 图谱节点展开 (SSE) |
| GET | /api/trends | 实时热榜 |
| GET | /api/conversations | 会话列表 |
| GET | /api/conversations/:id | 加载会话 |
| DELETE | /api/conversations/:id | 删除会话 |
| GET | /api/memory | 用户记忆 |
| POST | /api/memory | 更新记忆 |

---

## 六、与腾讯 PCG 赛道对齐

### 赛道要求回应

1. **KOC 痛点解决**: 定位难 → 领域雷达；质量低 → 多Agent评估；运营弱 → 跨平台策略
2. **AI Agent 设计**: 7 位专业 Agent 协作，非单模型问答
3. **自动化优化**: 反射循环自改进、A/B 标题测试
4. **微信生态**: 视频号策略 + 公众号适配 + 搜一搜 SEO + 私域引流
5. **商业可行性**: 可扩展为 SaaS 工具，Token 计费透明

### 微信生态集成点

- **视频号**: 双引擎推荐算法分析、社交裂变策略、创作者激励计划
- **公众号**: 长文排版适配、SEO 优化、引流设计
- **搜一搜**: 关键词布局建议
- **私域**: 粉丝沉淀策略、社群运营建议
