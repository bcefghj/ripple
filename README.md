# Ripple 涟漪 — KOC 决策智能平台

> **用 AI 拿捏社媒流量密码，帮普通 KOC 轻松涨粉。**

**参赛作品** · 腾讯 PCG 校园 AI 产品创意大赛 · 命题 5（AI + 社媒流量增长，连接 KOC 成长）

---

## Ripple 6.0 — KOC 决策智能平台 (最新版)

**一句话定位**: 你的 KOC 决策智能助手 — 9层搜索矩阵 + 多Agent辩论 + CES爆款预测，帮你从"不知道做什么"到"做出第一篇爆款"。

### 版本演进

| 对比 | v3.0 | v6.0 |
|------|------|------|
| **搜索引擎** | 4路并行，329条 | 9层矩阵，1000+条 |
| **搜索相关性** | 无过滤 | LLM批量分类 + 相关性>80% |
| **查询策略** | 宽泛关键词拼接 | Topic Decomposition 4层精准分解 |
| **Agent系统** | 3位专家，15条数据 | 5+1 Agent辩论，50-100条数据 |
| **爆款预测** | HKRR 12维度 | CES 19维100分 + 流量池预测 |
| **质量控制** | 无 | 搜索自测 + 反射循环自改进 |
| **可视化** | 基础进度条 | Token消耗 + 爆款评分 + Agent面板 |
| **意图引导** | 手动触发 | 自动引导 + 下一步建议 |

### 核心创新 (6.0 独有)

#### 1. 9层搜索矩阵 + Topic Decomposition
- **Layer 0**: MiniMax 联网搜索（Token Plan 450次/日免费）
- **Layer 1**: 腾讯混元 EnableEnhancement（比赛加分项）
- **Layer 2-8**: Tavily / Exa / Serper / DuckDuckGo / 百度 / DailyHot / 社交平台
- **话题分解**: 宽泛领域 → 子话题树 → 30+ 精准查询

#### 2. CES 爆款预测评分 (核心差异化)
- 小红书官方 CES 公式内置: `关注*8 + 评论*4 + 转发*4 + 收藏*1 + 点赞*1`
- 19维100分评分体系（标题吸引力/情绪共鸣/平台适配/竞争蓝海...）
- 流量池阶梯预测: 冷启动池 → 初级池 → 热门池

#### 3. 自改进反射循环 (Reflection Pattern)
- 搜索反射: 相关性不足 → 自动重写查询 → 重搜
- 分析反射: Agent输出空洞 → 要求补充证据 → 重新分析
- 终止条件: 最多2轮迭代，或质量分>=80

#### 4. 多Agent 2轮辩论制
- 5位专家: 数据分析师 / 内容策划师 / 平台运营专家 / 用户画像师 / 趋势研究员
- 仲裁者: 整合观点，指出矛盾，最终决策
- 强制证据引用: 每个观点必须引用具体搜索数据

### 技术栈

| 层 | 选型 |
|----|------|
| 后端 | Python 3.9+ · FastAPI · asyncio |
| 前端 | React 19 · TypeScript · Tailwind 4 · Framer Motion |
| AI/LLM | MiniMax M2.7 首选 · 腾讯混元 · 小米 MiMo |
| 搜索 | 9引擎矩阵 (MiniMax/混元/Tavily/Exa/Serper/DDG/百度/DailyHot/社交平台) |
| 算法 | CES评分 · Topic Decomposition · Reflection Loop · 相关性过滤 |
| 存储 | SQLite 对话历史 + 用户偏好 |
| 部署 | Docker + nginx + 阿里云 ECS |

### 快速启动

```bash
# 1. 克隆
git clone https://github.com/bcefghj/ripple.git && cd ripple

# 2. 安装依赖
cd ripple3
pip install -r requirements.txt
cd web && npm install && cd ..

# 3. 配置
cp .env.example .env
# 编辑 .env，填入 MINIMAX_API_KEY

# 4. 启动后端
python -m uvicorn api.main:app --reload --port 8001

# 5. 启动前端 (新终端)
cd web && npm run dev

# 6. 访问
# 前端: http://localhost:5173
# API文档: http://localhost:8001/docs
```

### 核心功能（对话触发 + 智能引导）

- **探索领域**: "帮我分析数码科技领域" → 9层搜索1000+条 + 5Agent讨论 + 生态报告
- **发现选题**: "帮我想选题" → 基于实时数据 + 蓝海分析 + 差异化建议
- **评估选题**: "评估折叠屏手机一年体验" → CES 19维评分 + 流量池预测 + 优化建议
- **创作内容**: "帮我写小红书笔记" → 多平台适配 + 内容DNA分析
- **分析风格**: "分析何同学的风格" → 蒸馏方法论 + 可复用框架

### 架构 (Ripple 6.0)

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

