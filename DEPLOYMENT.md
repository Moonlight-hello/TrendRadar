# 股票监控服务 - 部署文档

## 🏗️ 架构说明

### 设计模式：订阅-推送模式

```
用户（微信公众号/飞书）
    ↓ POST /api/subscribe（提供Webhook URL）
后端服务（本服务）
    ↓ 定时爬取数据
东方财富股吧
    ↓ 保存到数据库
SQLite
    ↓ 生成报告
报告生成器
    ↓ POST Webhook URL
用户接收推送（微信/飞书）
```

### 为什么不用WebSocket？

1. **微信公众号不支持WebSocket**：只能通过HTTP Webhook接收推送
2. **飞书机器人也是Webhook**：配置Webhook URL，接收POST请求
3. **服务端主动推送**：Webhook模式下，服务器主动POST数据到用户提供的URL

---

## 🚀 快速开始

### 1. 启动后端服务

```bash
cd /Users/wangxinlong/Code/TrendRadarRepository/TrendRadar

# 启动股票监控服务
python3 stock_monitor_service.py
```

服务启动后：
- **地址**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **自动监控**: 每60秒检查一次所有订阅，到时间就爬取并推送

### 2. 启动测试客户端（模拟Webhook接收）

```bash
# 新开一个终端
python3 test_client.py server
```

这会启动一个模拟的Webhook接收服务器（端口9000），用于接收推送。

### 3. 测试订阅流程

```bash
# 再开一个终端，运行测试
python3 test_client.py test1
```

---

## 📡 API接口

### 1. 订阅股票

```bash
POST /api/subscribe
Content-Type: application/json

{
  "stock_code": "000973",
  "webhook_url": "https://your-webhook.com/receive",
  "webhook_type": "feishu",  # feishu/dingtalk/wechat/generic
  "user_id": "user123",
  "interval": 300  # 爬取间隔（秒），默认300
}
```

**响应**:
```json
{
  "success": true,
  "subscription_id": 1,
  "message": "已订阅股票 000973，每 300秒 更新一次"
}
```

### 2. 取消订阅

```bash
POST /api/unsubscribe
Content-Type: application/json

{
  "stock_code": "000973",
  "user_id": "user123"
}
```

### 3. 查看我的订阅

```bash
GET /api/subscriptions/{user_id}
```

**响应**:
```json
{
  "user_id": "user123",
  "count": 2,
  "subscriptions": [
    {
      "id": 1,
      "stock_code": "000973",
      "webhook_url": "https://...",
      "interval": 300,
      "status": "active"
    }
  ]
}
```

### 4. 手动触发爬取

```bash
POST /api/trigger/{stock_code}
```

立即爬取该股票并推送给所有订阅者。

### 5. 查看统计

```bash
GET /api/stocks/{stock_code}/stats
```

---

## 📬 Webhook推送格式

### 飞书格式 (webhook_type: "feishu")

```json
{
  "msg_type": "interactive",
  "card": {
    "header": {
      "title": {"tag": "plain_text", "content": "股票 000973 监控报告"},
      "template": "blue"
    },
    "elements": [
      {
        "tag": "markdown",
        "content": "# 📊 股票 000973 监控报告\n\n..."
      }
    ]
  }
}
```

### 钉钉格式 (webhook_type: "dingtalk")

```json
{
  "msgtype": "markdown",
  "markdown": {
    "title": "股票监控提醒",
    "text": "# 📊 股票 000973 监控报告\n\n..."
  }
}
```

### 企业微信格式 (webhook_type: "wechat")

```json
{
  "msgtype": "markdown",
  "markdown": {
    "content": "# 📊 股票 000973 监控报告\n\n..."
  }
}
```

### 通用格式 (webhook_type: "generic")

```json
{
  "title": "股票 000973 监控报告",
  "content": "# 📊 股票 000973 监控报告\n\n..."
}
```

---

## 🧪 完整测试流程

### 步骤1: 启动服务

```bash
# 终端1: 启动后端服务
python3 stock_monitor_service.py

# 终端2: 启动Webhook接收器（模拟）
python3 test_client.py server
```

### 步骤2: 订阅股票

```bash
# 终端3: 订阅
curl -X POST http://localhost:8000/api/subscribe \
  -H "Content-Type: application/json" \
  -d '{
    "stock_code": "000973",
    "webhook_url": "http://localhost:9000/webhook/generic",
    "webhook_type": "generic",
    "user_id": "test_user",
    "interval": 120
  }'
```

### 步骤3: 手动触发（或等待自动触发）

```bash
# 手动触发爬取
curl -X POST http://localhost:8000/api/trigger/000973
```

### 步骤4: 查看推送

在终端2（Webhook接收器）会看到类似输出：

```
================================================================================
📬 收到通用Webhook推送
================================================================================
标题: 股票 000973 监控报告

内容:
# 📊 股票 000973 监控报告

**更新时间**: 2026-04-27 12:00:00

## 📈 统计信息
- 总帖子: 372 条
- 总评论: 385 条
- 最新时间: 2026-04-27 11:04:51

## 🆕 新增帖子 (5条)
1. **帖子标题**
   - 作者: 张三
   - 评论: 10 | 阅读: 100
   - 时间: 2026-04-27 11:00:00

...
================================================================================
```

