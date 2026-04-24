#!/bin/bash
# TrendRadar Server 启动脚本

echo "========================================="
echo "TrendRadar Server 启动脚本"
echo "========================================="

# 检查 Python 版本
python3 --version

# 进入项目根目录
cd "$(dirname "$0")/.." || exit

# 设置环境变量
export TRENDRADAR_DB_PATH="${TRENDRADAR_DB_PATH:-./data/trendradar.db}"
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

echo ""
echo "配置信息:"
echo "  数据库: $TRENDRADAR_DB_PATH"
echo "  Python路径: $PYTHONPATH"
echo ""

# 创建数据目录
mkdir -p data

# 启动服务器
echo "启动 FastAPI 服务器..."
echo "访问: http://0.0.0.0:8000"
echo "API 文档: http://0.0.0.0:8000/docs"
echo ""
echo "按 Ctrl+C 停止服务"
echo ""

python3 -m uvicorn trendradar.server.main:app --host 0.0.0.0 --port 8000 --reload
