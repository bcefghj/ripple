# Ripple 3.0 — KOC 内容灵感助手

> **腾讯 PCG 校园 AI 产品创意大赛 · 赛道5：AI + 社媒流量增长，连接 KOC 成长**

Ripple 是一款 AI 原生的 KOC 内容灵感助手，帮助想成为 KOC 的新手完成从**选题**到**创作**的全流程。通过自然语言对话，Ripple 为用户提供领域洞察、选题灵感、爆款预测、内容创作和风格蒸馏五大核心能力。

## 核心亮点

### AI 思考过程全程透明
Ripple 实时展示 AI 的思考过程：搜索了什么、找到了多少数据、正在分析什么。用户不再面对一个"黑盒"，而是能看到 AI 是如何一步步理解需求、搜集数据、深度分析、最终给出建议的。

### 多 Agent 协同可视化
搜索 Agent、分析 Agent、创作 Agent、评审 Agent 各司其职，实时状态展示。并行执行，大幅提升响应速度。

### 12 维度爆款预测 + HKRR 模型
基于8个基础维度 + 影视飓风HKRR模型4维度的深度评估，配合环形进度条、雷达图、维度条形图等丰富的可视化动画。

### 五层认知蒸馏（参考女娲 Skill 方法论）
不是简单的风格模仿，而是从表达 DNA、心智模型、决策启发式、反模式到诚实边界的五层认知提炼。

### 深度绑定腾讯生态
优先分析视频号和微信公众号的内容趋势，搜索直接覆盖 `mp.weixin.qq.com` 和微信生态。内容创作优先输出视频号版和公众号版。

## 技术架构

```
FastAPI (Python 后端)     React + Vite (现代 SPA 前端)
  │                           │
  ├── 意图识别路由             ├── Tailwind CSS 4
  ├── SSE 流式传输             ├── Framer Motion 动画
  ├── 多引擎调度               ├── 思考过程可视化
  ├── 并行搜索（DuckDuckGo）    ├── 评分动画系统
  ├── LLM 网关（MiniMax/MiMo） └── 响应式三端适配
  └── SQLite 持久化
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

# 前端依赖 + 构建
cd web && npm install && npm run build && cd ..

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入 API key
```

### 运行

```bash
# 启动集成服务器（API + 前端）
python run.py serve

# 访问 http://localhost:8000
```

### 开发模式

```bash
# 后端（热重载）
python run.py serve --reload

# 前端开发服务器（另一个终端）
cd web && npm run dev
# 前端开发服务器自动代理 /api 请求到后端
```

## 功能模块

| 功能 | 说明 | 输入示例 |
|------|------|----------|
| **领域雷达** | 分析内容生态、热门博主、入场机会 | "帮我分析美食探店这个领域" |
| **选题灵感** | AI 生成 10-15 个创意选题 | "帮我想10个职场效率类选题" |
| **爆款预测** | 12 维度深度评分 + HKRR 模型 | "评估「月薪3000吃遍北京」的爆款潜力" |
| **内容创作** | 完整内容包 + 多平台版本 | "帮我写一篇小红书笔记" |
| **风格蒸馏** | 五层认知蒸馏方法论 | "分析一下李子柒的创作风格" |

## 项目结构

```
ripple3/
├── api/          # FastAPI 后端 API 层
│   ├── main.py   # FastAPI 应用入口
│   ├── routes.py # SSE 流式端点
│   └── sse.py    # SSE 事件格式化工具
├── web/          # React 前端 (Vite + TypeScript)
│   └── src/
│       ├── components/   # UI 组件
│       ├── hooks/        # React Hooks
│       └── lib/          # API 工具库
├── core/         # 核心模块
│   ├── intent.py # 意图识别路由
│   ├── llm.py    # LLM 网关
│   └── store.py  # SQLite 持久化
├── engines/      # 功能引擎
│   ├── idea_engine.py      # 选题引擎
│   ├── viral_predictor.py  # 爆款预测
│   ├── content_create.py   # 内容创作
│   └── style_distill.py    # 风格蒸馏
├── adapters/     # 外部服务适配器
│   └── search.py # 并行搜索（DuckDuckGo）
└── run.py        # 入口
```

## 对齐赛题评分标准

| 评分维度 | 实现方式 |
|----------|----------|
| **赛道适配性** | 深度绑定视频号/公众号/QQ，搜索覆盖腾讯生态 |
| **作品完整性** | 五大功能闭环 + 美观 UI + 在线可运行 |
| **创新性** | AI 思考过程可视化 + 多 Agent 协同 + 五层认知蒸馏 |
| **用户洞察** | 聚焦 KOC 新手痛点：不知道做什么 → 不知道能不能火 → 不会写 |
| **AI 原生性** | 全链路 AI，思考过程全程透明，流式输出 |
| **落地可行性** | Python + React 标准栈，单命令启动 |

## License

MIT
