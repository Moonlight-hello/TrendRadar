# TrendRadar 服务器部署指南

> **版本**: v1.0
> **最后更新**: 2026-04-20

---

## 📋 部署前准备

### 服务器要求

#### 最低配置
- CPU: 2 核
- 内存: 4GB
- 磁盘: 50GB
- 操作系统: Ubuntu 20.04+ / CentOS 7+

#### 推荐配置
- CPU: 4 核
- 内存: 8GB
- 磁盘: 100GB SSD
- 操作系统: Ubuntu 22.04 LTS

### 软件依赖
- Python 3.10+
- Git
- SQLite3
- Nginx（可选，用于反向代理）
- Supervisor（可选，用于进程管理）
- Docker（可选，容器化部署）

---

## 🚀 快速部署（3种方式）

### 方式 1: 传统部署（推荐新手）

#### Step 1: 服务器初始化

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装基础依赖
sudo apt install -y python3.10 python3.10-venv python3-pip git sqlite3

# 创建部署用户（可选）
sudo useradd -m -s /bin/bash trendradar
sudo su - trendradar
```

#### Step 2: 克隆项目

```bash
# 进入部署目录
cd ~

# 克隆项目（如果已经打包，直接上传）
# 方式 A: 从 Git 克隆
git clone <your-repo-url> TrendRadar

# 方式 B: 上传打包文件
# scp -r /Users/wangxinlong/Code/TrendRadar user@server:~/
```

#### Step 3: 安装依赖

```bash
cd ~/TrendRadar

# 创建虚拟环境
python3 -m venv .venv

# 激活虚拟环境
source .venv/bin/activate

# 升级 pip
pip install --upgrade pip

# 安装依赖
pip install -r requirements.txt
```

#### Step 4: 配置环境

```bash
# 创建配置目录
mkdir -p config data logs

# 复制配置模板
cp config/config.yaml.example config/config.yaml

# 编辑配置
vim config/config.yaml
```

#### Step 5: 测试运行

```bash
# 运行测试脚本
python3 test_local.py

# 如果测试通过，运行主程序
python3 -m trendradar
```

#### Step 6: 配置系统服务

创建 systemd 服务文件：

```bash
sudo vim /etc/systemd/system/trendradar.service
```

内容：
```ini
[Unit]
Description=TrendRadar Agent System
After=network.target

[Service]
Type=simple
User=trendradar
WorkingDirectory=/home/trendradar/TrendRadar
Environment="PATH=/home/trendradar/TrendRadar/.venv/bin"
ExecStart=/home/trendradar/TrendRadar/.venv/bin/python3 -m trendradar
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
# 重新加载 systemd
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start trendradar

# 查看状态
sudo systemctl status trendradar

# 设置开机自启
sudo systemctl enable trendradar

# 查看日志
sudo journalctl -u trendradar -f
```

---

### 方式 2: Docker 部署（推荐生产环境）

#### Step 1: 创建 Dockerfile

```dockerfile
# Dockerfile
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    sqlite3 \
    git \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 创建数据目录
RUN mkdir -p /app/data /app/logs

# 暴露端口（如果需要）
EXPOSE 8000

# 设置环境变量
ENV PYTHONUNBUFFERED=1

# 启动命令
CMD ["python3", "-m", "trendradar"]
```

#### Step 2: 创建 docker-compose.yml

```yaml
version: '3.8'

services:
  trendradar:
    build: .
    container_name: trendradar
    restart: unless-stopped
    environment:
      - TZ=Asia/Shanghai
      - SCHEDULE_ENABLED=true
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./config:/app/config
    networks:
      - trendradar-network

  # 可选：添加数据库
  postgres:
    image: postgres:14
    container_name: trendradar-db
    restart: unless-stopped
    environment:
      - POSTGRES_DB=trendradar
      - POSTGRES_USER=trendradar
      - POSTGRES_PASSWORD=your_password
    volumes:
      - postgres-data:/var/lib/postgresql/data
    networks:
      - trendradar-network

volumes:
  postgres-data:

networks:
  trendradar-network:
    driver: bridge
```

#### Step 3: 部署

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down

# 重启服务
docker-compose restart
```

---

### 方式 3: Supervisor 管理（推荐多进程）

#### Step 1: 安装 Supervisor

```bash
sudo apt install -y supervisor
```

#### Step 2: 创建配置文件

```bash
sudo vim /etc/supervisor/conf.d/trendradar.conf
```

内容：
```ini
[program:trendradar]
command=/home/trendradar/TrendRadar/.venv/bin/python3 -m trendradar
directory=/home/trendradar/TrendRadar
user=trendradar
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/home/trendradar/TrendRadar/logs/trendradar.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=10
environment=PATH="/home/trendradar/TrendRadar/.venv/bin"
```

#### Step 3: 启动服务

```bash
# 更新配置
sudo supervisorctl reread
sudo supervisorctl update

# 启动服务
sudo supervisorctl start trendradar

# 查看状态
sudo supervisorctl status

# 查看日志
tail -f ~/TrendRadar/logs/trendradar.log
```

---

## 🔧 配置说明

### 1. 基础配置

编辑 `config/config.yaml`:

