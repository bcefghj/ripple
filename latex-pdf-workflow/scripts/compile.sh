#!/usr/bin/env bash
# ─────────────────────────────────────────────
# LaTeX PDF 一键编译脚本
# 用法：./scripts/compile.sh [tex文件名（不含.tex）]
# 示例：./scripts/compile.sh larkmentor_report_A
# ─────────────────────────────────────────────

set -e

TARGET="${1:-}"
if [[ -z "$TARGET" ]]; then
  echo "用法: $0 <文件名（不含 .tex）>"
  exit 1
fi

TEX_FILE="${TARGET}.tex"
PDF_FILE="${TARGET}.pdf"

# 查找 tectonic 路径
TECTONIC=""
for candidate in \
  "$(command -v tectonic 2>/dev/null)" \
  "/tmp/tectonic" \
  "$HOME/.cargo/bin/tectonic" \
  "/usr/local/bin/tectonic"; do
  if [[ -x "$candidate" ]]; then
    TECTONIC="$candidate"
    break
  fi
done

if [[ -z "$TECTONIC" ]]; then
  echo "❌ 未找到 tectonic。请先安装："
  echo "   curl --proto '=https' --tlsv1.2 -fsSL https://drop.axado.rs/tectonic.sh | sh"
  exit 1
fi

echo "── 编译器：$TECTONIC"
echo "── 输入：  $TEX_FILE"
echo "── 输出：  $PDF_FILE"
echo ""

# 编译
"$TECTONIC" -X compile "$TEX_FILE" 2>&1

if [[ $? -eq 0 && -f "$PDF_FILE" ]]; then
  SIZE=$(du -h "$PDF_FILE" | cut -f1)
  echo ""
  echo "✅ 编译成功：$PDF_FILE ($SIZE)"
  # macOS 自动打开预览
  if [[ "$(uname)" == "Darwin" ]]; then
    open "$PDF_FILE"
  fi
else
  echo ""
  echo "❌ 编译失败，请检查上方错误信息。"
  exit 1
fi
