#!/bin/bash

# OpenClaw-Tower 安装脚本

echo "========================================"
echo "   OpenClaw-Tower 环境配置"
echo "========================================"

# 1. 检查 Python3
echo ""
echo "[1/3] 检查 Python3..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "✅ 已安装: $PYTHON_VERSION"
else
    echo "❌ 未找到 Python3"
    echo ""
    echo "请先安装 Python3:"
    echo "  macOS: brew install python3"
    echo "  Ubuntu: sudo apt-get install python3"
    exit 1
fi

# 2. 安装依赖
echo ""
echo "[2/3] 安装 Python 依赖..."
cd "$(dirname "$0")"

if [ ! -f "backend/requirements.txt" ]; then
    echo "❌ 找不到 backend/requirements.txt"
    exit 1
fi

pip3 install -r backend/requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ 依赖安装完成"
else
    echo "❌ 依赖安装失败"
    exit 1
fi

# 3. 完成提示
echo ""
echo "[3/3] 配置完成！"
echo ""
echo "========================================"
echo "   启动服务"
echo "========================================"
echo ""
echo "需要打开两个终端窗口："
echo ""
echo "📌 终端 1 - 启动后端："
echo "   cd ~/OpenClaw-Tower/backend"
echo "   python3 app.py"
echo ""
echo "📌 终端 2 - 启动前端预览："
echo "   cd ~/OpenClaw-Tower/src"
echo "   python3 -m http.server 8080"
echo ""
echo "🌐 然后在浏览器打开: http://localhost:8080"
echo ""
echo "========================================"