```yaml
# 应用配置
app:
  timezone: "Asia/Shanghai"
  debug: false

# 调度配置
schedule:
  enabled: true
  preset: "always_on"  # office_hours, morning_evening

# 存储配置
storage:
  backend: "local"  # local, remote
  local:
    output_dir: "./data"
    data_retention_days: 30

# 通知配置
notification:
  enabled: true
  channels:
    feishu:
      enabled: true
      webhook_url: "${FEISHU_WEBHOOK_URL}"

# AI 配置
ai:
  enabled: true
  model: "deepseek/deepseek-chat"
  api_key: "${AI_API_KEY}"
```

### 2. 环境变量

创建 `.env` 文件：

```bash
# 通知渠道
FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/xxx
DINGTALK_WEBHOOK_URL=https://oapi.dingtalk.com/robot/send?access_token=xxx

# AI 配置
AI_API_KEY=sk-xxx
AI_MODEL=deepseek/deepseek-chat

# 数据库配置（如果使用 PostgreSQL）
DATABASE_URL=postgresql://user:pass@localhost/trendradar

# 其他配置
TZ=Asia/Shanghai
PYTHONUNBUFFERED=1
```

---

## 📊 监控和日志

### 1. 日志配置

```python
# 在 config/logging.yaml 中配置
version: 1
disable_existing_loggers: False

formatters:
  standard:
    format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

handlers:
  console:
    class: logging.StreamHandler
    formatter: standard
    level: INFO

  file:
    class: logging.handlers.RotatingFileHandler
    filename: logs/trendradar.log
    maxBytes: 10485760  # 10MB
    backupCount: 10
    formatter: standard
    level: DEBUG

loggers:
  trendradar:
    level: DEBUG
    handlers: [console, file]
    propagate: no

root:
  level: INFO
  handlers: [console, file]
```

### 2. 监控脚本

创建 `scripts/monitor.sh`:

```bash
#!/bin/bash

# 监控脚本
LOG_FILE="logs/monitor.log"

check_process() {
    if pgrep -f "python3 -m trendradar" > /dev/null; then
        echo "$(date): TrendRadar is running" >> $LOG_FILE
        return 0
    else
        echo "$(date): TrendRadar is NOT running" >> $LOG_FILE
        return 1
    fi
}

# 如果进程不存在，重启
if ! check_process; then
    echo "$(date): Restarting TrendRadar..." >> $LOG_FILE
    sudo systemctl restart trendradar
fi
```

添加到 crontab：
```bash
# 每 5 分钟检查一次
*/5 * * * * /home/trendradar/TrendRadar/scripts/monitor.sh
```

---

## 🔒 安全配置

### 1. 防火墙配置

```bash
# 如果需要开放端口
sudo ufw allow 8000/tcp
sudo ufw enable
```

### 2. 数据库备份

```bash
#!/bin/bash
# scripts/backup.sh

BACKUP_DIR="/home/trendradar/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# 备份数据库
cp data/*.db $BACKUP_DIR/db_$DATE.db

# 保留最近 30 天的备份
find $BACKUP_DIR -name "db_*.db" -mtime +30 -delete
```

添加到 crontab：
```bash
# 每天凌晨 2 点备份
0 2 * * * /home/trendradar/TrendRadar/scripts/backup.sh
```

---

## 🎯 性能优化

### 1. 数据库优化

```bash
# SQLite 优化
sqlite3 data/trendradar.db << EOF
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA cache_size = -64000;
PRAGMA temp_store = MEMORY;
EOF
```

### 2. 资源限制

编辑 `/etc/security/limits.conf`:

```
trendradar soft nofile 65536
trendradar hard nofile 65536
```

---

## 📝 常用运维命令

### 服务管理
```bash
# systemd
sudo systemctl start trendradar
sudo systemctl stop trendradar
sudo systemctl restart trendradar
sudo systemctl status trendradar

# supervisor
sudo supervisorctl start trendradar
sudo supervisorctl stop trendradar
sudo supervisorctl restart trendradar
sudo supervisorctl status

# docker
docker-compose up -d
docker-compose down
docker-compose restart
docker-compose logs -f
```

### 日志查看
```bash
# systemd 日志
sudo journalctl -u trendradar -f
sudo journalctl -u trendradar --since "1 hour ago"

# 文件日志
tail -f logs/trendradar.log
tail -100 logs/trendradar.log | grep ERROR

# docker 日志
docker logs -f trendradar
```

### 数据库操作
```bash
# 进入数据库
sqlite3 data/trendradar.db

# 查看表
.tables

# 统计数据
SELECT COUNT(*) FROM posts;

# 清理旧数据
DELETE FROM posts WHERE created_at < date('now', '-30 days');
VACUUM;
```

---

## 🆘 故障排查

### 问题 1: 服务无法启动

```bash
# 检查日志
sudo journalctl -u trendradar -n 50

# 检查配置
python3 -c "import yaml; yaml.safe_load(open('config/config.yaml'))"

# 检查依赖
pip list | grep -E "requests|litellm|fastmcp"
```

### 问题 2: 数据库锁定

```bash
# 检查是否有其他进程占用
lsof data/trendradar.db

# 关闭占用进程
kill -9 <PID>

# 恢复数据库
sqlite3 data/trendradar.db "VACUUM;"
```

### 问题 3: 内存占用过高

```bash
# 查看内存使用
ps aux | grep trendradar

# 限制内存使用（systemd）
# 在 service 文件中添加
MemoryLimit=1G
```

---

## 📞 技术支持

- **文档**: 查看项目文档目录
- **日志**: 检查 logs 目录
- **Issue**: 提交 GitHub Issue
- **社区**: 加入讨论组

---

**部署愉快！🚀**
