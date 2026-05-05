# Ripple 6.0 部署指南

## 本地开发

### 环境要求
- Python >= 3.10
- Node.js >= 18
- npm >= 8

### 后端启动

```bash
cd ripple3

# 1. 创建环境配置
cp .env.example .env
# 编辑 .env，填入以下必需的 API Key：
# - XIAOMI_API_KEY (小米 MiMo 模型)
# - MINIMAX_API_KEY (MiniMax 联网搜索)

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动 API 服务
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 前端启动

```bash
cd ripple3/web

# 1. 安装依赖
npm install

# 2. 开发模式
npm run dev
# 访问 http://localhost:5173

# 3. 构建生产版本
npm run build
# 输出到 dist/，后端自动 serve
```

### 一键启动 (开发模式)

```bash
cd ripple3

# 后端 + 前端同时启动
python -m uvicorn api.main:app --port 8000 &
cd web && npm run dev &
```

---

## Docker 部署

### docker-compose.yml

```yaml
version: '3.8'

services:
  ripple:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./ripple.db:/app/ripple.db
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install Node.js for frontend build
RUN apt-get update && apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Frontend build
COPY web/package*.json web/
RUN cd web && npm ci

COPY web/ web/
RUN cd web && npm run build

# Backend code
COPY . .

EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 阿里云 ECS 部署

### 1. 服务器配置

- 操作系统: Ubuntu 22.04 / CentOS 8
- 最低配置: 2C4G
- 推荐配置: 4C8G（多 Agent 并行时内存需求）
- 带宽: >= 5Mbps

### 2. Nginx 配置

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Connection '';
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_buffering off;
        proxy_cache off;
        chunked_transfer_encoding on;
        # SSE 需要关闭缓冲
        proxy_read_timeout 300s;
    }

    location / {
        root /opt/ripple/web/dist;
        try_files $uri $uri/ /index.html;
    }
}
```

### 3. systemd 服务

```ini
[Unit]
Description=Ripple API Server
After=network.target

[Service]
Type=exec
User=www-data
WorkingDirectory=/opt/ripple
ExecStart=/usr/bin/python3 -m uvicorn api.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5
EnvironmentFile=/opt/ripple/.env

[Install]
WantedBy=multi-user.target
```

### 4. 部署步骤

```bash
# 1. 克隆代码
cd /opt
git clone https://github.com/bcefghj/ripple.git
cd ripple/ripple3

# 2. 配置环境
cp .env.example .env
vim .env  # 填入 API Keys

# 3. 安装依赖
pip3 install -r requirements.txt
cd web && npm ci && npm run build && cd ..

# 4. 启动服务
sudo systemctl enable ripple
sudo systemctl start ripple

# 5. 配置 Nginx
sudo cp nginx.conf /etc/nginx/sites-available/ripple
sudo ln -s /etc/nginx/sites-available/ripple /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

---

## 环境变量说明

| 变量 | 必需 | 说明 |
|------|------|------|
| `XIAOMI_API_KEY` | ✅ | 小米 MiMo 模型 (主力推理) |
| `MINIMAX_API_KEY` | ✅ | MiniMax 联网搜索 + 对话 |
| `HUNYUAN_SECRET_ID` | 推荐 | 腾讯混元 (比赛加分项) |
| `HUNYUAN_SECRET_KEY` | 推荐 | 腾讯混元 |
| `SERPER_API_KEY` | 推荐 | Google SERP 搜索 |
| `TAVILY_API_KEY` | 推荐 | Tavily AI 搜索 |
| `EXA_API_KEY` | 可选 | Exa 语义搜索 |
| `SEARXNG_URL` | 可选 | SearXNG 自建实例 |
| `JINA_API_KEY` | 可选 | Jina Reader (网页抓取) |

---

## 故障排查

### 常见问题

1. **搜索结果为空**: 检查 API Key 是否正确，确保至少配置了 MINIMAX_API_KEY
2. **知识图谱不显示**: 检查 radar 意图是否触发（日志中看 `intent: radar`）
3. **前端白屏**: 确保 `web/dist/` 目录存在且有 index.html
4. **SSE 断连**: 检查 Nginx 是否关闭了 proxy_buffering
5. **Token 用量过大**: 调低 `max_tokens` 参数或减少搜索层数