---

## 🔧 微信公众号集成

### 1. 配置微信服务器

微信公众号需要你有一个公网可访问的服务器。

```python
# 在你的微信公众号后端
@app.post("/wechat/webhook")
async def receive_stock_report(request: Request):
    """接收股票监控推送"""
    data = await request.json()

    # 解析报告
    title = data['title']
    content = data['content']

    # 推送给用户（调用微信API）
    send_to_wechat_user(user_openid, content)

    return {"success": True}
```

### 2. 订阅时提供Webhook URL

```bash
# 用户在微信公众号输入：订阅 000973
# 后台调用
curl -X POST http://your-backend.com:8000/api/subscribe \
  -d '{
    "stock_code": "000973",
    "webhook_url": "https://your-wechat-server.com/wechat/webhook",
    "webhook_type": "wechat",
    "user_id": "wechat_openid_xxx"
  }'
```

### 3. 接收推送并转发给微信用户

每次爬取完成，后端会POST到你的Webhook URL，你再调用微信API推送给用户。

---

## 🚢 飞书机器人集成

### 方法1: 使用飞书群机器人

1. **创建飞书群机器人**
   - 在飞书群里添加机器人
   - 复制Webhook URL（类似 https://open.feishu.cn/open-apis/bot/v2/hook/...）

2. **订阅股票**
```bash
curl -X POST http://localhost:8000/api/subscribe \
  -d '{
    "stock_code": "000973",
    "webhook_url": "https://open.feishu.cn/open-apis/bot/v2/hook/YOUR_TOKEN",
    "webhook_type": "feishu"
  }'
```

3. **接收推送**
   - 爬取完成后，自动推送到飞书群
   - 显示为卡片消息

### 方法2: 使用飞书应用

如果要单独推送给用户（而不是群），需要：
1. 创建飞书应用
2. 获取用户的open_id
3. 使用飞书消息API发送

---

## 📊 监控流程

### 自动监控流程

```
1. 用户订阅股票（提供Webhook URL）
   ↓
2. 后台记录到subscriptions.db
   ↓
3. 监控循环每60秒检查一次
   ↓
4. 判断订阅是否到了爬取时间（last_crawl_time + interval）
   ↓
5. 到时间了 → 爬取数据
   ↓
6. 保存到eastmoney_stocks.db
   ↓
7. 生成Markdown报告
   ↓
8. POST到用户的Webhook URL
   ↓
9. 更新last_crawl_time
   ↓
10. 等待下次循环
```

### 手动触发流程

```
1. 调用 POST /api/trigger/{stock_code}
   ↓
2. 查找所有订阅该股票的用户
   ↓
3. 依次爬取并推送
   ↓
4. 立即返回（爬取在后台异步执行）
```

---

## 📈 性能优化

### 当前配置

- **监控循环**: 60秒检查一次
- **默认爬取间隔**: 300秒（5分钟）
- **每次爬取**: 2页帖子 + 30条评论/帖

### 扩展建议

1. **增加并发**: 使用asyncio.gather同时爬取多个股票
2. **消息队列**: 使用Redis/RabbitMQ解耦爬取和推送
3. **缓存**: 使用Redis缓存统计数据
4. **分布式**: 多个worker节点分担订阅

---

## 🛠️ 数据库表结构

### subscriptions.db

```sql
CREATE TABLE subscriptions (
    id INTEGER PRIMARY KEY,
    stock_code TEXT NOT NULL,
    webhook_url TEXT NOT NULL,
    webhook_type TEXT DEFAULT 'generic',
    user_id TEXT,
    interval INTEGER DEFAULT 300,
    last_crawl_time TIMESTAMP,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(stock_code, webhook_url)
);
```

### eastmoney_stocks.db

```sql
CREATE TABLE posts (...);  -- 帖子表
CREATE TABLE comments (...);  -- 评论表
```

---

## 🔒 安全建议

1. **验证Webhook URL**: 防止恶意URL
2. **限流**: 每个用户最多订阅N只股票
3. **签名验证**: Webhook推送时带上签名
4. **HTTPS**: 生产环境必须使用HTTPS

---

## 📝 环境变量

可以通过环境变量配置：

```bash
export DB_PATH="/data/eastmoney_stocks.db"
export SUBSCRIPTIONS_DB="/data/subscriptions.db"
export DEFAULT_CRAWL_INTERVAL=300
```

---

## 🐳 Docker部署（可选）

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python3", "stock_monitor_service.py"]
```

```bash
docker build -t stock-monitor .
docker run -d -p 8000:8000 \
  -v /data:/app/data \
  stock-monitor
```

---

## 📞 常见问题

### Q1: Webhook推送失败怎么办？

检查：
1. Webhook URL是否可访问
2. 网络是否通畅
3. 查看服务日志

### Q2: 如何修改爬取频率？

在订阅时设置`interval`参数（秒）。

### Q3: 如何查看所有订阅？

```bash
curl http://localhost:8000/api/subscriptions
```

### Q4: 如何停止某个订阅？

```bash
curl -X POST http://localhost:8000/api/unsubscribe \
  -d '{"stock_code":"000973","user_id":"xxx"}'
```

---

**最后更新**: 2026-04-27
**维护者**: TrendRadar Team
