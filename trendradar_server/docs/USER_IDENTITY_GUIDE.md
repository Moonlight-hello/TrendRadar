# 用户身份识别方案（极简版）

> 版本: 1.0 | 更新: 2026-04-23
> 目标: 区分不同用户，实现个性化订阅推送

---

## 🎯 核心问题

**问题**: 如何识别用户身份，避免所有人看到相同内容？

**解决方案**: 给每个用户分配唯一ID，根据用户的订阅列表推送个性化内容。

---

## 📱 用户身份识别方案（5种）

### 方案1：Telegram Bot（推荐）⭐⭐⭐⭐⭐

**优点**:
- ✅ Telegram自动提供用户ID（唯一且稳定）
- ✅ 无需注册，开箱即用
- ✅ 支持推送消息
- ✅ 免费，无审核

**用户ID来源**: `message.from.id`（Telegram用户ID）

**示例流程**:
```
用户: 打开Telegram，搜索 @YourBot
     ↓
用户: 点击"开始" /start
     ↓
Bot:  自动获取用户ID (e.g., 123456789)
     ↓
后端: user_id = f"telegram_{telegram_id}"
     ↓
用户: 发送 "/subscribe TSLA"
     ↓
后端: 为用户 telegram_123456789 创建订阅
     ↓
定时: 爬取TSLA数据 → AI分析 → 推送给该用户
```

**代码示例**:
```python
# telegram_bot.py

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """用户首次使用"""
    telegram_id = update.effective_user.id
    username = update.effective_user.username

    # 自动注册用户
    user_id = f"telegram_{telegram_id}"
    user_mgr.register_user(
        user_id=user_id,
        channel='telegram',
        telegram_id=str(telegram_id),
        telegram_username=username
    )

    await update.message.reply_text(
        f"欢迎 @{username}！\n"
        f"您的ID: {user_id}\n\n"
        f"使用 /subscribe 订阅股票"
    )

async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """订阅股票"""
    telegram_id = update.effective_user.id
    user_id = f"telegram_{telegram_id}"

    # 获取股票代码
    if not context.args:
        await update.message.reply_text("用法: /subscribe TSLA")
        return

    stock_code = context.args[0].upper()

    # 创建订阅
    success, msg, sub_id = user_mgr.create_subscription(
        user_id=user_id,
        subscription_type='stock',
        target=stock_code,
        platforms=['eastmoney'],
        push_channels=['telegram']
    )

    await update.message.reply_text(f"✅ {msg}")

# 启动Bot
app = Application.builder().token("YOUR_BOT_TOKEN").build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("subscribe", subscribe))
app.run_polling()
```

---

### 方案2：微信公众号

**优点**:
- ✅ 微信提供OpenID（用户唯一标识）
- ✅ 用户量大
- ✅ 支持推送

**缺点**:
- ❌ 需要认证公众号（300元/年）
- ❌ 推送有限制（每月4条）

**用户ID来源**: `event.FromUserName`（微信OpenID）

**示例流程**:
```
用户: 关注公众号
     ↓
微信: 发送 subscribe 事件
     ↓
后端: 获取 openid = "oXXXXXXXXXXXXX"
     ↓
后端: user_id = f"wechat_{openid}"
     ↓
后端: 自动注册用户
```

**代码示例**:
```python
from wechatpy import parse_message, create_reply

def handle_wechat_message(xml_data):
    msg = parse_message(xml_data)

    if msg.type == 'event' and msg.event == 'subscribe':
        # 用户关注公众号
        openid = msg.source
        user_id = f"wechat_{openid}"

        # 自动注册
        user_mgr.register_user(
            user_id=user_id,
            channel='wechat',
            wechat_openid=openid
        )

        reply_text = "欢迎关注TrendRadar！\n回复"订阅 特斯拉"开始使用"
        return create_reply(reply_text, msg).render()

    elif msg.type == 'text':
        openid = msg.source
        user_id = f"wechat_{openid}"
        content = msg.content

        # 处理订阅命令
        if content.startswith("订阅"):
            # ...
            pass
```

---

### 方案3：Web匿名UUID（最简单）⭐⭐⭐⭐

