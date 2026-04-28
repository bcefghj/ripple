# Ripple 云端部署指南(评审期备份)

> **目标**:在评审期(8 天)内,确保本地 Demo + 云端备份双链路,任何一个挂掉都不影响展示。

---

## 1. 部署拓扑

```
                    ┌──────────────────┐
                    │   评委 / 用户     │
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
       ┌────────────┐ ┌────────────┐ ┌────────────┐
       │ Vercel 静  │ │ Streamlit  │ │ 本地 Demo   │
       │ 态产品页   │ │ Cloud Demo │ │ (录屏备份)  │
       └─────┬──────┘ └─────┬──────┘ └────────────┘
             │              │
             └──────┬───────┘
                    ▼
            ┌───────────────┐
            │ Railway/Fly   │
            │ FastAPI 后端  │
            │  + 12 Agent   │
            └───────┬───────┘
                    ▼
            ┌───────────────┐
            │  腾讯云 COS   │ ← 静态资源
            │  腾讯云混元   │ ← 主 LLM
            │  Postgres     │ ← (可选)
            └───────────────┘
```

---

## 2. Vercel 部署(产品介绍页 5 分钟上线)

### 2.1 准备

```bash
cd ripple/apps/web
# 当前是纯静态 HTML,无需 build
```

### 2.2 部署

方式 A:CLI

```bash
npm i -g vercel
vercel login
vercel --prod        # 跟提示一路回车,project name = ripple
```

方式 B:Web Dashboard
1. <https://vercel.com/new> 导入 GitHub 仓库
2. Framework Preset 选 **Other**
3. Root Directory 选 `apps/web`
4. Build Command 留空
5. Output Directory 填 `.`(当前目录)
6. Deploy

### 2.3 自定义域名(可选)

Vercel Dashboard → Settings → Domains → 添加(如 `ripple.komako.me`)

---

## 3. Railway 部署 FastAPI 后端

### 3.1 增加 Dockerfile

如果还没有,在 `apps/api/Dockerfile`:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PORT=8000
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 3.2 部署

1. <https://railway.app/new> → Deploy from GitHub Repo
2. Root Directory 填 `apps/api`
3. Variables(必填):
   ```
   MINIMAX_API_KEY=eyJhbGc...
   HUNYUAN_API_KEY=sk-xxx
   HUNYUAN_DEFAULT_MODEL=hunyuan-turbos-latest
   DB_URL=postgresql://...   # 可选,Railway 一键加 Postgres
   ```
4. Deploy → 自动给个 URL 如 `ripple-api-production.up.railway.app`

### 3.3 健康检查

```bash
curl https://ripple-api-production.up.railway.app/health
# {"status": "ok", "version": "0.1.0"}
```

---

## 4. Streamlit Cloud 部署(零配置)

1. <https://share.streamlit.io> → New app
2. Repo: `ripple`,Branch: `main`,Main file path: `apps/streamlit_demo/app.py`
3. Advanced settings:
   ```
   RIPPLE_API_BASE = https://ripple-api-production.up.railway.app
   ```
4. Deploy → 得到 `https://ripple-demo.streamlit.app`

---

## 5. Docker Compose 自托管(评委可一行启动)

```bash
cd ripple/infra/docker
docker compose up -d
```

启动:
- `postgres:15` (端口 5432) - 多租户存储 + RLS
- `redis:7` (6379) - 速率限制 / 任务队列
- `api` (8000) - FastAPI + 12 Agent
- `streamlit_demo` (8501) - 演示 UI

停止:`docker compose down`

---

## 6. 评审期高可用清单

### 主链路(必须)
- [ ] 本地 Demo 双备份(主 Mac + 备用 Mac/PC)
- [ ] 录屏 1080p MP4(≤500MB,≤3min)上传 3 份(B 站 unlisted / 腾讯微云 / 飞书)
- [ ] PDF 答辩文档上传腾讯文档 + Notion + GitHub Release

### 备链路(强烈推荐)
- [ ] Vercel 产品介绍页(`ripple.app` 或 `ripple-xxx.vercel.app`)
- [ ] Railway FastAPI 后端 + 健康检查 ping(每 5min)
- [ ] Streamlit Cloud Demo(可线上一键演示)
- [ ] Docker Compose 一键启动包(放 GitHub,评委可下载)

### 灾备(防黑天鹅)
- [ ] 录屏镜像:阿里云盘 + 百度网盘
- [ ] PDF 镜像:邮件附件给自己 + 腾讯文档外链
- [ ] 演示稿外发(关键评委可拿到无演示也能看懂)

---

## 7. 监控与告警

| 工具 | 用途 | 配置文件 |
|------|------|----------|
| **UptimeRobot** | 5min ping 健康检查 | <https://uptimerobot.com> 添加 `/health` |
| **Sentry** | 错误追踪 | `apps/api/main.py` 已预留 `SENTRY_DSN` |
| **Prometheus** | 指标 | `ops/prometheus/prometheus.yml` |
| **OpenTelemetry** | Trace | `ops/otel/otel-collector-config.yaml` |
| **Langfuse** | LLM 调用追踪 | 在 `.env` 配 `LANGFUSE_*` |

---

## 8. 成本估算(评审期 8 天)

| 项目 | 提供商 | 单价 | 8 天预估 |
|------|--------|------|----------|
| FastAPI 后端 | Railway Starter | $5/mo | ~$1.5 |
| 数据库 | Railway Postgres | $5/mo | ~$1.5 |
| Vercel | Hobby | 免费 | 0 |
| Streamlit Cloud | 免费 | 免费 | 0 |
| LLM 调用 | 混元 turbos / MiniMax | ~¥0.01/次 | ¥10–30 |
| 录屏存储 | B 站 / 微云 | 免费 | 0 |
| **合计** | | | **< ¥50** |

---

## 9. 故障应急方案

| 故障 | 一线处置 | 二线处置 |
|------|----------|----------|
| Railway 后端挂 | 切 Streamlit Cloud(内置 mock) | 启动本地 Demo + 备用 Mac |
| Vercel 静态页 404 | 切 GitHub Pages 镜像 | 截图 + PDF 演示 |
| LLM Key 被限流 | 自动 fallback 到下一个 Provider(LiteLLM) | 切 mock 模式 |
| 演示当天网断 | 启动本地 Demo + 录屏播放 | 用 PDF + 现场口述 |

---

## 10. 部署执行清单(8 天倒排)

| 距离评审 | 必须完成 |
|----------|----------|
| **D-7** | 本地 Demo 完整跑通 + 全部测试通过 |
| **D-6** | Vercel 产品页上线 + 自定义域名 |
| **D-5** | Railway 后端上线 + 健康检查 |
| **D-4** | Streamlit Cloud 上线 + 联通 Railway 后端 |
| **D-3** | 完整录屏第 1 版 + PDF 编译 |
| **D-2** | 五视角 review + 录屏第 2 版(终版) |
| **D-1** | 全链路演练 + 监控配置 + 备份镜像 |
| **D-0** | 提交资料 + 启动 UptimeRobot |

---

如需 CI/CD 自动化,参考 `ripple/.github/workflows/`(预留)。
