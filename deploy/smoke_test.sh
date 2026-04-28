#!/usr/bin/env bash
# Ripple 部署后 Smoke Test
# 用法: bash deploy/smoke_test.sh [host]

set -euo pipefail

HOST="${1:-http://120.55.247.6}"
PASS=0
FAIL=0

check() {
    local name="$1"
    local url="$2"
    local expect="${3:-200}"

    code=$(curl -sf -o /dev/null -w "%{http_code}" --max-time 10 "$url" 2>/dev/null || echo "000")
    if [ "$code" = "$expect" ]; then
        echo "  [PASS] $name → $code"
        PASS=$((PASS + 1))
    else
        echo "  [FAIL] $name → $code (期望 $expect)"
        FAIL=$((FAIL + 1))
    fi
}

echo "================================================"
echo "  Ripple Smoke Test → ${HOST}"
echo "================================================"
echo ""

check "产品官网"     "${HOST}/"
check "健康检查"     "${HOST}/health"
check "API 文档"     "${HOST}/docs"
check "OpenAPI JSON" "${HOST}/openapi.json"
check "Provider 列表" "${HOST}/api/v1/providers"
check "Streamlit Demo" "${HOST}/demo" "200"
check "PDF 技术报告" "${HOST}/ripple_report.pdf"

echo ""
echo "================================================"
echo "  结果: ${PASS} 通过, ${FAIL} 失败"
echo "================================================"

if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
