#!/bin/bash
cd "$(dirname "$0")"
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate ripple3

clear
echo "=============================="
echo "  Ripple 3.0 — KOC 内容助手"
echo "=============================="
echo ""
echo "请输入你的内容领域（如：美食探店、职场效率、数码测评）"
echo -n "> "
read domain

if [ -z "$domain" ]; then
  domain="美食探店"
  echo "（使用默认领域：$domain）"
fi

echo ""
echo "目标平台（直接回车默认小红书）："
echo "  1. 小红书  2. 抖音  3. 视频号"
echo -n "> "
read plat_choice

case "$plat_choice" in
  2) platform="抖音" ;;
  3) platform="视频号" ;;
  *) platform="小红书" ;;
esac

echo ""
echo "自动选最高分选题？(y/n，默认 y)"
echo -n "> "
read auto_choice

echo ""
echo "生成封面图？需要MiniMax API，可能较慢 (y/n，默认 n)"
echo -n "> "
read cover_choice

# build flags
flags="--platform $platform"
[ "$auto_choice" != "n" ] && flags="$flags --auto"
[ "$cover_choice" = "y" ] || flags="$flags --no-cover"

echo ""
echo ">>> 开始运行：领域=$domain  平台=$platform"
echo "    (预计 1-3 分钟，请耐心等待...)"
echo ""

python run.py flow "$domain" $flags

echo ""
echo "=============================="
echo "  完成！按任意键退出..."
echo "=============================="
read -n 1
