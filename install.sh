#!/usr/bin/env bash
# Ripple 2.0 一键安装脚本 - 支持 Mac / Linux / Windows (WSL)
#
# 用法:
#   curl -sSL https://raw.githubusercontent.com/bcefghj/ripple/main/install.sh | bash
#
# 或者:
#   git clone https://github.com/bcefghj/ripple && cd ripple && bash install.sh

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${BLUE}==>${NC} $*"; }
ok()  { echo -e "${GREEN}✓${NC} $*"; }
warn() { echo -e "${YELLOW}⚠${NC} $*"; }
err() { echo -e "${RED}✗${NC} $*"; }

OS=$(uname -s)
ARCH=$(uname -m)

log "Ripple 2.0 安装程序"
log "OS: $OS $ARCH"

# 1. 检查 Python
if ! command -v python3 >/dev/null; then
    err "需要 Python 3.10+, 请先安装"
    exit 1
fi
PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
ok "Python $PY_VERSION 已安装"

# 2. 检查 git
if ! command -v git >/dev/null; then
    err "需要 git, 请先安装"
    exit 1
fi

# 3. 克隆仓库 (如果还没有)
if [ ! -d "ripple" ] && [ ! -f "apps/api/main.py" ]; then
    log "克隆仓库..."
    git clone https://github.com/bcefghj/ripple.git
    cd ripple
fi

if [ ! -f "apps/api/main.py" ] && [ -d "ripple/apps" ]; then
    cd ripple
fi

# 4. 创建虚拟环境
log "创建 Python 虚拟环境..."
python3 -m venv venv
source venv/bin/activate

# 5. 安装依赖
log "安装依赖..."
pip install --quiet --upgrade pip
pip install --quiet -r apps/api/requirements.txt
ok "依赖安装完成"

# 6. 配置 .env
if [ ! -f "apps/api/.env" ]; then
    log "请配置 LLM API Key:"
    echo ""
    echo "支持的 Provider:"
    echo "  - 小米 MiMo (XIAOMI_API_KEY) - 默认首选"
    echo "  - MiniMax (MINIMAX_API_KEY)"
    echo "  - DeepSeek (DEEPSEEK_API_KEY)"
    echo "  - 腾讯混元 (HUNYUAN_API_KEY)"
    echo ""
    read -p "请输入 XIAOMI_API_KEY (或回车跳过): " XIAOMI_KEY
    read -p "请输入 MINIMAX_API_KEY (或回车跳过): " MINIMAX_KEY

    cat > apps/api/.env <<EOF
# Ripple 2.0 配置
XIAOMI_API_KEY=$XIAOMI_KEY
MINIMAX_API_KEY=$MINIMAX_KEY
APP_ENV=local
LOG_LEVEL=INFO
EOF
    ok ".env 已写入"
fi

# 7. 初始化 SQLite
log "初始化 SQLite..."
cd apps/api
python3 -c "from kernel.persistence.db import init_db; init_db()"
cd ../..
ok "SQLite 已初始化在 ~/.ripple/ripple.db"

# 8. 启动建议
echo ""
ok "安装完成!"
echo ""
echo "启动:"
echo "  source venv/bin/activate"
echo "  cd apps/api && uvicorn main:app --port 8000"
echo ""
echo "然后打开:"
echo "  - 本地 Web Chat: 把 apps/web-chat/index.html 用 file:// 打开"
echo "  - 或部署到 Nginx, 见 deploy/ 目录"
echo "  - API 文档: http://localhost:8000/docs"
echo ""
echo "Cursor / Claude Code 集成 (MCP):"
echo "  在 ~/.cursor/mcp.json 添加:"
echo '  { "mcpServers": { "ripple": { "command": "npx", "args": ["-y", "@ripple/mcp"] } } }'
echo ""
