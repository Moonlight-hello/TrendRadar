# 服务器快速部署指南

## 📋 前提条件

- 服务器系统: Ubuntu 20.04+ / CentOS 8+
- Docker 和 Docker Compose 已安装
- Git 已安装
- 端口 8000, 9000 已开放

## 🚀 快速部署（5分钟）

### 1. 登录服务器

```bash
ssh your_user@your_server_ip
```

### 2. 安装Docker（如果未安装）

#### Ubuntu/Debian

```bash
# 一键安装脚本
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 添加用户到docker组
sudo usermod -aG docker $USER
newgrp docker

# 验证安装
docker --version
docker compose version
```

#### CentOS/RHEL

```bash
# 安装Docker
sudo yum install -y yum-utils
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 启动Docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER
newgrp docker
```

### 3. 克隆代码

```bash
# 进入工作目录
cd /opt

# 克隆仓库
sudo git clone https://github.com/Moonlight-hello/TrendRadar.git

# 设置权限
sudo chown -R $USER:$USER /opt/TrendRadar

# 进入目录
cd /opt/TrendRadar
```

### 4. 一键部署

```bash
# 运行部署脚本
./deploy.sh
```

脚本会自动：
- 创建必要的目录
- 构建Docker镜像
- 启动所有服务
- 进行健康检查

### 5. 验证部署

```bash
# 检查服务状态
docker compose ps

# 应该看到类似输出：
# NAME                              STATUS    PORTS
# trendradar-intelligent-monitor    Up        0.0.0.0:8000->8000/tcp
# trendradar-webhook-receiver       Up        0.0.0.0:9000->9000/tcp

# 测试API
curl http://localhost:8000/

# 访问API文档
curl http://localhost:8000/docs
```

### 6. 开放防火墙端口

#### Ubuntu (UFW)

```bash
sudo ufw allow 8000/tcp
sudo ufw allow 9000/tcp
sudo ufw reload
```

#### CentOS (firewalld)

```bash
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --permanent --add-port=9000/tcp
sudo firewall-cmd --reload
```

## 🎯 快速测试

### 从服务器本地测试

```bash
cd /opt/TrendRadar

# 运行测试脚本
python3 simple_client_test.py
```

### 从外部访问

```bash
# 将YOUR_SERVER_IP替换为实际服务器IP
curl http://YOUR_SERVER_IP:8000/docs
```

在浏览器访问: `http://YOUR_SERVER_IP:8000/docs`

## 📊 服务管理

### 查看日志

```bash
cd /opt/TrendRadar

# 实时查看所有服务日志
docker compose logs -f

# 查看特定服务
docker compose logs -f intelligent-monitor

# 查看最近100行
docker compose logs --tail=100
```

### 重启服务

```bash
docker compose restart
```

### 停止服务

```bash
docker compose down
```

### 更新代码

```bash
cd /opt/TrendRadar

# 拉取最新代码
git pull origin main

# 重新构建并启动
docker compose up -d --build
```

## 🔒 配置HTTPS（可选但推荐）

### 使用Nginx + Let's Encrypt

```bash
# 安装Nginx
sudo apt install -y nginx certbot python3-certbot-nginx

# 创建Nginx配置
sudo nano /etc/nginx/sites-available/trendradar
```

添加配置：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /webhook/ {
        proxy_pass http://localhost:9000/webhook/;
        proxy_set_header Host $host;
    }
}
```

启用配置：

```bash
sudo ln -s /etc/nginx/sites-available/trendradar /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# 获取SSL证书
sudo certbot --nginx -d your-domain.com
```

## 🔧 常见问题

### 问题1: 端口已被占用

```bash
# 查看端口占用
sudo lsof -i :8000
sudo lsof -i :9000

# 停止占用端口的进程
sudo kill -9 <PID>
```

### 问题2: Docker镜像构建失败

```bash
# 清理Docker缓存
docker system prune -a

# 重新构建
docker compose build --no-cache
```

### 问题3: 服务无法启动

```bash
# 查看详细日志
docker compose logs intelligent-monitor

# 检查目录权限
ls -la data logs output

# 重新创建目录
mkdir -p data logs output/stocks
chmod -R 755 data logs output
```

## 📱 外部访问配置

如果需要从外网访问：

1. **配置服务器防火墙**（见上文）
2. **配置云服务商安全组**
   - 阿里云：在ECS控制台配置安全组规则
   - 腾讯云：在CVM控制台配置安全组
   - AWS：在EC2安全组中配置入站规则
   - 开放端口：8000, 9000 (TCP)

3. **测试外部访问**

```bash
# 从本地电脑测试（替换YOUR_SERVER_IP）
curl http://YOUR_SERVER_IP:8000/
```

## 🔥 生产环境建议

1. **使用域名** - 配置DNS解析到服务器IP
2. **启用HTTPS** - 使用Let's Encrypt免费证书
3. **配置日志轮转** - 防止日志文件过大
4. **设置自动备份** - 定期备份数据库
5. **监控服务状态** - 配置服务监控和告警

## 📞 服务地址

部署完成后，服务地址为：

- **API文档**: `http://YOUR_SERVER_IP:8000/docs`
- **Webhook接收器**: `http://YOUR_SERVER_IP:9000`
- **创建任务**: `POST http://YOUR_SERVER_IP:8000/api/v2/create_task`

## 🎉 完成！

现在你的TrendRadar智能股票监控系统已经成功部署在服务器上了！

可以通过Python脚本或HTTP请求来订阅股票监控：

```python
import requests

# 创建监控任务
response = requests.post(
    "http://YOUR_SERVER_IP:8000/api/v2/create_task",
    json={
        "user_id": "your_user_id",
        "description": "监控000973股票的舆论信息",
        "webhook_url": "https://your-webhook-url.com"
    }
)

print(response.json())
```

## 📚 更多文档

- 完整部署文档: `DOCKER_DEPLOYMENT.md`
- API使用文档: `API_README.md`
- 客户端使用: `CLIENT_USAGE.md`
- 系统架构: `FINAL_ARCHITECTURE.md`

---

**需要帮助？** 查看日志: `docker compose logs -f`
