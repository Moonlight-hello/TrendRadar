# 快速启动指南

> 10分钟完成Telegram Bot集成

---

## 🚀 Step 1: 安装依赖（1分钟）

```bash
pip install python-telegram-bot
```

---

## 🤖 Step 2: 创建Telegram Bot（3分钟）

### 在Telegram中操作：

1. 打开Telegram，搜索 `@BotFather`
2. 发送 `/newbot`
3. 输入Bot名称，例如: `TrendRadar Dev Bot`
4. 输入Bot用户名，例如: `trendradar_dev_bot`
5. 复制获得的Token: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`

---

## ⚙️ Step 3: 配置环境变量（1分钟）

```bash
# 设置Bot Token
export TELEGRAM_BOT_TOKEN='123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11'

# 设置数据库路径（可选，默认/tmp/trendradar_bot.db）
export TRENDRADAR_DB_PATH='/data/trendradar.db'
```

---

## 🏃 Step 4: 运行Bot（1分钟）

```bash
cd /Users/wangxinlong/Code/TrendRadarRepository/TrendRadar/trendradar_server

# 运行Bot
python3 -m user.telegram_bot
```

看到如下输出表示成功：

```
🚀 TrendRadar Bot 启动中...
📂 数据库: /tmp/trendradar_bot.db
✅ Bot已启动，按Ctrl+C停止
```

---

## 🎉 Step 5: 测试Bot（5分钟）

### 在Telegram中操作：

1. 搜索你的Bot: `@trendradar_dev_bot`
2. 点击 **开始** 或发送 `/start`

你会看到：

```
👋 欢迎 张三！

🎯 TrendRadar - 股票讨论智能追踪

🎉 首次注册成功！

📋 快速开始:
• /subscribe 订阅股票
• /list 查看订阅列表
• /help 查看帮助

💡 例如: /subscribe TSLA
```

3. 发送 `/subscribe TSLA`

Bot回复：

```
✅ 订阅成功！

📊 股票: TSLA
🔔 订阅ID: 1
📡 数据源: 东方财富股吧

系统将自动推送该股票的最新讨论和AI分析。
```

4. 发送 `/list` 查看订阅列表

```
📋 您的订阅列表 (1个)

1. ✅ TSLA (TSLA)
   📡 数据源: eastmoney
   🔔 推送: 开启
   🆔 ID: 1

💡 使用 /unsubscribe <ID> 取消订阅
```

---

## 🔧 常见问题

### Q1: 提示"No module named 'telegram'"

```bash
pip install python-telegram-bot
```

### Q2: 提示"请设置环境变量 TELEGRAM_BOT_TOKEN"

```bash
export TELEGRAM_BOT_TOKEN='your_bot_token'
```

### Q3: Bot无响应

检查：
1. Token是否正确
2. 网络是否畅通（需要访问Telegram服务器）
3. Bot是否已启动

---

## 📝 下一步

### 集成到后端服务

```python
# main.py

from user import MinimalUserManager, TrendRadarBot, PushService
from core.crawler_agent import CrawlerAgent

# 1. 初始化
user_mgr = MinimalUserManager("/data/trendradar.db")
bot = TrendRadarBot(token="...", db_path="/data/trendradar.db")
bot.setup()
push_service = PushService(user_mgr, bot)

# 2. 运行Bot（后台线程）
import threading
bot_thread = threading.Thread(target=bot.run)
bot_thread.daemon = True
bot_thread.start()

# 3. 定时任务（爬取和推送）
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()

@scheduler.scheduled_job('interval', minutes=30)
async def crawl_and_push():
    # 获取所有订阅
    subscriptions = user_mgr.get_all_active_subscriptions()

    for sub in subscriptions:
        # 爬取数据
        crawler = CrawlerAgent(user_mgr)
        success, msg, data = crawler.crawl(
            user_id=sub['user_id'],
            platform='eastmoney',
            target=sub['target'],
            max_items=50
        )

        if not success:
            continue

        # AI分析（待实现）
        # analysis = await analyzer.analyze(data)

        # 推送
        await push_service.push_to_user(
            user_id=sub['user_id'],
            subscription_id=sub['id'],
            title=f"{sub['target']} 更新",
            content=f"发现{len(data)}条新讨论"
        )

scheduler.start()
```

---

## 🎯 完成！

现在你已经有了：
- ✅ 用户身份识别系统
- ✅ Telegram Bot交互界面
- ✅ 订阅管理功能
- ✅ 消息推送能力

可以开始集成爬虫和AI分析了！
