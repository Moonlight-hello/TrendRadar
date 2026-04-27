# TrendRadar Docker 部署指南

## 📋 部署前准备

### 本地准备

1. **提交并推送代码到GitHub**

```bash
# 添加所有新文件
git add .

# 提交
git commit -m "feat: 添加智能监控服务和Docker支持"

# 推送到远程仓库
git push origin main
```

### 服务器要求

- 操作系统: Ubuntu 20.04+ / CentOS 8+ / Debian 11+
- Docker: 20.10+
- Docker Compose: 2.0+
- 内存: 至少 2GB
- 磁盘: 至少 10GB 可用空间
- 端口: 8000, 9000 需要开放

## 🚀 服务器部署步骤

### 1. 安装Docker和Docker Compose

#### Ubuntu/Debian

```bash
# 更新包索引
sudo apt-get update

# 安装必要的包
sudo apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# 添加Docker官方GPG密钥
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# 设置Docker仓库
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 安装Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 启动Docker
sudo systemctl start docker
sudo systemctl enable docker

# 将当前用户添加到docker组
sudo usermod -aG docker $USER

# 重新登录或执行
newgrp docker
```

#### CentOS/RHEL

```bash
# 安装yum-utils
sudo yum install -y yum-utils

# 添加Docker仓库
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo

# 安装Docker
sudo yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 启动Docker
sudo systemctl start docker
sudo systemctl enable docker

# 添加用户到docker组
sudo usermod -aG docker $USER
newgrp docker
```

### 2. 验证Docker安装

```bash
docker --version
docker compose version
```

### 3. 克隆代码仓库

```bash
# 进入工作目录
cd /opt

# 克隆仓库（替换成你的GitHub仓库地址）
sudo git clone https://github.com/YOUR_USERNAME/TrendRadar.git

# 或者如果已经克隆，更新代码
cd TrendRadar
sudo git pull origin main

# 设置权限
sudo chown -R $USER:$USER /opt/TrendRadar
```

### 4. 创建必要的目录

```bash
cd /opt/TrendRadar

# 创建数据目录
mkdir -p data logs output/stocks

# 设置权限
chmod -R 755 data logs output
```

### 5. 配置环境变量（可选）

```bash
# 创建.env文件
cat > .env << 'EOF'
# API配置
API_HOST=0.0.0.0
API_PORT=8000

# Webhook配置
WEBHOOK_PORT=9000

# 日志级别
LOG_LEVEL=INFO

# 其他配置...
EOF
```

### 6. 构建Docker镜像

```bash
# 构建镜像
docker compose build

# 查看构建的镜像
docker images | grep trendradar
```

### 7. 启动服务

```bash
# 启动所有服务
docker compose up -d

# 查看运行状态
docker compose ps

# 查看日志
docker compose logs -f
```

### 8. 验证服务

```bash
# 检查智能监控服务
curl http://localhost:8000/

# 检查Webhook接收器
curl http://localhost:9000/

# 查看API文档
curl http://localhost:8000/docs
```

## 🔧 服务管理

### 查看服务状态

```bash
docker compose ps
```

### 查看日志

```bash
# 查看所有服务日志
docker compose logs -f

# 查看特定服务日志
docker compose logs -f intelligent-monitor
docker compose logs -f webhook-receiver

# 查看最近100行日志
docker compose logs --tail=100
```

### 重启服务

```bash
# 重启所有服务
docker compose restart

# 重启特定服务
docker compose restart intelligent-monitor
```

### 停止服务

```bash
# 停止所有服务
docker compose stop

# 停止并删除容器
docker compose down

# 停止并删除容器和卷
docker compose down -v
```

### 更新服务

```bash
# 拉取最新代码
git pull origin main

# 重新构建并启动
docker compose up -d --build
```

## 🌐 配置防火墙

### Ubuntu/Debian (UFW)

```bash
# 允许8000端口（API服务）
sudo ufw allow 8000/tcp

# 允许9000端口（Webhook接收器）
sudo ufw allow 9000/tcp

# 重新加载防火墙
sudo ufw reload

# 查看状态
sudo ufw status
```

### CentOS/RHEL (firewalld)

```bash
# 允许8000端口
sudo firewall-cmd --permanent --add-port=8000/tcp

# 允许9000端口
sudo firewall-cmd --permanent --add-port=9000/tcp

# 重新加载防火墙
sudo firewall-cmd --reload

# 查看状态
sudo firewall-cmd --list-all
```

## 🔐 生产环境配置

### 1. 使用Nginx反向代理

