# Ripple — KOC 早期信号雷达 + 多 Agent 内容工厂

> 「资本永远先于舆论。我们让 KOC 在话题刚开始火的 7-14 天窗口期看见它,而不是等热搜出现后追风。」

参赛作品 · 腾讯 PCG 校园 AI 产品创意大赛 · 命题 5(AI + 社媒流量增长,连接 KOC 成长)

---

## 一句话定位

**KOC 的 Bloomberg Terminal**:在热搜出现前 7-14 天告诉你下一个会火的话题,12 个 AI Agent 帮你把它做成可发布的内容包。

---

## 30 秒快速启动

```bash
cd ripple
./start.sh                # 一键启动 FastAPI + Streamlit + 产品介绍页
```

打开浏览器:

| 入口 | 地址 |
|------|------|
| **Streamlit Demo**(评委首选) | <http://localhost:8501> |
| FastAPI Docs | <http://localhost:8000/docs> |
| 产品介绍页 | <http://localhost:5050> |

更多操作:`./start.sh status` | `./start.sh test` | `./start.sh stop`

---

## 核心创新(3 个杀手锏)

### 🎯 #1 早期信号雷达(Oracle)
- 9 个数据源并行扫描:Polymarket / Manifold / Kalshi / 微信指数 / 巨量算数 / Reddit / HackerNews / GitHub / X
- 算法:CUSUM + MAD-zscore + LLM 矛盾推理
- 概念:借鉴 [Digital Oracle](https://oracle.komako.me/) 的「资本永远先于舆论」哲学

### 🤖 #2 12 Agent 论坛辩论(Forum)
- 移植 [BettaFish](https://github.com/Kocoro-lab/BettaFish) ForumEngine
- 4 Phase × 12 个专业 Agent 协作
- 多视角推理 + 反方意见 + 风险提示,而非单 Agent 黑箱

### 🧠 #3 Claude Code 架构移植
- TAOR 主循环 + 5 层记忆 + 4 层压缩 + Hooks + Skills + Subagent
- 端侧 BYOK 加密(AES-256-GCM + Argon2id)+ 11 个 LLM Provider
- 全栈开源,完全离线也能跑(Mock + 本地 Ollama)

---

## 灵感谱系

| 项目 | 借鉴的具体设计 |
|------|---------------|
| **Digital Oracle** | 早期信号思想(资本走在舆论之前) |
| **Claude Code(51 万行)** | TAOR 主循环 / 5 层记忆 / 4 层压缩 / Hooks / Skills / Subagent |
| **MiroFish** | 群体仿真(SimPredictor 附加增强) |
| **BettaFish** | 多 Agent 论坛辩论(ForumEngine) |
| **Hermes Agent** | Memory pattern + Plan-Execute-Reflect 循环 |

---

## 项目结构

```
ripple/
├── start.sh                            # ⭐ 一键启动
├── SUBMISSION.md                        # ⭐ 最终提交清单
│
├── apps/
│   ├── api/                             # FastAPI + 12 Agent + Claude Code 架构
│   │   ├── agent/                       # Claude Code 移植的主循环 / 记忆 / 压缩 / Hooks / Skills
│   │   ├── agents/                      # 12 个业务 Agent + Orchestrator
│   │   ├── utils/                       # LLM Router + BYOK 加密
│   │   ├── tests/                       # 10 smoke + 10 E2E 测试
│   │   └── main.py                      # FastAPI 入口
│   ├── streamlit_demo/                  # 主演示 UI(评委用)
│   ├── web/                             # 静态产品介绍页
│   ├── desktop/                         # Tauri 2 桌面端(roadmap)
│   ├── miniprogram/                     # 微信小程序(roadmap)
│   └── pwa/                             # 移动 PWA
│
├── docs/
│   ├── proposal/                        # ⭐ LaTeX PDF 提案 (24 页)
│   │   ├── main.tex
│   │   ├── build.sh                     # 一键编译
│   │   └── PDF_GUIDE.md                 # 编译指引
│   ├── deployment/
│   │   ├── QUICKSTART.md                # ⭐ 评委 / 评审使用指南
│   │   └── CLOUD_DEPLOY.md              # 云端部署
│   ├── architecture/BYOK.md             # BYOK 端侧加密
│   ├── security/STRIDE.md               # STRIDE 威胁建模 + OWASP LLM Top 10 v2
│   ├── defense/QA.md                    # 答辩 Q&A 20 题
│   ├── review/CRITICAL_REVIEW.md        # 五视角批判性 review 清单
│   └── video/SCRIPT.md                  # 录屏脚本(3 分钟分镜)
│
├── infra/docker/                        # Docker Compose 部署
└── ops/                                 # OpenTelemetry / Prometheus
```

---

## 文档导航

### 评委 / 评审必看
- [📺 评委 30 秒启动指南](docs/deployment/QUICKSTART.md)
- [📋 提案 PDF](docs/proposal/main.pdf)
- [🎬 录屏脚本](docs/video/SCRIPT.md)

### 技术深度
- [🏗 BYOK 端侧加密架构](docs/architecture/BYOK.md)
- [🔒 STRIDE 威胁建模](docs/security/STRIDE.md)
- [☁️ 云端部署指南](docs/deployment/CLOUD_DEPLOY.md)
- [📐 PDF 编译指引](docs/proposal/PDF_GUIDE.md)

### 答辩准备
- [💬 答辩 Q&A 20 题](docs/defense/QA.md)
- [🔍 五视角批判性 Review](docs/review/CRITICAL_REVIEW.md)
- [📤 最终提交清单](SUBMISSION.md)

---

## 测试与质量

```bash
./start.sh test                # 跑全部测试
# Smoke 测试:10/10 通过
# E2E 集成测试:10/10 通过
```

包含:
- 5 层记忆系统 / 4 层压缩管线 / Hooks 安全 / BYOK 加解密
- 11 个 LLM Provider 注册 / Skills 渐进披露
- OracleAgent 9 数据源 / Orchestrator 完整流水线 / 流式 WebSocket

---

## 核心技术栈

| 层 | 选型 |
|----|------|
| 后端 | Python 3.10+ + FastAPI + LiteLLM + Pydantic v2 + loguru |
| Agent | 自研 12 Agent + 移植 Claude Code 架构 |
| LLM | MiniMax M2.7 主 / 腾讯混元兜底 / DeepSeek / 豆包 / 智谱 / Kimi / Claude / GPT / Ollama / LM Studio (BYOK) |
| 数据 | PostgreSQL 16 + pgvector + Redis + SQLite (本地) |
| 前端 | Next.js 15(规划)/ Streamlit(MVP)/ Tauri 2(桌面)/ 微信小程序(roadmap)/ PWA |
| 加密 | AES-256-GCM + Argon2id (OWASP 2025 推荐参数) |
| 文档 | LaTeX (xelatex + ctex + tikz + tcolorbox) |
| 部署 | Docker Compose + Vercel + Railway + Streamlit Cloud |
| 观测 | OpenTelemetry + Prometheus + Sentry + Langfuse |

---

## 提交物清单

| 类型 | 文件名 | 状态 |
|------|--------|------|
| **Demo** | 本地 `./start.sh` + 云端备份 | ✅ |
| **录屏视频** | `选手姓名_命题5_Ripple_Demo演示.mp4` | ⏳ 录制(脚本在 `docs/video/SCRIPT.md`) |
| **PDF 文档** | `选手姓名_命题5_Ripple_Demo演示.pdf` | ✅ 24 页 / ~500KB |

详见 [SUBMISSION.md](SUBMISSION.md) 完整提交清单。

---

## 开源许可

MIT License(待最终确认),欢迎学术研究 / 个人使用 / 二次开发。

---

## 致谢

- Anthropic Claude Code 团队 — 51 万行架构启发
- Komako Workshop / Digital Oracle — 早期信号哲学
- Kocoro Lab(BettaFish / Shannon)— 多 Agent 框架
- 腾讯 PCG / MiniMax / 字节跳动 / DeepSeek 等 LLM 提供方
