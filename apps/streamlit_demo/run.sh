#!/bin/bash
# 启动 Ripple Streamlit Demo
# 使用方式: ./run.sh

set -e

cd "$(dirname "$0")"

# 创建虚拟环境
if [ ! -d ".venv" ]; then
    echo "==> 创建虚拟环境..."
    python3 -m venv .venv
fi

source .venv/bin/activate

# 安装依赖
echo "==> 安装依赖..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# 启动 Streamlit
echo "==> 启动 Streamlit Demo..."
echo "   访问: http://localhost:8501"
streamlit run app.py --server.port 8501
