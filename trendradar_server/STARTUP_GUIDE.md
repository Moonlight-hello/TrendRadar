# TrendRadar Server - 启动指南

> 完整的TrendRadar服务启动指南

---

## 🎯 系统架构

```
┌─────────────────────────────────────────────────────┐
│                  FastAPI Server                      │
│                  (main.py:8000)                      │
│  ┌─────────────────────────────────────────────┐   │
│  │  UserManager    - 用户管理                    │   │
│  │  CrawlerAgent   - 数据爬取                    │   │
│  │  AnalyzerAgent  - AI分析                      │   │
│  │  Scheduler      - 定时任务                    │   │
│  │  TelegramBot    - 用户交互 (可选)             │   │
│  │  PushService    - 消息推送 (可选)             │   │
│  └─────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
                         ↓
           ┌──────────────────────────┐
           │     New API Gateway       │
           │  http://45.197.145.24:3000│
           └──────────────────────────┘
```

---

## 🚀 快速启动

### 方法1: 使用启动脚本（推荐）

```bash
cd /Users/wangxinlong/Code/TrendRadarRepository/TrendRadar/trendradar_server

# 运行启动脚本
./start.sh
```

### 方法2: 手动启动

```bash
cd /Users/wangxinlong/Code/TrendRadarRepository/TrendRadar/trendradar_server

# 1. 安装依赖
pip3 install -r requirements.txt

# 2. 设置环境变量
export TRENDRADAR_DB_PATH="/tmp/trendradar.db"
export MOCK_MODE="true"

# 3. 启动服务
python3 main.py
```

启动后访问：
- **API服务**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

---

## 📋 环境变量配置

### 必需配置

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `TRENDRADAR_DB_PATH` | 数据库路径 | `/tmp/trendradar.db` |

### 可选配置

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `NEW_API_BASE` | New API地址 | `http://45.197.145.24:3000/v1` |
| `NEW_API_KEY` | API密钥 | (已配置) |
| `MOCK_MODE` | Mock模式（开发用） | `true` |
| `TELEGRAM_BOT_TOKEN` | Telegram Bot Token | (未配置) |

### 示例配置

```bash
# 开发环境（使用Mock模式）
export TRENDRADAR_DB_PATH="/tmp/trendradar_dev.db"
export MOCK_MODE="true"

# 生产环境（使用真实API）
export TRENDRADAR_DB_PATH="/data/trendradar.db"
export MOCK_MODE="false"
export NEW_API_KEY="your_production_api_key"
export TELEGRAM_BOT_TOKEN="your_bot_token"
```

---

## 🧪 测试API

### 1. 健康检查

```bash
curl http://localhost:8000/health
```

响应：
```json
{
  "status": "healthy",
  "timestamp": "2026-04-23T12:00:00",
  "services": {
    "database": true,
    "crawler": true,
    "analyzer": true,
    "scheduler": true,
    "telegram_bot": false,
    "push_service": false
  }
}
```

### 2. 提交分析任务

```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "TSLA",
    "source": "eastmoney",
    "max_posts": 20,
    "analysis_type": "comprehensive"
  }'
```

### 3. 创建订阅

```bash
curl -X POST http://localhost:8000/api/subscriptions \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "telegram_123",
    "target": "TSLA",
    "target_display_name": "特斯拉",
    "platforms": ["eastmoney"],
    "push_channels": ["telegram"]
  }'
```

### 4. 查询订阅列表

```bash
curl http://localhost:8000/api/subscriptions/telegram_123
```

### 5. 手动触发爬取（测试）

```bash
curl -X POST http://localhost:8000/api/trigger-crawl
```

---

## 🔄 系统流程

### 用户订阅流程

```
1. 用户通过Telegram Bot发送 /subscribe TSLA
   ↓
2. TelegramBot → UserManager 创建订阅
   ↓
3. 订阅保存到数据库
   ↓
4. 调度器定时触发爬取（默认30分钟）
   ↓
5. CrawlerAgent 爬取数据
   ↓
6. AnalyzerAgent AI分析
   ↓
7. PushService 推送给用户
```

