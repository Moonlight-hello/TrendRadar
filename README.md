# TrendRadar - 智能股票监控系统

[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

AI驱动的股票舆论监控系统，支持自然语言任务创建、多维度智能分析、自动定时监控和Webhook推送。

## ✨ 特性

- 🤖 **AI驱动** - 自然语言理解，自动解析监控需求
- 📊 **多维分析** - 情绪统计、看多看空、高质量评论、活跃用户、热门话题
- 🕷️ **多平台支持** - 东方财富股吧（更多平台开发中）
- ⏰ **自动监控** - 配置一次，持续监控，定时推送
- 📬 **Webhook推送** - 支持飞书、钉钉、企业微信、通用Webhook
- 🐳 **Docker部署** - 一键部署，开箱即用
- 📱 **RESTful API** - 完整的HTTP API接口

## 🚀 快速开始

### 使用Docker（推荐）

```bash
# 克隆仓库
git clone https://github.com/Moonlight-hello/TrendRadar.git
cd TrendRadar

# 一键部署
./deploy.sh

# 服务将在以下端口启动
# - API服务: http://localhost:8000
# - API文档: http://localhost:8000/docs
# - Webhook接收器: http://localhost:9000
```

### 本地开发

```bash
# 安装依赖
pip install -r requirements.txt

# 启动智能监控服务
python3 intelligent_monitor_service.py

# 启动Webhook接收器（另一个终端）
python3 test_client.py server
```

## 📖 使用示例

### Python客户端

```python
import requests

# 1. 创建监控任务
response = requests.post(
    "http://localhost:8000/api/v2/create_task",
    json={
        "user_id": "my_user",
        "description": "监控000973股票的情绪统计和看多看空比例",
        "webhook_url": "https://your-webhook-url.com"
    }
)

task_id = response.json()['task_id']
stock_code = response.json()['intent']['entities']['stock_code']

# 2. 配置任务
requests.post(
    "http://localhost:8000/api/v2/configure_task",
    json={
        "task_id": task_id,
        "stock_code": stock_code,
        "analysis_types": ["sentiment", "bull_bear", "quality_posts"],
        "platforms": ["eastmoney"],
        "interval_minutes": 10
    }
)

print(f"✅ 成功订阅股票{stock_code}的监控，每10分钟推送一次")
```

### 快速测试

```bash
# 使用内置测试脚本
python3 simple_client_test.py
```

## 🔍 系统架构

```
用户输入自然语言
        ↓
AI理解意图 (IntentRecognizer)
        ↓
生成配置选项 (ConfigurationGuide)
        ↓
用户确认配置
        ↓
激活监控任务 (TaskManager)
        ↓
定时/手动触发执行
        ↓
爬虫Agent采集数据 (CrawlerAgent)
   ├─ 东方财富股吧
   ├─ 知乎（开发中）
   └─ 微博（开发中）
        ↓
分析Agent智能分析 (AnalysisAgent)
   ├─ 情绪统计
   ├─ 看多看空比例
   ├─ 有价值的评论
   ├─ 活跃用户分析
   └─ 热门话题
        ↓
生成结构化报告 (ReportGenerator)
        ↓
推送给用户 (Webhook)
```

## 📊 分析维度

| 分析类型 | 说明 | 输出示例 |
|---------|------|---------|
| 情绪统计 | 分析讨论区整体情绪 | 积极19.3% / 消极4.4% / 中性76.3% |
| 看多看空 | 统计看多和看空占比 | 看多76.5% / 看空23.5% → 看多占优 |
| 高质量评论 | 筛选有理论、有依据、有结论的分析 | 发现1条高质量帖子(0.48%) |
| 活跃用户 | 识别频繁发帖用户，警惕水军 | 用户A发帖15次(7.2%) |
| 热门话题 | 提取讨论最多的话题和关键词 | 锂电池(23次) / 业绩(18次) |

## 🌐 API文档

### 核心接口

- `POST /api/v2/create_task` - 创建监控任务
- `POST /api/v2/configure_task` - 配置任务
- `GET /api/v2/task/{id}` - 查询任务状态
- `POST /api/v2/trigger/{id}` - 手动触发执行

完整API文档: http://localhost:8000/docs

## 🐳 Docker部署

### 快速部署到服务器

```bash
# 1. 登录服务器
ssh user@your-server

# 2. 克隆代码
cd /opt
git clone https://github.com/Moonlight-hello/TrendRadar.git
cd TrendRadar

# 3. 一键部署
./deploy.sh

# 4. 验证
curl http://localhost:8000/
```

详细部署文档: [SERVER_DEPLOY_QUICK.md](SERVER_DEPLOY_QUICK.md)

### Docker Compose管理

```bash
# 启动服务
docker compose up -d

# 查看日志
docker compose logs -f

# 重启服务
docker compose restart

# 停止服务
docker compose down

# 更新代码
git pull && docker compose up -d --build
```

## 📚 文档

- [快速部署指南](SERVER_DEPLOY_QUICK.md) - 5分钟快速部署
- [完整部署文档](DOCKER_DEPLOYMENT.md) - 详细的生产环境部署
- [客户端使用指南](CLIENT_USAGE.md) - API调用和客户端使用
- [系统架构说明](FINAL_ARCHITECTURE.md) - 技术架构和设计
- [API文档](API_README.md) - 完整的API参考
- [演示文档](DEMO.md) - 实际运行示例

## 🔧 配置

### 环境变量

创建 `.env` 文件：

```bash
# API配置
API_HOST=0.0.0.0
API_PORT=8000

# Webhook配置
WEBHOOK_PORT=9000

# 日志级别
LOG_LEVEL=INFO
```

### 监控配置

在创建任务时配置：

```python
{
    "stock_code": "000973",           # 股票代码
    "analysis_types": [               # 分析维度
        "sentiment",                  # 情绪统计
        "bull_bear",                  # 看多看空
        "quality_posts"               # 高质量评论
    ],
    "platforms": ["eastmoney"],       # 监控平台
    "interval_minutes": 10            # 更新频率（分钟）
}
```

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 License

MIT License

## 🙏 致谢

- FastAPI - 现代化的Web框架
- httpx - 异步HTTP客户端
- Docker - 容器化部署

## 📞 联系方式

- GitHub: [@Moonlight-hello](https://github.com/Moonlight-hello)
- Issues: [提交问题](https://github.com/Moonlight-hello/TrendRadar/issues)

---

**⚠️ 免责声明**: 本系统仅用于技术研究和学习，不构成任何投资建议。请遵守相关平台的使用条款和爬虫规范。
