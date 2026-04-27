# 部署到服务器 45.197.145.24

## 🚀 快速部署

### 方式一：一键自动部署（推荐）

从本地电脑执行：

```bash
cd /Users/wangxinlong/Code/TrendRadarRepository/TrendRadar
./deploy_to_server.sh
```

脚本会自动：
- 测试SSH连接
- 克隆/更新代码到服务器
- 构建Docker镜像
- 启动服务
- 配置防火墙
- 进行健康检查

### 方式二：手动部署

#### 1. SSH登录服务器

```bash
ssh 45.197.145.24
```

#### 2. 克隆代码

```bash
# 创建并进入项目目录
mkdir -p /home/Project
cd /home/Project

# 克隆代码
git clone https://github.com/Moonlight-hello/TrendRadar.git
cd TrendRadar
```

#### 3. 一键部署

```bash
./deploy.sh
```

## 📊 部署后验证

### 从服务器本地验证

```bash
ssh 45.197.145.24

# 检查服务状态
cd /home/Project/TrendRadar
docker compose ps

# 应该看到两个服务都是Up状态：
# NAME                              STATUS
# trendradar-intelligent-monitor    Up
# trendradar-webhook-receiver       Up

# 测试API
curl http://localhost:8000/

# 查看日志
docker compose logs -f
```

### 从本地电脑验证

```bash
# 测试API访问
curl http://45.197.145.24:8000/

# 在浏览器访问API文档
open http://45.197.145.24:8000/docs
```

## 🧪 快速测试订阅功能

### 在服务器上测试

```bash
ssh 45.197.145.24
cd /home/Project/TrendRadar

# 运行测试脚本
python3 simple_client_test.py
```

### 从本地测试

```python
import requests

# 创建监控任务
response = requests.post(
    "http://45.197.145.24:8000/api/v2/create_task",
    json={
        "user_id": "test_user",
        "description": "监控000973股票的舆论信息",
        "webhook_url": "http://45.197.145.24:9000/webhook/generic"
    }
)

print(response.json())
```

## 🔧 服务管理

### 查看日志

```bash
ssh 45.197.145.24
cd /home/Project/TrendRadar

# 实时查看所有日志
docker compose logs -f

# 查看智能监控服务日志
docker compose logs -f intelligent-monitor

# 查看Webhook接收器日志
docker compose logs -f webhook-receiver

# 查看最近100行日志
docker compose logs --tail=100
```

### 重启服务

```bash
ssh 45.197.145.24
cd /home/Project/TrendRadar

# 重启所有服务
docker compose restart

# 重启特定服务
docker compose restart intelligent-monitor
```

### 停止服务

```bash
ssh 45.197.145.24
cd /home/Project/TrendRadar

# 停止服务
docker compose down
```

### 更新代码

```bash
ssh 45.197.145.24
cd /home/Project/TrendRadar

# 拉取最新代码
git pull origin main

# 重新构建并启动
docker compose up -d --build
```

## 🔒 安全配置

### 1. 防火墙配置

服务器上执行：

```bash
# Ubuntu/Debian
sudo ufw allow 8000/tcp
sudo ufw allow 9000/tcp
sudo ufw reload

# CentOS/RHEL
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --permanent --add-port=9000/tcp
sudo firewall-cmd --reload
```

### 2. 云服务商安全组

如果服务器在云平台（阿里云/腾讯云/AWS等），需要在控制台配置安全组：

- 入站规则：
  - 端口 8000 (TCP) - API服务
  - 端口 9000 (TCP) - Webhook接收器

## 🌐 外部访问

### API文档

浏览器访问: http://45.197.145.24:8000/docs

### API端点

- 创建任务: `POST http://45.197.145.24:8000/api/v2/create_task`
- 配置任务: `POST http://45.197.145.24:8000/api/v2/configure_task`
- 查询任务: `GET http://45.197.145.24:8000/api/v2/task/{id}`
- 触发任务: `POST http://45.197.145.24:8000/api/v2/trigger/{id}`

### Webhook接收器

- 通用Webhook: `POST http://45.197.145.24:9000/webhook/generic`
- 查看消息: `GET http://45.197.145.24:9000/messages`

## 📊 监控

### 查看容器资源使用

```bash
ssh 45.197.145.24
cd /home/Project/TrendRadar

# 查看实时资源使用
docker stats

# 查看磁盘使用
docker system df
```

### 查看数据库

```bash
ssh 45.197.145.24
cd /home/Project/TrendRadar

# 查询所有任务
sqlite3 data/tasks.db "SELECT task_id, stock_code, status FROM tasks;"

# 查询活跃任务
sqlite3 data/tasks.db "SELECT task_id, stock_code, status FROM tasks WHERE status='active';"
```

## 🐛 故障排查

### 问题1: 服务无法访问

```bash
# 检查服务状态
docker compose ps

# 检查端口监听
sudo netstat -tlnp | grep -E '8000|9000'

# 检查防火墙
sudo ufw status
```

### 问题2: 容器无法启动

```bash
# 查看容器日志
docker compose logs intelligent-monitor

# 重新构建
docker compose down
docker compose build --no-cache
docker compose up -d
```

### 问题3: 磁盘空间不足

```bash
# 清理Docker资源
docker system prune -a

# 清理日志
cd /home/Project/TrendRadar
rm -rf logs/*
```

## 🔄 完整部署流程示例

```bash
# 1. 从本地电脑登录服务器
ssh 45.197.145.24

# 2. 进入项目目录（如果已存在）或创建新目录
cd /home/Project
# 如果首次部署：
# git clone https://github.com/Moonlight-hello/TrendRadar.git

# 如果已存在，更新代码：
cd TrendRadar
git pull origin main

# 3. 停止旧服务（如果有）
docker compose down

# 4. 重新构建并启动
docker compose up -d --build

# 5. 查看状态
docker compose ps
docker compose logs -f

# 6. 测试API
curl http://localhost:8000/

# 7. 退出服务器
exit

# 8. 从本地测试外部访问
curl http://45.197.145.24:8000/
```

## 📞 快速命令参考

```bash
# SSH登录
ssh 45.197.145.24

# 进入项目
cd /home/Project/TrendRadar

# 查看状态
docker compose ps

# 查看日志
docker compose logs -f

# 重启
docker compose restart

# 更新
git pull && docker compose up -d --build

# 停止
docker compose down

# 测试
python3 simple_client_test.py
```

## 🎉 部署完成

部署成功后，你可以：

1. **访问API文档**: http://45.197.145.24:8000/docs
2. **订阅股票监控**: 使用API创建监控任务
3. **查看推送报告**: 访问Webhook接收器
4. **监控系统状态**: 使用docker命令查看日志和资源

---

**服务器信息**
- IP: 45.197.145.24
- 项目目录: /home/Project/TrendRadar
- API端口: 8000
- Webhook端口: 9000
