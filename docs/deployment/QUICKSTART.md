# Ripple 评委演示 / 本地启动指南

> 适用对象:腾讯 PCG 校园 AI 产品创意大赛评委、内部 review、合作伙伴试用
> 目标:**3 分钟内**让任何一位评委在自己电脑上跑起 Ripple 完整流水线

---

## 1. 30 秒最小启动(推荐)

```bash
cd ripple
./start.sh           # 一键启动 FastAPI + Streamlit + 产品介绍页
```

打开浏览器访问:

| 入口 | 地址 | 用途 |
|------|------|------|
| **Streamlit Demo** | <http://localhost:8501> | 主演示界面(评委首选) |
| FastAPI Docs | <http://localhost:8000/docs> | OpenAPI Swagger,可在线调试 12 Agent |
| 产品介绍页 | <http://localhost:5050> | 静态产品页(架构 / 卖点 / 定价) |

停止:`./start.sh stop` 状态:`./start.sh status`

---

## 2. 系统要求

| 组件 | 最低版本 | 说明 |
|------|----------|------|
| Python | 3.10+ | macOS 内置 3.9 也可,但建议 3.10+ |
| pip | 21+ | `python3 -m pip --version` |
| 内存 | 4 GB | mock 模式 / 8 GB 推荐(本地模型) |
| 端口 | 8000 / 8501 / 5050 | 启动脚本会自动检测占用 |
| OS | macOS / Linux / WSL2 | Windows 原生需 WSL2 |

启动脚本会**自动安装**缺失的关键依赖(`pyyaml`, `loguru`, `httpx`, `cryptography`, `argon2-cffi`, `streamlit`)。

完整依赖手动安装:

```bash
pip3 install --user -r apps/api/requirements.txt
pip3 install --user -r apps/streamlit_demo/requirements.txt
```

---

## 3. 三种演示模式

### 模式 A:**完全离线 mock**(零成本,演示流水线)

无需任何 API Key,即可看到 12 Agent 协作 + 编排器全流程。

```bash
./start.sh
# 浏览器: http://localhost:8501
# 选择 "Mock 模式" → 输入选题种子 → 一键生成
```

### 模式 B:**腾讯混元 + MiniMax**(推荐评委体验)

在 `apps/api/.env` 中填入(参考 `.env.example`):

```dotenv
MINIMAX_API_KEY=eyJhbGc...     # MiniMax 主力(已预置可用 Key)
HUNYUAN_API_KEY=sk-xxxxxxx     # 腾讯混元兜底 + 合规叙事
HUNYUAN_DEFAULT_MODEL=hunyuan-turbos-latest
```

重启 API:`./start.sh restart`

### 模式 C:**BYOK(用户自带 Key)**

打开 Streamlit 侧边栏 → "BYOK API Key 管理" → 选 Provider → 填 Key + 主密码 → 保存

Key 会用 **AES-256-GCM + Argon2id** 加密保存到本地 SQLite,服务端不持久化明文。详见 `docs/architecture/BYOK.md`。

---

## 4. 验证安装(不到 30 秒)

```bash
./start.sh test       # 全部 20 项测试(10 smoke + 10 E2E)
```

预期输出:

```
✓ 全部 10 个测试通过!
✓ 全部 10 个 E2E 测试通过!
```

---

## 5. 评委 90 秒演示动线(标准脚本)

| 时长 | 动作 | 演示要点 |
|------|------|----------|
| 0–10s | 打开 Streamlit | "AI 时代的 KOC 操作系统,12 Agent 协作" |
| 10–25s | 输入选题种子(如"黄金能买吗") | "不是给你 1 条建议,是给你 7 天前的早期信号" |
| 25–55s | 看 Phase 1 实时输出 | 强调 Polymarket / Manifold 等 9 个数据源,这是别人没有的 |
| 55–75s | 看 Phase 2 论坛辩论 | "3 专家 + 1 主持的论坛辩论,而不是单 Agent 黑盒" |
| 75–90s | 展示最终内容包 | 10 标题 + 4 平台脚本 + 3 封面 + 风险审查 + 归因报告 |

