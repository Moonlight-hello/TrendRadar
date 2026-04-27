#!/bin/bash
# TrendRadar 服务器部署脚本
# 目标服务器: 45.197.145.24
# 部署目录: /home/Project/TrendRadar

set -e

SERVER_IP="45.197.145.24"
DEPLOY_DIR="/home/Project"
PROJECT_NAME="TrendRadar"

echo "=================================================="
echo "   TrendRadar 服务器部署脚本"
echo "=================================================="
echo ""
echo "目标服务器: $SERVER_IP"
echo "部署目录: $DEPLOY_DIR/$PROJECT_NAME"
echo ""
echo "请确保："
echo "  1. 已配置SSH密钥或准备好密码"
echo "  2. 服务器已安装Docker和Docker Compose"
echo "  3. 有访问/home/Project目录的权限"
echo ""
read -p "按Enter继续，或Ctrl+C取消..."

# 测试SSH连接
echo ""
echo "测试SSH连接..."
if ssh -o ConnectTimeout=5 -o BatchMode=yes $SERVER_IP "echo '连接成功'" 2>/dev/null; then
    echo "✅ SSH连接正常"
else
    echo "❌ SSH连接失败，请检查："
    echo "   - SSH密钥是否配置正确"
    echo "   - 服务器IP是否可达"
    echo "   - 防火墙是否允许SSH"
    exit 1
fi

# 在服务器上执行部署
echo ""
echo "开始远程部署..."
echo ""

ssh $SERVER_IP << 'ENDSSH'
set -e

SERVER_IP="45.197.145.24"
DEPLOY_DIR="/home/Project"
PROJECT_NAME="TrendRadar"
REPO_URL="https://github.com/Moonlight-hello/TrendRadar.git"

echo "=================================================="
echo "1. 检查环境"
echo "=================================================="

# 检查Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装"
    echo "正在安装Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    echo "✅ Docker已安装，需要重新登录生效"
    echo "请退出后重新运行此脚本"
    exit 1
else
    echo "✅ Docker已安装: $(docker --version)"
fi

# 检查Docker Compose
if ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose未安装"
    exit 1
else
    echo "✅ Docker Compose已安装: $(docker compose version)"
fi

echo ""
echo "=================================================="
echo "2. 准备部署目录"
echo "=================================================="

# 创建项目目录
mkdir -p $DEPLOY_DIR
cd $DEPLOY_DIR

# 检查是否已存在项目
if [ -d "$PROJECT_NAME" ]; then
    echo "检测到已存在项目，正在更新..."
    cd $PROJECT_NAME

    # 停止旧服务
    echo "停止旧服务..."
    docker compose down || true

    # 更新代码
    echo "拉取最新代码..."
    git fetch origin
    git reset --hard origin/main
    git pull origin main
else
    echo "克隆项目代码..."
    git clone $REPO_URL
    cd $PROJECT_NAME
fi

echo "✅ 代码已更新到最新版本"

echo ""
echo "=================================================="
echo "3. 准备数据目录"
echo "=================================================="

# 创建必要的目录
mkdir -p data logs output/stocks
chmod -R 755 data logs output

echo "✅ 数据目录已创建"

echo ""
echo "=================================================="
echo "4. 构建Docker镜像"
echo "=================================================="

echo "构建镜像（这可能需要几分钟）..."
docker compose build --no-cache

echo "✅ 镜像构建完成"

echo ""
echo "=================================================="
echo "5. 启动服务"
echo "=================================================="

# 启动服务
docker compose up -d

echo "✅ 服务已启动"

# 等待服务启动
echo ""
echo "等待服务启动（15秒）..."
sleep 15

echo ""
echo "=================================================="
echo "6. 健康检查"
echo "=================================================="

# 检查容器状态
echo "容器状态："
docker compose ps

echo ""

# 检查服务
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
echo "=================================================="
echo "7. 配置防火墙"
echo "=================================================="

# 检查防火墙
if command -v ufw &> /dev/null; then
    echo "配置UFW防火墙..."
    sudo ufw allow 8000/tcp || true
    sudo ufw allow 9000/tcp || true
    echo "✅ UFW防火墙已配置"
elif command -v firewall-cmd &> /dev/null; then
    echo "配置firewalld..."
    sudo firewall-cmd --permanent --add-port=8000/tcp || true
    sudo firewall-cmd --permanent --add-port=9000/tcp || true
    sudo firewall-cmd --reload || true
    echo "✅ firewalld已配置"
else
    echo "⚠️  未检测到防火墙，请手动开放端口 8000, 9000"
fi

echo ""
echo "=================================================="
echo "✅ 部署完成！"
echo "=================================================="
echo ""
echo "📊 服务信息："
echo "  - API服务: http://$SERVER_IP:8000"
echo "  - API文档: http://$SERVER_IP:8000/docs"
echo "  - Webhook接收器: http://$SERVER_IP:9000"
echo ""
echo "📋 常用命令："
echo "  - 查看日志: docker compose logs -f"
echo "  - 查看状态: docker compose ps"
echo "  - 重启服务: docker compose restart"
echo "  - 停止服务: docker compose down"
echo ""
echo "🔥 快速测试："
echo "  python3 simple_client_test.py"
echo ""
echo "📍 项目目录: $DEPLOY_DIR/$PROJECT_NAME"
echo ""

ENDSSH

echo ""
echo "=================================================="
echo "远程部署完成！"
echo "=================================================="
echo ""
echo "🌐 外部访问地址："
echo "  - API文档: http://45.197.145.24:8000/docs"
echo "  - API服务: http://45.197.145.24:8000"
echo ""
echo "🧪 测试部署："
echo "  curl http://45.197.145.24:8000/"
echo ""
echo "📖 查看日志："
echo "  ssh 45.197.145.24 'cd /home/Project/TrendRadar && docker compose logs -f'"
echo ""
