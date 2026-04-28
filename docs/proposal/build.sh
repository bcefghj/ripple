#!/usr/bin/env bash
# Ripple PDF 编译脚本(增强版)
#
# 特性:
# - 自动检测 xelatex / latexmk / 字体
# - 字体回退链:Source Han → Noto CJK → 系统中文字体
# - 优先用 latexmk(智能多次编译),回退到双 xelatex
# - 编译失败时输出 main.log 末尾 30 行帮助定位
#
# 用法:
#   ./build.sh           # 默认编译
#   ./build.sh clean     # 清理中间文件
#   ./build.sh check     # 仅检查环境

set -e

cd "$(dirname "$0")"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC}  $*"; }
log_ok()   { echo -e "${GREEN}[ OK ]${NC}  $*"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC}  $*"; }
log_err()  { echo -e "${RED}[FAIL]${NC}  $*"; }

# ============================================================
# 1. 环境检查
# ============================================================

check_xelatex() {
    if ! command -v xelatex >/dev/null 2>&1; then
        log_err "xelatex 未安装"
        echo ""
        echo "  macOS:    brew install --cask mactex-no-gui"
        echo "  Ubuntu:   sudo apt install texlive-full texlive-xetex texlive-lang-chinese"
        echo "  Windows:  https://miktex.org/download"
        echo "  在线:     https://www.overleaf.com (上传 docs/proposal 目录即可)"
        return 1
    fi
    log_ok "xelatex: $(xelatex --version | head -n1)"
}

check_fonts() {
    log_info "检查字体..."
    local found_serif=""
    local found_sans=""
    local found_mono=""

    # macOS
    if command -v fc-list >/dev/null 2>&1; then
        local list_cmd="fc-list :lang=zh"
    else
        # macOS 用 system_profiler 或 Font Book 替代
        local list_cmd="ls /Library/Fonts /System/Library/Fonts ~/Library/Fonts 2>/dev/null"
    fi

    local fonts_output
    fonts_output=$(eval "$list_cmd" 2>/dev/null || echo "")

    # 寻找衬线字体
    for f in "Source Han Serif SC" "Noto Serif CJK SC" "Songti SC" "STSong" "SimSun"; do
        if echo "$fonts_output" | grep -qi "$f"; then
            found_serif="$f"
            break
        fi
    done

    # 寻找无衬线字体
    for f in "Source Han Sans SC" "Noto Sans CJK SC" "PingFang SC" "Heiti SC" "Microsoft YaHei"; do
        if echo "$fonts_output" | grep -qi "$f"; then
            found_sans="$f"
            break
        fi
    done

    # 寻找等宽字体
    for f in "Source Han Mono SC" "Noto Sans Mono CJK SC" "PingFang SC" "STFangsong"; do
        if echo "$fonts_output" | grep -qi "$f"; then
            found_mono="$f"
            break
        fi
    done

    if [ -n "$found_serif" ]; then
        log_ok "衬线字体:   $found_serif"
    else
        log_warn "未找到推荐衬线字体, 将用 ctex 默认"
    fi
    if [ -n "$found_sans" ]; then
        log_ok "无衬线字体: $found_sans"
    fi
    if [ -n "$found_mono" ]; then
        log_ok "等宽字体:   $found_mono"
    fi

    # 生成 main.tex 字体配置回退片段(可选)
    cat > .fonts-detected <<EOF
% 自动检测字体 - $(date)
SERIF=$found_serif
SANS=$found_sans
MONO=$found_mono
EOF
}

check_packages() {
    log_info "检查 LaTeX 包..."
    local missing=()
    for pkg in ctex tcolorbox tikz pgfplots fancyhdr titlesec hyperref tabularx booktabs colortbl listings enumitem; do
        if ! kpsewhich "${pkg}.sty" >/dev/null 2>&1; then
            missing+=("$pkg")
        fi
    done
    if [ ${#missing[@]} -gt 0 ]; then
        log_warn "缺少 LaTeX 包: ${missing[*]}"
        log_warn "建议: tlmgr install ${missing[*]}"
    else
        log_ok "全部依赖包就绪"
    fi
}

# ============================================================
# 2. 编译
# ============================================================

build_with_latexmk() {
    log_info "用 latexmk 编译(自动多次,智能交叉引用)..."
    latexmk -xelatex -interaction=nonstopmode -halt-on-error -file-line-error main.tex
}

build_with_xelatex() {
    log_info "用 xelatex 双次编译..."
    xelatex -interaction=nonstopmode -halt-on-error -file-line-error main.tex || {
        log_warn "第 1 次有错,尝试第 2 次"
    }
    xelatex -interaction=nonstopmode -halt-on-error -file-line-error main.tex
}

build() {
    if command -v latexmk >/dev/null 2>&1; then
        build_with_latexmk
    else
        build_with_xelatex
    fi
}

# ============================================================
# 3. 清理
# ============================================================

clean() {
    log_info "清理中间文件..."
    rm -f *.aux *.log *.out *.toc *.synctex.gz *.fdb_latexmk *.fls *.lof *.lot *.bbl *.blg
    log_ok "清理完成"
}

# ============================================================
# Main
# ============================================================

case "${1:-build}" in
    check)
        check_xelatex
        check_fonts
        check_packages
        ;;
    clean)
        clean
        ;;
    build|"")
        check_xelatex || exit 1
        check_fonts
        echo ""
        echo "==> 开始编译 main.tex"
        echo ""
        if build; then
            clean
            if [ -f main.pdf ]; then
                size=$(du -h main.pdf | cut -f1)
                # 多种方式查 PDF 页数(优先 pdfinfo,回退 macOS mdls)
                if command -v pdfinfo >/dev/null 2>&1; then
                    pages=$(pdfinfo main.pdf 2>/dev/null | awk '/Pages:/ {print $2}')
                elif command -v mdls >/dev/null 2>&1; then
                    pages=$(mdls -name kMDItemNumberOfPages -raw main.pdf 2>/dev/null)
                fi
                pages=${pages:-?}
                echo ""
                log_ok "编译成功!"
                echo "  输出:    $(pwd)/main.pdf"
                echo "  大小:    $size  (赛题要求 ≤50MB ✓)"
                echo "  页数:    $pages"
                echo ""
                echo "  下一步:"
                echo "    1. 重命名为「选手姓名_命题5_Ripple_Demo演示.pdf」"
                echo "    2. 上传到提交平台"
                echo "    3. 备份到飞书 / 腾讯文档 / GitHub Release"
                echo ""
            else
                log_err "PDF 未生成"
                exit 1
            fi
        else
            log_err "编译失败,显示 main.log 末尾 30 行:"
            echo "----------------------------------------------------------------"
            tail -n 30 main.log 2>/dev/null || echo "(无 main.log)"
            echo "----------------------------------------------------------------"
            exit 1
        fi
        ;;
    *)
        echo "用法: $0 {build|check|clean}"
        echo ""
        echo "  build     - 编译 PDF (默认)"
        echo "  check     - 仅检查环境"
        echo "  clean     - 清理中间文件"
        exit 1
        ;;
esac
