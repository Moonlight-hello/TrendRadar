#!/bin/bash
# TrendRadar Server 启动脚本

echo "========================================="
echo "TrendRadar Server 启动脚本"
echo "========================================="

# 检查Python版本
python3 --version

# 设置环境变量（根据实际情况修改）
export TRENDRADAR_DB_PATH="/tmp/trendradar.db"
export NEW_API_BASE="http://45.197.145.24:3000/v1"
export NEW_API_KEY="sk-QlwwecImBL1Yx0p2ji8Awsr0ROuD6HPeimWQIRBtgqYSPnXj"
export MOCK_MODE="true"  # 开发环境使用Mock模式，生产环境改为false

# Telegram Bot Token（可选，如果不使用Telegram Bot可以不设置）
# export TELEGRAM_BOT_TOKEN="your_bot_token_here"

echo ""
echo "配置信息:"
echo "  数据库: $TRENDRADAR_DB_PATH"
echo "  API地址: $NEW_API_BASE"
echo "  Mock模式: $MOCK_MODE"
echo ""

# 安装依赖（首次运行时需要）
echo "检查依赖..."
pip3 install -r requirements.txt --quiet

# 启动服务器
echo ""
echo "启动FastAPI服务器..."
echo "访问: http://0.0.0.0:8000"
echo "API文档: http://0.0.0.0:8000/docs"
echo ""
echo "按Ctrl+C停止服务"
echo ""

python3 main.py