**杀手记忆点**:
1. **资本走在舆论之前**(Digital Oracle 哲学,与赛题"用 AI 解构传播规律"对齐)
2. **5 层记忆 + 4 层压缩**(直接移植 Claude Code 51 万行架构)
3. **BYOK + 端侧加密**(企业级安全,不是 toy)

---

## 6. 故障排查

| 症状 | 处理 |
|------|------|
| 端口 8000 占用 | `lsof -i :8000` 杀掉旧进程,或改 `start.sh` 中端口 |
| Streamlit 不响应 | `tail -f .logs/streamlit.log` 查日志 |
| `cryptography` 安装失败(macOS) | `brew install rust openssl` 后重试 `pip install` |
| Python 3.9 报类型错误 | 已用 `from __future__ import annotations` 兼容,如仍报错升级到 3.10+ |
| API 返回 500 | 检查 `.env` Key 是否填了真实 Key;mock 模式不需要 Key |
| 中文乱码 | 终端使用 UTF-8 (`export LANG=zh_CN.UTF-8`) |

---

## 7. 部署到云(可选,赛后线上化)

| 平台 | 部署的服务 | 推荐套餐 | 启动文件 |
|------|----------|----------|----------|
| **Vercel** | 产品介绍页 + Next.js 升级版 | 免费 Hobby | `apps/web/` |
| **Railway / Render** | FastAPI 后端 | $5/mo Starter | `apps/api/Dockerfile` |
| **Fly.io** | FastAPI + Postgres | $0–10/mo | `infra/docker/` |
| **腾讯云 CloudBase** | 全栈 + 微信小程序后端 | 弹性按量 | 需腾讯云账号 |

简易 Docker 部署:

```bash
cd infra/docker
docker compose up -d        # 启动 postgres + redis + api + streamlit
```

> **评审期备份策略**(关键!):
> - 主链路:本地 Demo + 录屏(2 份)
> - 备链路:Vercel 静态产品页 + Streamlit Cloud Demo
> - 灾备:Notion / Feishu 在线 PDF 链接 + Github Release

---

## 8. 文件位置速查

```
ripple/
├── start.sh                  ← 一键启动入口
├── apps/
│   ├── api/                  ← FastAPI 后端 + 12 Agent
│   ├── streamlit_demo/       ← 主演示 UI(给评委看)
│   ├── web/                  ← 产品介绍页(静态 HTML)
│   ├── desktop/              ← Tauri 桌面端(roadmap)
│   ├── miniprogram/          ← 微信小程序(roadmap)
│   └── pwa/                  ← 移动 PWA
├── docs/
│   ├── proposal/             ← LaTeX PDF 提案(评委必看)
│   ├── architecture/         ← 架构文档(BYOK 等)
│   ├── security/             ← 安全文档(STRIDE / OWASP)
│   ├── defense/              ← 答辩 Q&A
│   └── deployment/           ← 本文件所在
├── infra/docker/             ← Docker Compose 部署
└── ops/                      ← OpenTelemetry / Prometheus
```

---

## 9. 常用命令速查卡

```bash
./start.sh                    # 全启动
./start.sh stop               # 全停止
./start.sh status             # 查状态
./start.sh test               # 跑测试
./start.sh restart            # 重启

tail -f .logs/api.log         # 看 API 日志
tail -f .logs/streamlit.log   # 看 Streamlit 日志

# 单独跑测试
cd apps/api && python3 tests/test_smoke.py
cd apps/api && python3 tests/test_e2e_pipeline.py

# 编译 PDF 提案
cd docs/proposal && ./build.sh
```

---

如有任何问题,请联系参赛人员或查看 [docs/defense/QA.md](../defense/QA.md) 答辩话术。
