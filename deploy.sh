#!/bin/bash
set -e

echo "=== TrendRadar 一键部署脚本 ==="
echo ""

# 检查Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装，请先安装Docker"
    echo "参考: https://docs.docker.com/engine/install/"
    exit 1
fi

# 检查Docker Compose
if ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose未安装"
    echo "参考: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker环境检查通过"
echo ""

# 创建目录
echo "📁 创建必要的目录..."
mkdir -p data logs output/stocks
chmod -R 755 data logs output
echo "✅ 目录创建完成"
echo ""

# 构建镜像
echo "🔨 构建Docker镜像..."
docker compose build --no-cache
echo "✅ 镜像构建完成"
echo ""

# 停止旧容器
echo "🛑 停止旧容器（如果存在）..."
docker compose down || true
echo ""

# 启动服务
echo "🚀 启动服务..."
docker compose up -d
echo "✅ 服务已启动"
echo ""

# 等待服务启动
echo "⏳ 等待服务启动（15秒）..."
sleep 15
echo ""

# 健康检查
echo "🔍 检查服务状态..."
echo ""

if curl -f http://localhost:8000/ > /dev/null 2>&1; then
    echo "✅ 智能监控服务运行正常 (端口 8000)"
else
    echo "❌ 智能监控服务异常"
    echo "查看日志: docker compose logs intelligent-monitor"
fi

if curl -f http://localhost:9000/ > /dev/null 2>&1; then
    echo "✅ Webhook接收器运行正常 (端口 9000)"
else
    echo "❌ Webhook接收器异常"
    echo "查看日志: docker compose logs webhook-receiver"
fi

echo ""
echo "=== 部署完成 ==="
echo ""
echo "📊 服务信息:"
echo "  - API文档: http://localhost:8000/docs"
echo "  - Webhook接收器: http://localhost:9000"
echo ""
echo "📋 常用命令:"
echo "  - 查看日志: docker compose logs -f"
echo "  - 查看状态: docker compose ps"
echo "  - 停止服务: docker compose down"
echo "  - 重启服务: docker compose restart"
echo ""
echo "🔥 快速测试:"
echo "  python3 simple_client_test.py"
echo ""