**优点**:
- ✅ 无需注册
- ✅ 实现简单
- ✅ 隐私友好

**缺点**:
- ❌ 无法主动推送（需要用户主动刷新）
- ❌ 换设备会丢失

**用户ID来源**: 浏览器生成UUID，存储在localStorage

**示例流程**:
```javascript
// 前端（Web）

// 1. 检查本地是否有UUID
let userId = localStorage.getItem('trendradar_user_id');

if (!userId) {
    // 2. 生成新UUID
    userId = 'web_' + crypto.randomUUID();
    localStorage.setItem('trendradar_user_id', userId);

    // 3. 注册用户
    fetch('/api/user/register', {
        method: 'POST',
        body: JSON.stringify({ user_id: userId, channel: 'web' })
    });
}

// 4. 使用userId订阅
function subscribeStock(stockCode) {
    fetch('/api/subscription', {
        method: 'POST',
        body: JSON.stringify({
            user_id: userId,
            target: stockCode,
            platforms: ['eastmoney']
        })
    });
}

// 5. 轮询获取更新
setInterval(() => {
    fetch(`/api/user/${userId}/feed`)
        .then(res => res.json())
        .then(data => {
            // 更新页面显示
            updateFeed(data);
        });
}, 60000); // 每分钟轮询
```

---

### 方案4：手机号/邮箱注册

**优点**:
- ✅ 用户可以换设备登录
- ✅ 可以找回账号

**缺点**:
- ❌ 需要发送验证码（成本）
- ❌ 用户注册流程复杂

**用户ID来源**: `phone_13800138000` 或 `email_user@example.com`

**示例流程**:
```python
# 1. 用户输入手机号
phone = "13800138000"

# 2. 发送验证码（使用阿里云/腾讯云短信）
sms_code = generate_code()
send_sms(phone, sms_code)

# 3. 用户输入验证码
if verify_code(phone, user_input_code):
    user_id = f"phone_{phone}"
    user_mgr.register_user(user_id, channel='phone')
```

---

### 方案5：OAuth第三方登录

**优点**:
- ✅ 用户信任度高
- ✅ 无需管理密码

**缺点**:
- ❌ 需要申请开发者账号
- ❌ 实现复杂

**支持平台**:
- GitHub OAuth
- Google OAuth
- Apple Sign In

---

## 🎯 推荐方案对比

| 方案 | 实现难度 | 用户体验 | 推送能力 | 成本 | 推荐度 |
|------|---------|---------|---------|------|--------|
| **Telegram Bot** | ⭐ 简单 | ⭐⭐⭐⭐⭐ | ✅ 支持 | 免费 | ⭐⭐⭐⭐⭐ |
| **微信公众号** | ⭐⭐⭐ 中等 | ⭐⭐⭐⭐ | ✅ 支持 | 300元/年 | ⭐⭐⭐⭐ |
| **Web匿名UUID** | ⭐ 简单 | ⭐⭐⭐ | ❌ 不支持 | 免费 | ⭐⭐⭐⭐ |
| **手机号注册** | ⭐⭐⭐⭐ 复杂 | ⭐⭐ | ✅ 支持 | 短信费 | ⭐⭐ |

---

## 🚀 MVP推荐方案：Telegram Bot + Web匿名

### 为什么？

1. **Telegram Bot**（主推送渠道）
   - 实现简单（50行代码）
   - 免费
   - 支持实时推送
   - 适合早期用户

2. **Web匿名UUID**（辅助渠道）
   - 无需注册
   - 降低门槛
   - 用户自己轮询刷新

---

## 📋 实际使用场景示例

### 场景1：张三的一天

```
早上9:00
张三打开Telegram
Bot推送: "特斯拉(TSLA)股吧有10条新讨论，整体情绪：积极 📈"

点击查看详情
Bot显示: AI摘要 + 关键讨论

下午3:00
张三发送: /subscribe AAPL
Bot回复: "✅ 已订阅苹果(AAPL)"

晚上8:00
Bot推送: "苹果(AAPL)股吧有15条新讨论..."
```

---

### 场景2：李四的一天

