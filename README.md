<div align="center">

# 🌊 Ripple 涟漪 — KOC 决策智能平台

### AI-Native Social Media Growth Engine for Content Creators

[![腾讯 PCG 校园 AI 大赛](https://img.shields.io/badge/腾讯_PCG-校园AI产品创意大赛-blue?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZmlsbD0iI2ZmZiIgZD0iTTEyIDJDNi40OCAyIDIgNi40OCAyIDEyczQuNDggMTAgMTAgMTAgMTAtNC40OCAxMC0xMFMxNy41MiAyIDEyIDJ6bTAgMThjLTQuNDEgMC04LTMuNTktOC04czMuNTktOCA4LTggOCAzLjU5IDggOC0zLjU5IDgtOCA4eiIvPjwvc3ZnPg==)](https://gameinstitute.qq.com/college)
[![React 19](https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react)](https://react.dev)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![Three.js](https://img.shields.io/badge/Three.js-3D_Graph-black?style=flat-square&logo=three.js)](https://threejs.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)

**赛道5: AI + 社媒流量增长，连接 KOC 成长**

[🎮 在线 Demo](http://120.55.247.6/chat) · [📄 技术报告](http://120.55.247.6/ripple_tech_report.pdf) · [🎬 演示视频](#demo-video)

</div>

---

## 💡 一句话定位

> **你的 AI 内容军师** — 通过 9 层搜索矩阵聚合全网数据，7 位 AI 专家圆桌辩论，3D 知识图谱可视化领域生态，CES 爆款评分预测流量池，帮助 KOC 从"不知道做什么"到"做出下一篇爆款"。

---

## 🏗️ 系统架构

```
用户输入 → 智能意图引擎 (自动识别 + 流式衔接)
    ↓
话题分解引擎 → 30+ 精准子查询
    ↓
┌──────────────────────────────────────────────────┐
│         9 层搜索矩阵 (并行, Semaphore=30)          │
│  MiniMax | 混元 | Tavily | Exa | Serper | DDG     │
│  百度 | DailyHot | 社交平台API | SearXNG | Jina    │
└──────────────────────────────────────────────────┘
    ↓
相关性双重过滤 (关键词 + LLM 分类) → >80% 相关
    ↓
搜索质量自测 (4 维度) → 不达标自动重搜
    ↓
┌──────────────────────────────────────────────────┐
│     7 位 AI 专家 · 2 轮辩论 · 仲裁共识             │
│  📊 数据分析师 | 🎨 内容策划师 | 🧠 用户心理专家    │
│  ⚙️ 平台运营 | 🛡️ 风控专家 | 📈 行业研究员         │
│  👤 用户代言人 |  🏛️ 首席仲裁者                     │
└──────────────────────────────────────────────────┘
    ↓
CES 爆款评分 + 反射循环自改进
    ↓
3D 知识图谱 + 流式 SSE → React 前端
```

---

## ✨ 核心能力

### 1. 3D 知识图谱 (全网首创)

沉浸式宇宙星空主题可视化，从搜索数据中自动提取 **80-150 个实体节点** 和 **200+ 关系边**，展现领域完整生态：
- 节点按类型使用不同三维几何体 (球体/二十面体/立方体/八面体...)
- 节点脉冲发光 + 轨道环 + 连线粒子流动画
- 点击节点触发深度探索，动态扩展子图
- 全屏沉浸模式 + 星空粒子背景 + 星云效果

### 2. 9层搜索矩阵

| 层级 | 搜索源 | 特点 |
|------|--------|------|
| L0 | MiniMax 联网搜索 | Token Plan 免费 450次/日 |
| L1 | 腾讯混元 | EnableEnhancement (比赛加分) |
| L2 | Tavily / Exa | AI 优化语义搜索 |
| L3 | Serper (Google) | SERP 结构化结果 |
| L4 | DuckDuckGo | 免费无限 |
| L5 | 百度搜索 | 中文内容覆盖 |
| L6 | SearXNG | 元搜索聚合 |
| L7 | 平台 API | 小红书/B站/抖音直连 |
| L8 | DailyHot + Jina | 热搜聚合 + 深度抓取 |

### 3. 多 Agent 圆桌辩论

7 位不同视角的 AI 专家进行 2 轮结构化辩论：
- **第一轮**：独立分析，各抒己见
- **第二轮**：交叉讨论，观点碰撞
- **仲裁**：首席仲裁者综合研判，给出最终建议

### 4. CES 爆款评分预测

内置小红书官方 CES 公式 + 19 维度 100 分评分体系：
- 流量池阶梯预测: 冷启动池 → 初级池 → 热门池 → 爆款池
- 实时动态仪表盘可视化评分过程
- 优势/短板自动诊断 + 优化建议

### 5. 搜索雷达可视化

9 层同心圆实时动画，展示 AI 搜索全过程：
- 光点在各层环上运动，代表搜索源工作状态
- 找到结果时粒子飞向中心
- 实时显示 Token 消耗和进度

---

## 🚀 快速开始

### 环境要求
- Python >= 3.10
- Node.js >= 18

### 安装运行

```bash
# 克隆项目
git clone https://github.com/bcefghj/ripple.git
cd ripple/ripple3

# 后端
cp .env.example .env
# 编辑 .env 填入你的 API Key
pip install -r requirements.txt
python run.py

# 前端 (新终端)
cd web
npm install
npm run dev
```

访问 http://localhost:5173 即可体验。

### Docker 部署

```bash
cd infra/docker
docker-compose up -d
```

---

## 📁 项目结构

```
ripple3/                    ← 主代码 (Ripple 6.0)
├── api/                   # FastAPI 后端入口
├── core/                  # 配置、LLM 网关、意图引擎
├── engines/               # AI 引擎集合
│   ├── graph_builder.py   # 知识图谱构建
│   ├── multi_agent.py     # 多 Agent 辩论
│   ├── viral_scorer.py    # CES 爆款评分
│   ├── viral_predictor.py # 流量池预测
│   ├── content_create.py  # 内容创作
│   ├── topic_decomposer.py # 话题分解
│   └── reflection.py      # 反射循环
├── adapters/              # 搜索引擎适配器 (9层)
├── web/                   # React 19 + Vite + Three.js 前端
│   └── src/components/
│       ├── KnowledgeGraph3D.tsx  # 3D 知识图谱
│       ├── SearchRadar.tsx       # 搜索雷达动画
│       ├── MultiAgentPanel.tsx   # 圆桌会议
│       ├── ViralScorePanel.tsx   # 爆款仪表盘
│       └── ...
├── tests/                 # 测试套件
└── requirements.txt
```

---

## 🏆 赛道对齐

| 评分维度 | Ripple 的回应 |
|---------|--------------|
| **赛道适配性** | 专为 KOC 设计，覆盖选题→创作→评估→优化全流程 |
| **作品完整性** | 在线 Demo + 录屏 + PDF + 可跑通的端到端案例 |
| **创新性** | 3D 知识图谱 + 9层搜索 + 多 Agent 辩论（全网首创组合） |
| **用户洞察** | 基于真实 KOC 痛点（定位难/质量低/运营弱）设计 |
| **AI 原生性** | AI 是核心引擎，非辅助功能；LLM 深度融合全链路 |
| **落地可行性** | 已部署阿里云，可体验；技术栈成熟可扩展 |

---

## 🛠️ 技术栈

**后端**: Python 3.12 · FastAPI · uvicorn · httpx · Pydantic · SQLite

**前端**: React 19 · Vite · TypeScript · Tailwind CSS 4 · Framer Motion · Three.js · react-force-graph-3d · Recharts · GSAP

**AI**: MiniMax · 腾讯混元 · 小米 MiMo · 多引擎搜索矩阵

**部署**: Docker · Nginx · 阿里云 ECS

---

## 📜 License

MIT License - 参见 [LICENSE](LICENSE) 文件

---

<div align="center">
<sub>Built with ❤️ for Tencent PCG Campus AI Competition 2026</sub>
</div>
