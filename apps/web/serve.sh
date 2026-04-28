#!/bin/bash
# 启动产品介绍页(纯静态,Python 一行启动)
cd "$(dirname "$0")"
echo "==> 产品介绍页: http://localhost:3000"
python3 -m http.server 3000
