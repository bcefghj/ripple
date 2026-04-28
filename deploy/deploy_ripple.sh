#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# Ripple 一键部署脚本
# 目标: 阿里云 ECS Ubuntu 22.04 (120.55.247.6)
#
# 用法:
#   chmod +x deploy/deploy_ripple.sh
#   DEPLOY_HOST=120.55.247.6 bash deploy/deploy_ripple.sh
# ============================================================

DEPLOY_HOST="${DEPLOY_HOST:-120.55.247.6}"
DEPLOY_USER="${DEPLOY_USER:-root}"
DEPLOY_DIR="/opt/ripple"
WEB_DIR="/var/www/ripple"
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "================================================================"
echo "  Ripple 部署 → ${DEPLOY_USER}@${DEPLOY_HOST}"
echo "  本地目录: ${PROJECT_ROOT}"
echo "  远端目录: ${DEPLOY_DIR}"
echo "================================================================"

# ---- Step 1: 本地打包 ----
echo ""
echo "[1/6] 本地打包..."
cd "${PROJECT_ROOT}"

TARBALL="/tmp/ripple_deploy.tar.gz"
tar czf "${TARBALL}" \
    --exclude='.venv' \
    --exclude='__pycache__' \
    --exclude='.env' \
    --exclude='*.pyc' \
    --exclude='.git' \
    --exclude='node_modules' \
    --exclude='.DS_Store' \
    .

echo "  打包完成: $(du -h "${TARBALL}" | cut -f1)"

# ---- Step 2: 上传 ----
echo ""
echo "[2/6] 上传到服务器..."
scp "${TARBALL}" "${DEPLOY_USER}@${DEPLOY_HOST}:/tmp/ripple_deploy.tar.gz"
echo "  上传完成"

# ---- Step 3-6: 远端执行 ----
echo ""
echo "[3/6] 远端安装..."

ssh "${DEPLOY_USER}@${DEPLOY_HOST}" bash -s <<'REMOTE_SCRIPT'
set -euo pipefail

DEPLOY_DIR="/opt/ripple"
WEB_DIR="/var/www/ripple"

# 安装基础依赖
echo "  安装系统依赖..."
apt-get update -qq
apt-get install -y -qq python3 python3-pip python3-venv nginx >/dev/null 2>&1

# 解压到部署目录(原子切换)
echo "  解压项目..."
rm -rf "${DEPLOY_DIR}.new"
mkdir -p "${DEPLOY_DIR}.new"
tar xzf /tmp/ripple_deploy.tar.gz -C "${DEPLOY_DIR}.new"

if [ -d "${DEPLOY_DIR}" ] && [ -f "${DEPLOY_DIR}/.env" ]; then
    cp "${DEPLOY_DIR}/.env" "${DEPLOY_DIR}.new/apps/api/.env" 2>/dev/null || true
fi

rm -rf "${DEPLOY_DIR}.old"
if [ -d "${DEPLOY_DIR}" ]; then
    mv "${DEPLOY_DIR}" "${DEPLOY_DIR}.old"
fi
mv "${DEPLOY_DIR}.new" "${DEPLOY_DIR}"

# Python 虚拟环境
echo "  创建虚拟环境并安装依赖..."
cd "${DEPLOY_DIR}/apps/api"
python3 -m venv venv
source venv/bin/activate
pip install -q --upgrade pip
pip install -q fastapi uvicorn httpx loguru pydantic pydantic-settings streamlit >/dev/null 2>&1
deactivate

# 静态网站
echo "  部署静态网站..."
mkdir -p "${WEB_DIR}"
cp -r "${DEPLOY_DIR}/apps/web/"* "${WEB_DIR}/"
# 如有 PDF 也复制过来
if [ -f "${DEPLOY_DIR}/docs/proposal/main.pdf" ]; then
    cp "${DEPLOY_DIR}/docs/proposal/main.pdf" "${WEB_DIR}/ripple_report.pdf"
fi

# nginx 配置
echo "  配置 nginx..."
cp "${DEPLOY_DIR}/deploy/nginx_ripple.conf" /etc/nginx/sites-available/ripple
ln -sf /etc/nginx/sites-available/ripple /etc/nginx/sites-enabled/ripple
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx

# systemd 服务 — FastAPI
echo "  配置 systemd 服务..."
cat > /etc/systemd/system/ripple-api.service <<EOF
[Unit]
Description=Ripple FastAPI Backend
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=${DEPLOY_DIR}/apps/api
Environment=PATH=${DEPLOY_DIR}/apps/api/venv/bin:/usr/local/bin:/usr/bin
EnvironmentFile=-${DEPLOY_DIR}/apps/api/.env
ExecStart=${DEPLOY_DIR}/apps/api/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# systemd 服务 — Streamlit
cat > /etc/systemd/system/ripple-streamlit.service <<EOF
[Unit]
Description=Ripple Streamlit Demo
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=${DEPLOY_DIR}/apps/streamlit_demo
Environment=PATH=${DEPLOY_DIR}/apps/api/venv/bin:/usr/local/bin:/usr/bin
EnvironmentFile=-${DEPLOY_DIR}/apps/api/.env
ExecStart=${DEPLOY_DIR}/apps/api/venv/bin/streamlit run app.py --server.port 8501 --server.address 127.0.0.1 --server.baseUrlPath /demo --browser.gatherUsageStats false
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable ripple-api ripple-streamlit
systemctl restart ripple-api ripple-streamlit

echo "  等待服务启动..."
sleep 3

# 验证
echo ""
echo "[4/6] 验证服务状态..."
systemctl is-active ripple-api && echo "  ripple-api: OK" || echo "  ripple-api: FAILED"
systemctl is-active ripple-streamlit && echo "  ripple-streamlit: OK" || echo "  ripple-streamlit: FAILED"

echo ""
echo "[5/6] 健康检查..."
curl -sf http://127.0.0.1:8000/health && echo "" && echo "  FastAPI: OK" || echo "  FastAPI: FAILED"
curl -sf http://127.0.0.1:80/ | head -c 100 && echo "" && echo "  Nginx: OK" || echo "  Nginx: FAILED"

echo ""
echo "[6/6] 清理..."
rm -f /tmp/ripple_deploy.tar.gz
rm -rf "${DEPLOY_DIR}.old"

echo ""
echo "================================================================"
echo "  部署完成!"
echo "  产品官网: http://120.55.247.6"
echo "  在线 Demo: http://120.55.247.6/demo"
echo "  API 文档:  http://120.55.247.6/docs"
echo "  健康检查:  http://120.55.247.6/health"
echo "================================================================"
REMOTE_SCRIPT

rm -f "${TARBALL}"
echo ""
echo "本地清理完成。部署结束。"
