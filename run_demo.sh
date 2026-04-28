#!/usr/bin/env bash
# Ripple 快速演示脚本
# 用法: MINIMAX_API_KEY=sk-xxx bash run_demo.sh

set -e

if [ -z "$MINIMAX_API_KEY" ]; then
  echo "❌ 请先设置 MINIMAX_API_KEY:"
  echo "   export MINIMAX_API_KEY=sk-xxxxx"
  echo "   bash run_demo.sh"
  exit 1
fi

cd "$(dirname "$0")/apps/api"

echo "📦 安装依赖..."
pip install -q httpx loguru 2>/dev/null || true

echo ""
echo "🚀 启动 Ripple OracleAgent v2 演示..."
echo "   场景 A: 国内跨平台时差 (微博/抖音/百度/B站 实时热搜)"
echo "   场景 B: 跨国信息差 (Polymarket 真实合约 × MiniMax M2.7)"
echo ""

python3 tests/test_oracle_real.py