```
中午12:00
李四打开网页版 trendradar.com

首次访问，浏览器自动生成UUID
显示欢迎页：输入股票代码开始订阅

李四输入: 比亚迪
系统创建订阅: user_id=web_abc123, target=比亚迪

每5分钟自动刷新页面
显示: "比亚迪最新讨论：XXX"
```

---

## 🔧 后端API设计

### 极简版API

```python
# api/user_api.py

from fastapi import APIRouter
from core.user_manager import UserManager

router = APIRouter(prefix="/api")
user_mgr = UserManager("/data/trendradar.db")

@router.post("/user/register")
def register_user(user_id: str, channel: str, **kwargs):
    """
    注册用户（自动创建）

    Examples:
        - Telegram: user_id="telegram_123456", channel="telegram"
        - Web: user_id="web_abc123", channel="web"
        - 微信: user_id="wechat_oXXXXX", channel="wechat"
    """
    result = user_mgr.register_user(user_id, channel, **kwargs)
    return result

@router.post("/subscription")
def create_subscription(
    user_id: str,
    target: str,
    subscription_type: str = 'stock',
    platforms: list = ['eastmoney'],
    push_channels: list = None
):
    """
    创建订阅

    Example:
        {
            "user_id": "telegram_123456",
            "target": "TSLA",
            "platforms": ["eastmoney", "xueqiu"],
            "push_channels": ["telegram"]
        }
    """
    if push_channels is None:
        # 根据user_id推断推送渠道
        if user_id.startswith('telegram_'):
            push_channels = ['telegram']
        elif user_id.startswith('wechat_'):
            push_channels = ['wechat']
        else:
            push_channels = []

    success, msg, sub_id = user_mgr.create_subscription(
        user_id=user_id,
        subscription_type=subscription_type,
        target=target,
        platforms=platforms,
        push_channels=push_channels
    )

    return {"success": success, "message": msg, "subscription_id": sub_id}

@router.get("/user/{user_id}/subscriptions")
def get_subscriptions(user_id: str):
    """查询用户的订阅列表"""
    subs = user_mgr.get_user_subscriptions(user_id)
    return {"user_id": user_id, "subscriptions": subs}

@router.get("/user/{user_id}/feed")
def get_user_feed(user_id: str, hours: int = 24):
    """
    获取用户的个性化内容推送

    根据用户的订阅列表，返回最新的分析结果
    """
    # 1. 查询用户订阅
    subs = user_mgr.get_user_subscriptions(user_id)

    # 2. 获取每个订阅的最新数据
    feed = []
    for sub in subs:
        # 查询该订阅的最新分析结果
        latest = get_latest_analysis(sub['target'], hours)
        feed.append({
            'subscription': sub,
            'analysis': latest
        })

    return {"user_id": user_id, "feed": feed}
```

---

## 📊 数据流程图

```
用户端
    ↓
[选择渠道] Telegram / 微信 / Web
    ↓
[获取身份ID] telegram_123 / wechat_oXXX / web_abc123
    ↓
后端
    ├─ 自动注册用户（如果不存在）
    ├─ 用户创建订阅（选择关注的股票）
    └─ 保存：user_id → subscriptions
    ↓
定时任务（每30分钟）
    ├─ 遍历所有active订阅
    ├─ 爬取数据 → AI分析
    └─ 推送到对应渠道
    ↓
推送渠道
    ├─ Telegram: 调用Bot API发送消息
    ├─ 微信: 发送模板消息
    └─ Web: 用户轮询/api/user/{user_id}/feed
```

---

## ✅ 总结

### 问题：为什么需要用户身份？

**答案**: 实现个性化订阅！

- 张三关注特斯拉 → 只推送特斯拉相关内容
- 李四关注苹果 → 只推送苹果相关内容
- 如果没有用户ID，所有人看到相同内容 = 没有价值

### 推荐方案

**MVP阶段**: Telegram Bot

- 实现简单
- 免费
- 支持推送
- 50行代码搞定

**后续扩展**: 微信公众号、Web版

---

## 🔧 下一步

1. 创建Telegram Bot（@BotFather）
2. 实现极简版UserManager（已完成）
3. 编写Bot命令处理
4. 测试完整流程

预计1天完成！