### 定时任务

| 任务 | 频率 | 功能 |
|------|------|------|
| 爬取分析推送 | 每30分钟 | 爬取订阅数据→AI分析→推送 |
| 会员检查 | 每天凌晨2点 | 检查会员过期 |
| 余额检查 | 每小时 | 检查Token余额 |

---

## 📊 监控和日志

### 查看系统统计

```bash
curl http://localhost:8000/api/stats
```

响应：
```json
{
  "scheduler": {
    "total_runs": 10,
    "success_runs": 8,
    "failed_runs": 2,
    "last_run": "2026-04-23T12:30:00",
    "is_running": true,
    "next_run": "2026-04-23T13:00:00"
  }
}
```

### 日志查看

服务启动后，日志会输出到终端：

```
2026-04-23 12:00:00 - INFO - TrendRadar Server 启动中...
2026-04-23 12:00:01 - INFO - ✅ 用户管理器初始化完成
2026-04-23 12:00:02 - INFO - ✅ 爬虫Agent初始化完成
2026-04-23 12:00:03 - INFO - ✅ 分析Agent初始化完成
2026-04-23 12:00:04 - INFO - ✅ 定时任务调度器启动完成
2026-04-23 12:00:05 - INFO - 🚀 TrendRadar Server 启动完成！
```

---

## 🔧 常见问题

### Q1: 端口8000已被占用

**解决方案**:
修改 `main.py` 最后一行的端口号：
```python
uvicorn.run("main:app", host="0.0.0.0", port=8001)
```

### Q2: 数据库权限错误

**解决方案**:
确保数据库路径有写权限：
```bash
mkdir -p /tmp
chmod 777 /tmp
```

### Q3: Mock模式下API不调用真实接口

**原因**: Mock模式用于开发测试，不会调用真实API。

**解决方案**: 设置环境变量：
```bash
export MOCK_MODE="false"
```

### Q4: Telegram Bot无法启动

**原因**: 未配置 `TELEGRAM_BOT_TOKEN`。

**解决方案**:
1. 通过 @BotFather 创建Bot获取Token
2. 设置环境变量：
```bash
export TELEGRAM_BOT_TOKEN="your_token"
```

---

## 📂 项目结构

```
trendradar_server/
├── main.py                  # FastAPI主入口 ⭐
├── start.sh                 # 启动脚本 ⭐
├── requirements.txt         # 依赖列表
├── STARTUP_GUIDE.md        # 本文档
├── core/                    # 核心模块
│   ├── user_manager.py     # 用户管理
│   ├── crawler_agent.py    # 爬虫Agent
│   ├── analyzer_agent.py   # AI分析Agent ⭐
│   └── scheduler.py        # 定时调度器 ⭐
├── user/                    # 用户模块
│   ├── manager.py          # 简化的用户管理
│   ├── telegram_bot.py     # Telegram Bot
│   └── push_service.py     # 推送服务
├── db/                      # 数据库
│   └── schema.sql          # 表结构
├── config/                  # 配置
│   └── membership_rules.py # 会员规则
└── tests/                   # 测试
    ├── test_user_manager.py
    ├── test_crawler_agent.py
    └── test_analyzer_agent.py ⭐
```

⭐ = 本次新增或更新

---

## 🎉 完成状态

### 已完成功能

- [x] 数据库设计（9张表）
- [x] 用户管理系统（UserManager）
- [x] 爬虫Agent（CrawlerAgent）
- [x] AI分析Agent（AnalyzerAgent）⭐
- [x] 定时任务调度器（Scheduler）⭐
- [x] FastAPI服务接口 ⭐
- [x] Telegram Bot
- [x] 推送服务
- [x] Mock模式（开发测试）

### 待完善功能

- [ ] 真实API对接（需配置New API）
- [ ] 微信公众号支付集成
- [ ] 数据持久化优化
- [ ] 异步任务队列（Celery）
- [ ] 监控告警系统
- [ ] Docker容器化部署

---

## 📞 联系方式

- 项目: TrendRadar
- 版本: 1.0
- 更新: 2026-04-23
