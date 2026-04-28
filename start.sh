#!/usr/bin/env bash
# Ripple 一键启动脚本(本地评审 / 评委演示)
#
# 用法:
#   ./start.sh              # 启动 Streamlit Demo + FastAPI 后端
#   ./start.sh api          # 仅启动 FastAPI
#   ./start.sh streamlit    # 仅启动 Streamlit
#   ./start.sh web          # 启动产品介绍页(静态 HTML)
#   ./start.sh test         # 跑全部测试
#   ./start.sh stop         # 停止全部进程

set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
API_DIR="$ROOT_DIR/apps/api"
STREAMLIT_DIR="$ROOT_DIR/apps/streamlit_demo"
WEB_DIR="$ROOT_DIR/apps/web"
PID_DIR="$ROOT_DIR/.pids"
LOG_DIR="$ROOT_DIR/.logs"

mkdir -p "$PID_DIR" "$LOG_DIR"

# ============================================================
# 颜色输出
# ============================================================

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info()    { echo -e "${BLUE}[INFO]${NC}  $*"; }
log_ok()      { echo -e "${GREEN}[ OK ]${NC}  $*"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
log_err()     { echo -e "${RED}[FAIL]${NC}  $*"; }

# ============================================================
# 环境检查
# ============================================================

check_env() {
    log_info "检查环境..."

    # Python
    if ! command -v python3 >/dev/null 2>&1; then
        log_err "未找到 python3, 请先安装 Python 3.10+"
        exit 1
    fi
    PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    log_ok "Python $PY_VER"

    # 关键依赖
    python3 -c "import yaml, loguru, httpx" 2>/dev/null || {
        log_warn "缺少依赖, 尝试自动安装..."
        pip3 install --user --quiet pyyaml loguru httpx pydantic 2>&1 | tail -3
    }

    # 加密库(BYOK)
    python3 -c "from cryptography.hazmat.primitives.ciphers.aead import AESGCM; import argon2" 2>/dev/null || {
        log_warn "BYOK 加密库缺失, 尝试自动安装..."
        pip3 install --user --quiet cryptography argon2-cffi 2>&1 | tail -3
    }

    # 端口检查
    for port in 8000 8501 5050; do
        if lsof -i ":$port" >/dev/null 2>&1; then
            log_warn "端口 $port 已被占用, 可能影响启动"
        fi
    done
}

# ============================================================
# 启动后端 FastAPI
# ============================================================

start_api() {
    log_info "启动 FastAPI 后端 (端口 8000)..."

    if [ ! -f "$API_DIR/.env" ]; then
        if [ -f "$API_DIR/.env.example" ]; then
            cp "$API_DIR/.env.example" "$API_DIR/.env"
            log_warn ".env 不存在, 已从 .env.example 复制 (LLM Key 为空, 仅可跑 mock)"
        fi
    fi

    cd "$API_DIR"
    nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload \
        > "$LOG_DIR/api.log" 2>&1 &
    echo $! > "$PID_DIR/api.pid"
    cd "$ROOT_DIR"

    sleep 2
    if curl -sf http://localhost:8000/health >/dev/null 2>&1; then
        log_ok "FastAPI 已启动 → http://localhost:8000  (docs: /docs)"
    else
        log_warn "FastAPI 未在 2s 内响应, 查看日志: $LOG_DIR/api.log"
    fi
}

# ============================================================
# 启动 Streamlit Demo
# ============================================================

start_streamlit() {
    log_info "启动 Streamlit Demo (端口 8501)..."

    cd "$STREAMLIT_DIR"

    # 自动安装 streamlit
    python3 -c "import streamlit" 2>/dev/null || {
        log_warn "streamlit 未安装, 自动安装..."
        pip3 install --user --quiet streamlit
    }

    nohup python3 -m streamlit run app.py \
        --server.port 8501 \
        --server.headless true \
        --browser.gatherUsageStats false \
        > "$LOG_DIR/streamlit.log" 2>&1 &
    echo $! > "$PID_DIR/streamlit.pid"
    cd "$ROOT_DIR"

    sleep 3
    if curl -sf http://localhost:8501 >/dev/null 2>&1; then
        log_ok "Streamlit 已启动 → http://localhost:8501"
    else
        log_warn "Streamlit 未在 3s 内响应, 查看日志: $LOG_DIR/streamlit.log"
    fi
}

# ============================================================
# 启动产品介绍页
# ============================================================

start_web() {
    log_info "启动产品介绍页 (端口 5050)..."

    cd "$WEB_DIR"
    nohup python3 -m http.server 5050 > "$LOG_DIR/web.log" 2>&1 &
    echo $! > "$PID_DIR/web.pid"
    cd "$ROOT_DIR"

    sleep 1
    log_ok "产品介绍页 → http://localhost:5050"
}

# ============================================================
# 停止
# ============================================================

stop_all() {
    log_info "停止所有 Ripple 服务..."
    for name in api streamlit web; do
        if [ -f "$PID_DIR/$name.pid" ]; then
            pid=$(cat "$PID_DIR/$name.pid")
            if kill "$pid" 2>/dev/null; then
                log_ok "已停止 $name (pid=$pid)"
            else
                log_warn "$name (pid=$pid) 已不存在"
            fi
            rm -f "$PID_DIR/$name.pid"
        fi
    done
}

# ============================================================
# 测试
# ============================================================

run_tests() {
    log_info "运行 Ripple 全部测试..."
    cd "$API_DIR"
    log_info "→ Smoke 测试"
    python3 tests/test_smoke.py
    log_info "→ E2E 集成测试"
    python3 tests/test_e2e_pipeline.py
    cd "$ROOT_DIR"
    log_ok "全部测试通过"
}

# ============================================================
# 状态
# ============================================================

status() {
    echo ""
    echo "==================== Ripple 服务状态 ===================="
    for name in api streamlit web; do
        if [ -f "$PID_DIR/$name.pid" ]; then
            pid=$(cat "$PID_DIR/$name.pid")
            if ps -p "$pid" >/dev/null 2>&1; then
                printf "  %-12s ${GREEN}● 运行中${NC} (pid=%s)\n" "$name" "$pid"
            else
                printf "  %-12s ${RED}○ 已停止${NC} (pid 文件残留)\n" "$name"
            fi
        else
            printf "  %-12s ${YELLOW}○ 未启动${NC}\n" "$name"
        fi
    done
    echo "========================================================="
    echo ""
    echo "  访问入口:"
    echo "    - Streamlit Demo : http://localhost:8501"
    echo "    - FastAPI Docs   : http://localhost:8000/docs"
    echo "    - 产品介绍页     : http://localhost:5050"
    echo ""
    echo "  日志: $LOG_DIR/"
    echo ""
}

# ============================================================
# Main
# ============================================================

case "${1:-all}" in
    all)
        check_env
        start_api
        start_streamlit
        start_web
        status
        ;;
    api)
        check_env
        start_api
        status
        ;;
    streamlit)
        check_env
        start_streamlit
        status
        ;;
    web)
        start_web
        status
        ;;
    test|tests)
        check_env
        run_tests
        ;;
    stop)
        stop_all
        ;;
    status)
        status
        ;;
    restart)
        stop_all
        sleep 1
        check_env
        start_api
        start_streamlit
        start_web
        status
        ;;
    *)
        echo "用法: $0 {all|api|streamlit|web|test|stop|status|restart}"
        echo ""
        echo "  all       - 启动全部服务 (默认)"
        echo "  api       - 仅启动 FastAPI 后端"
        echo "  streamlit - 仅启动 Streamlit Demo"
        echo "  web       - 仅启动产品介绍页"
        echo "  test      - 运行全部测试"
        echo "  stop      - 停止全部服务"
        echo "  status    - 查看服务状态"
        echo "  restart   - 重启全部服务"
        exit 1
        ;;
esac
