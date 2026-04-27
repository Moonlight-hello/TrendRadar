# TrendRadar 智能股票监控系统 - Docker镜像

FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p logs output/stocks data

# 暴露端口
# 8000: 智能监控服务API
# 9000: Webhook接收器
EXPOSE 8000 9000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# 默认命令：启动智能监控服务
CMD ["python3", "intelligent_monitor_service.py"]