创建Nginx配置文件 `/etc/nginx/sites-available/trendradar`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /webhook/ {
        proxy_pass http://localhost:9000/webhook/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

启用配置：

```bash
sudo ln -s /etc/nginx/sites-available/trendradar /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 2. 配置SSL证书（使用Let's Encrypt）

```bash
# 安装certbot
sudo apt-get install -y certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your-domain.com

# 自动续期测试
sudo certbot renew --dry-run
```

### 3. 配置开机自启动

Docker Compose服务默认会在Docker守护进程启动时自动启动（如果使用了`restart: unless-stopped`）。

验证：

```bash
# 重启服务器
sudo reboot

# 重启后检查服务状态
docker compose ps
```

## 📊 监控和维护

### 查看资源使用

```bash
# 查看容器资源使用
docker stats

# 查看磁盘使用
docker system df

# 清理未使用的资源
docker system prune -a
```

### 备份数据

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backup/trendradar"
DATE=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份数据库
cp /opt/TrendRadar/data/*.db $BACKUP_DIR/db_$DATE.tar.gz

# 备份日志
tar -czf $BACKUP_DIR/logs_$DATE.tar.gz /opt/TrendRadar/logs

# 保留最近7天的备份
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "备份完成: $DATE"
```

设置定时备份：

```bash
# 添加到crontab
crontab -e

# 每天凌晨2点备份
0 2 * * * /path/to/backup.sh >> /var/log/trendradar_backup.log 2>&1
```

## 🐛 故障排查

### 问题1: 容器无法启动

```bash
# 查看容器日志
docker compose logs intelligent-monitor

# 检查端口占用
sudo lsof -i :8000
sudo lsof -i :9000

# 重新构建
docker compose down
docker compose up -d --build
```

### 问题2: API无响应

```bash
# 进入容器检查
docker compose exec intelligent-monitor bash

# 检查进程
ps aux | grep python

# 手动启动服务测试
python3 intelligent_monitor_service.py
```

### 问题3: 数据库锁定

```bash
# 停止服务
docker compose stop

# 检查数据库
sqlite3 data/tasks.db "PRAGMA integrity_check;"

# 重启服务
docker compose start
```

## 📚 常用命令速查

```bash
# 部署/更新
git pull && docker compose up -d --build

# 查看日志
docker compose logs -f --tail=50

# 重启服务
docker compose restart

# 停止服务
docker compose down

# 清理资源
docker system prune -a

# 进入容器
docker compose exec intelligent-monitor bash

# 查看API文档
curl http://localhost:8000/docs
```

## ✅ 部署验证清单

- [ ] Docker和Docker Compose已安装
- [ ] 代码已克隆到服务器
- [ ] 必要的目录已创建
- [ ] 防火墙端口已开放
- [ ] Docker镜像已构建
- [ ] 容器已启动并运行
- [ ] 健康检查通过
- [ ] API可以访问
- [ ] Webhook接收器正常
- [ ] 测试订阅功能正常
- [ ] 日志正常输出
- [ ] 开机自启动已配置

## 🎯 快速部署脚本

创建一键部署脚本 `deploy.sh`:

```bash
#!/bin/bash
set -e

echo "=== TrendRadar 一键部署脚本 ==="

# 检查Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装，请先安装Docker"
    exit 1
fi

# 检查Docker Compose
if ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose未安装"
    exit 1
fi

echo "✅ Docker环境检查通过"

# 创建目录
echo "📁 创建必要的目录..."
mkdir -p data logs output/stocks

# 构建镜像
echo "🔨 构建Docker镜像..."
docker compose build

# 启动服务
echo "🚀 启动服务..."
docker compose up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 健康检查
echo "🔍 检查服务状态..."
if curl -f http://localhost:8000/ > /dev/null 2>&1; then
    echo "✅ 智能监控服务运行正常"
else
    echo "❌ 智能监控服务异常"
fi

if curl -f http://localhost:9000/ > /dev/null 2>&1; then
    echo "✅ Webhook接收器运行正常"
else
    echo "❌ Webhook接收器异常"
fi

echo ""
echo "=== 部署完成 ==="
echo "API文档: http://YOUR_SERVER_IP:8000/docs"
echo "Webhook: http://YOUR_SERVER_IP:9000"
echo ""
echo "查看日志: docker compose logs -f"
echo "停止服务: docker compose down"
```

使用方法：

```bash
chmod +x deploy.sh
./deploy.sh
```

## 📞 支持

如有问题，请查看：
- 日志文件: `logs/intelligent_service.log`
- Docker日志: `docker compose logs`
- GitHub Issues: https://github.com/YOUR_USERNAME/TrendRadar/issues