---

## 在线体验

| 入口 | 地址 | 说明 |
|------|------|------|
| **产品官网** | http://120.55.247.6 | 了解产品定位、技术亮点 |
| **在线 Demo** | http://120.55.247.6/demo | 在线体验 |
| **API 文档** | http://120.55.247.6/docs | FastAPI Swagger |

---

## 项目结构

```
ripple/
├── ripple3/                           # ★ 核心代码 (Ripple 6.0)
│   ├── adapters/                      # 搜索引擎适配器 (9层)
│   │   ├── search.py                  # 搜索编排器主逻辑
│   │   ├── minimax_search.py          # MiniMax 联网搜索
│   │   ├── hunyuan_search.py          # 腾讯混元搜索增强
│   │   ├── query_builder.py           # 4层查询策略生成器
│   │   └── ...                        # 其他引擎适配器
│   ├── engines/                       # AI 引擎模块
│   │   ├── topic_decomposer.py        # 话题分解引擎
│   │   ├── multi_agent.py             # 多Agent讨论系统
│   │   ├── viral_scorer.py            # CES 爆款评分模型
│   │   ├── relevance_filter.py        # 相关性过滤器
│   │   ├── search_validator.py        # 搜索质量验证
│   │   ├── reflection.py              # 自改进反射循环
│   │   └── content_dna.py             # 内容DNA分析
│   ├── api/                           # FastAPI 后端
│   │   ├── routes.py                  # API路由 + SSE流
│   │   └── sse.py                     # 事件流系统
│   ├── core/                          # 核心配置
│   │   ├── config.py                  # 配置管理
│   │   ├── intent.py                  # 意图识别引擎
│   │   └── store.py                   # 数据存储
│   ├── web/                           # React 前端
│   │   └── src/
│   │       ├── components/            # UI组件
│   │       │   ├── TokenUsagePanel.tsx # Token消耗可视化
│   │       │   ├── ViralScorePanel.tsx # CES评分面板
│   │       │   └── ...
│   │       └── hooks/useChat.ts       # 聊天状态管理
│   └── tests/                         # 自动化测试
│
├── apps/                              # 旧版入口 (v1/v2 兼容)
│   ├── api/                           # v1 FastAPI + 12Agent
│   ├── streamlit_demo/                # Streamlit 演示
│   └── web/                           # 产品官网
│
├── docs/                              # 文档
│   ├── proposal/                      # LaTeX 技术报告
│   └── defense/QA.md                  # 答辩 Q&A
│
├── deploy/                            # 部署脚本
│   ├── deploy_ripple.sh               # 一键部署
│   └── nginx_ripple.conf              # nginx 配置
│
├── _handover/                         # 交接材料 (本地参考)
│
└── start.sh                           # 一键启动
```

---

## 差异化优势 (vs 竞品)

| 维度 | ChatGPT | OClaw | 蝉妈妈 | **Ripple 6.0** |
|------|---------|-------|--------|----------------|
| 搜索量 | 5-10条 | 不搜索 | 历史数据 | **1000+条实时** |
| 相关性 | 依赖引擎 | — | 高 | **LLM过滤>80%** |
| 分析深度 | 单视角 | 单Agent | 数据面板 | **5Agent辩论** |
| 爆款预测 | 通用建议 | 互动率 | CES历史 | **19维CES+流量池** |
| 成本 | $20/月 | ¥199 | ¥8000/年 | **开源免费** |
| 自改进 | 无 | 无 | 无 | **反射循环** |

---

## 参考项目

- **GPT Researcher** (26k stars): 20+源聚合、质量验证循环
- **Nexus Agents**: Topic Decomposition + A2A 通信
- **DingBulb**: 5 Agent 并行内容创作
- **Digital Oracle**: 多信号交叉验证哲学
- **Viral Loop Engine**: 加权互动率评分公式
- **小红书 CES 公式**: `关注*8 + 评论*4 + 转发*4 + 收藏*1 + 点赞*1`
- **Claude Code 架构**: TAOR 主循环 / 5 层记忆 / Hooks / Skills

---

## 提交物清单

| 类型 | 文件 | 状态 |
|------|------|------|
| **Demo** | http://120.55.247.6 | ✅ |
| **技术报告** | [在线下载](http://120.55.247.6/ripple_report.pdf) | ✅ |
| **源码** | [GitHub](https://github.com/bcefghj/ripple) | ✅ |

---

## 开源许可

MIT License

---

## 致谢

- Anthropic Claude Code 团队 — 架构启发
- Komako Workshop / Digital Oracle — 早期信号哲学
- 腾讯 PCG / MiniMax / 小米 MiMo / DeepSeek 等 LLM 提供方
- GPT Researcher / Nexus Agents / DingBulb — 搜索和Agent架构参考
