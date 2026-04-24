# User Module - 用户管理模块

> 版本: 1.0 | 更新: 2026-04-23

---

## 📦 模块结构

```
user/
├── manager.py          # 用户管理器（数据库操作）
├── telegram_bot.py     # Telegram Bot（用户交互）
├── push_service.py     # 推送服务（消息推送）
├── config.py           # 配置文件
└── README.md           # 本文档
```

---

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install python-telegram-bot
```

### 2. 获取Telegram Bot Token

```
1. 打开Telegram，搜索 @BotFather
2. 发送 /newbot
3. 按提示创建Bot
4. 获得Token: 123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
```

### 3. 设置环境变量

```bash
export TELEGRAM_BOT_TOKEN='your_bot_token'
export TRENDRADAR_DB_PATH='/data/trendradar.db'
```

### 4. 运行Bot

```bash
cd /Users/wangxinlong/Code/TrendRadarRepository/TrendRadar/trendradar_server

python3 -m user.telegram_bot
```

---

## 📋 Bot命令列表

| 命令 | 说明 | 示例 |
|------|------|------|
| `/start` | 开始使用（自动注册） | `/start` |
| `/subscribe` | 订阅股票 | `/subscribe TSLA` |
| `/list` | 查看订阅列表 | `/list` |
| `/unsubscribe` | 取消订阅 | `/unsubscribe 1` |
| `/pause` | 暂停订阅 | `/pause 1` |
| `/resume` | 恢复订阅 | `/resume 1` |
| `/stats` | 查看统计 | `/stats` |
| `/help` | 帮助信息 | `/help` |

---

## 🔧 API使用示例

### 1. 用户管理器

```python
from user.manager import MinimalUserManager

# 初始化
user_mgr = MinimalUserManager("/data/trendradar.db")

# 注册用户
result = user_mgr.register_user(
    user_id="telegram_123456",
    channel="telegram",
    username="张三",
    telegram_id="123456"
)

# 查询用户
user_info = user_mgr.get_user_info("telegram_123456")

# 创建订阅
success, msg, sub_id = user_mgr.create_subscription(
    user_id="telegram_123456",
    subscription_type="stock",
    target="TSLA",
    platforms=["eastmoney"],
    push_channels=["telegram"]
)

# 查询订阅列表
subs = user_mgr.get_user_subscriptions("telegram_123456")

# 获取所有活跃订阅（用于定时任务）
all_subs = user_mgr.get_all_active_subscriptions()
```

---

### 2. Telegram Bot

```python
from user.telegram_bot import TrendRadarBot
import os

# 初始化Bot
bot = TrendRadarBot(
    token=os.getenv("TELEGRAM_BOT_TOKEN"),
    db_path="/data/trendradar.db"
)

# 运行Bot（阻塞模式）
bot.run()
```

---

### 3. 推送服务

```python
from user.push_service import PushService
from user.manager import MinimalUserManager
from user.telegram_bot import TrendRadarBot

# 初始化
user_mgr = MinimalUserManager("/data/trendradar.db")
bot = TrendRadarBot(token="...", db_path="/data/trendradar.db")
bot.setup()

push_service = PushService(user_mgr, bot)

# 推送消息给用户
import asyncio

async def push():
    success, msg = await push_service.push_to_user(
        user_id="telegram_123456",
        subscription_id=1,
        title="特斯拉更新",
        content="今日有10条新讨论..."
    )
    print(f"推送结果: {success}")

asyncio.run(push())
```

---

## 🔄 完整工作流程

### 用户使用流程

```
1. 用户打开Telegram，搜索Bot
2. 发送 /start
   ↓
   Bot自动注册用户（telegram_123456）

3. 发送 /subscribe TSLA
   ↓
   创建订阅: user_id → target=TSLA

4. 后台定时任务（每30分钟）
   ↓
   爬取TSLA数据 → AI分析 → 推送给用户

5. 用户收到推送
   ↓
   📊 特斯拉最新分析
   AI摘要: ...
   市场情绪: 积极
```

---

### 后端推送流程

```python
# scheduler.py - 定时任务示例

from apscheduler.schedulers.background import BackgroundScheduler
from user.manager import MinimalUserManager
from user.push_service import PushService
from core.crawler_agent import CrawlerAgent
from core.analyzer_agent import AnalyzerAgent

scheduler = BackgroundScheduler()

@scheduler.scheduled_job('interval', minutes=30)
async def crawl_and_push():
    """每30分钟执行一次"""

    # 1. 获取所有活跃订阅
    subscriptions = user_mgr.get_all_active_subscriptions()

    for sub in subscriptions:
        # 2. 爬取数据
        success, msg, data = crawler.crawl(
            user_id=sub['user_id'],
            platform='eastmoney',
            target=sub['target'],
            max_items=50
        )

        if not success:
            continue

        # 3. AI分析
        analysis = await analyzer.analyze(data)

        # 4. 格式化推送内容
        title, content = push_service.format_notification(sub, analysis)

        # 5. 推送给用户
        await push_service.push_to_user(
            user_id=sub['user_id'],
            subscription_id=sub['id'],
            title=title,
            content=content
        )

        # 6. 更新最后推送时间
        user_mgr.update_last_push(sub['id'])

scheduler.start()
```

---

## 📊 数据库表结构

### users表

```sql
CREATE TABLE users (
    user_id TEXT PRIMARY KEY,       -- telegram_123456
    username TEXT,                  -- 张三
    channel TEXT,                   -- telegram
    telegram_id TEXT,               -- 123456
    telegram_username TEXT,         -- zhangsan
    wechat_openid TEXT,             -- (微信用户)
    status TEXT,                    -- active/inactive
    created_at TEXT,
    last_active_at TEXT
);
```

### subscriptions表

```sql
CREATE TABLE subscriptions (
    id INTEGER PRIMARY KEY,
    user_id TEXT,                   -- telegram_123456
    subscription_type TEXT,         -- stock
    target TEXT,                    -- TSLA
    target_display_name TEXT,       -- 特斯拉
    platforms TEXT,                 -- ["eastmoney"]
    push_enabled INTEGER,           -- 1/0
    push_channels TEXT,             -- ["telegram"]
    push_frequency TEXT,            -- realtime
    status TEXT,                    -- active/paused
    last_push_at TEXT,
    created_at TEXT
);
```

---

## 🧪 测试

```bash
# 测试用户管理器
python3 -c "from user.manager import MinimalUserManager; \
mgr = MinimalUserManager('/tmp/test.db'); \
print(mgr.register_user('test_123', 'telegram'))"

# 测试Bot（需要设置Token）
export TELEGRAM_BOT_TOKEN='your_token'
python3 -m user.telegram_bot
```

---

## 🔐 安全建议

1. **不要将Bot Token提交到Git**
   ```bash
   # .gitignore
   *.env
   .env.*
   config_local.py
   ```

2. **使用环境变量存储敏感信息**
   ```bash
   export TELEGRAM_BOT_TOKEN='...'
   ```

3. **生产环境使用Webhook而非Polling**
   ```python
   bot.start_webhook(
       webhook_url='https://your-domain.com/webhook',
       port=8443
   )
   ```

---

## 📝 待办事项

- [ ] 添加微信公众号支持
- [ ] 支持批量订阅（上传CSV）
- [ ] 添加订阅标签分组
- [ ] 支持自定义推送频率
- [ ] 添加推送历史查询
- [ ] 支持订阅分享

---

## 📞 联系

- 项目: TrendRadar
- 模块: User Module
- 版本: 1.0
