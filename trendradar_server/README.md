# TrendRadar Server - 用户管理系统

> 版本: 1.0 | 更新: 2026-04-23

## 📦 项目结构

```
trendradar_server/
├── db/
│   └── schema.sql              # 数据库表设计（9张表）
├── config/
│   └── membership_rules.py     # 会员规则配置
├── core/
│   └── user_manager.py         # 用户管理核心类（供Agent调用）
├── tests/
│   └── test_user_manager.py    # 测试脚本
└── README.md                   # 本文档
```

---

## 🚀 快速开始

### 1. 运行测试

```bash
cd /Users/wangxinlong/Code/TrendRadarRepository/TrendRadar/trendradar_server

# 运行测试脚本
python tests/test_user_manager.py
```

测试将验证：
- ✅ 用户注册
- ✅ 用户信息查询
- ✅ Token余额管理
- ✅ Token扣除和充值
- ✅ 会员升级
- ✅ 订阅管理
- ✅ 限制检查

### 2. 在Agent中使用

```python
from core.user_manager import UserManager

# 初始化（指定数据库路径）
user_mgr = UserManager("/path/to/trendradar.db")

# 注册用户
result = user_mgr.register_user("telegram_123", "telegram")
print(result)  # {'success': True, 'token_balance': 10000, ...}

# 查询用户信息
user_info = user_mgr.get_user_info("telegram_123")
print(f"Token余额: {user_info['token']['balance']}")

# 扣除Token（AI调用后）
success, msg, result = user_mgr.deduct_token(
    user_id="telegram_123",
    amount=500,
    operation="analyze",
    model="deepseek-chat",
    prompt_tokens=300,
    completion_tokens=200
)

if success:
    print(f"剩余余额: {result['remaining_balance']}")
else:
    print(f"扣除失败: {msg}")  # 余额不足时会失败

# 创建订阅
success, msg, sub_id = user_mgr.create_subscription(
    user_id="telegram_123",
    subscription_type="stock",
    target="TSLA",
    platforms=["eastmoney", "xueqiu"],
    push_channels=["telegram"]
)

# 查询订阅列表
subs = user_mgr.get_user_subscriptions("telegram_123")
for sub in subs:
    print(f"{sub['display_name']}: {sub['status']}")
```

---

## 📊 数据库表设计

### 核心表

| 表名 | 说明 | 主要字段 |
|------|------|---------|
| `users` | 用户账户表 | user_id, membership_type, token_balance |
| `subscriptions` | 用户订阅表 | user_id, target, platforms, status |
| `token_usage` | Token消耗记录 | user_id, model, total_tokens, cost |
| `token_purchases` | 充值记录 | user_id, amount, price, payment_status |
| `membership_orders` | 会员订单 | user_id, membership_type, end_date |
| `tasks` | 任务队列 | task_type, platform, target, status |
| `raw_data` | 原始爬取数据 | platform, content, publish_time |
| `analysis_results` | AI分析结果 | target, summary, sentiment |
| `push_history` | 推送记录 | subscription_id, channel, status |

完整表结构见：`db/schema.sql`

---

## 🔧 UserManager API 文档

### 用户管理

#### `register_user(user_id, channel='telegram')`
注册新用户（首次使用自动注册）

**返回**:
```python
{
    'success': True,
    'user_id': 'telegram_123',
    'is_new': True,
    'token_balance': 10000,
    'membership': 'free'
}
```

#### `get_user_info(user_id)`
查询用户详细信息

**返回**:
```python
{
    'user_id': 'telegram_123',
    'membership': {
        'type': 'free',
        'status': 'active',
        'is_expired': False
    },
    'token': {
        'balance': 9500,
        'total_consumed': 500
    },
    'limits': {
        'max_subscriptions': 3,
        'max_daily_requests': 10
    }
}
```

#### `user_exists(user_id) -> bool`
检查用户是否存在

---

### Token管理

#### `get_token_balance(user_id) -> int`
查询Token余额

#### `deduct_token(user_id, amount, operation, model, ...)`
扣除Token（AI调用时使用）

**参数**:
- `user_id`: 用户ID
- `amount`: 扣除数量
- `operation`: 操作类型(analyze/summarize/verify)
- `model`: AI模型名称
- `subscription_id`: 关联订阅ID（可选）
- `prompt_tokens`: 输入token数
- `completion_tokens`: 输出token数

**返回**: `(成功?, 消息, 结果字典)`

```python
success, msg, result = user_mgr.deduct_token(
    user_id="telegram_123",
    amount=500,
    operation="analyze",
    model="deepseek-chat",
    prompt_tokens=300,
    completion_tokens=200
)

if success:
    print(result['remaining_balance'])  # 剩余余额
else:
    print(msg)  # "Token余额不足..."
```

#### `add_token(user_id, amount, source='purchase')`
增加Token（充值或赠送）

#### `get_token_history(user_id, limit=50)`
查询Token消耗历史

---

### 会员管理

#### `upgrade_membership(user_id, membership_type, duration_months=1)`
升级会员

**参数**:
- `membership_type`: 'basic' / 'pro' / 'enterprise'
- `duration_months`: 购买时长（月）

#### `check_membership_valid(user_id) -> bool`
检查会员是否有效（未过期）

---

### 订阅管理

#### `create_subscription(user_id, subscription_type, target, platforms, push_channels, ...)`
创建订阅

**参数**:
- `subscription_type`: 订阅类型(stock/topic/keyword)
- `target`: 目标内容(如: "TSLA")
- `platforms`: 数据源平台列表(如: ["eastmoney", "xueqiu"])
- `push_channels`: 推送渠道(如: ["telegram"])
- `push_frequency`: 推送频率(realtime/hourly/daily)

**返回**: `(成功?, 消息, 订阅ID)`

#### `get_user_subscriptions(user_id, status='active')`
查询用户订阅列表

#### `update_subscription_status(subscription_id, status)`
更新订阅状态(active/paused/cancelled)

---

### 统计查询

#### `get_user_stats(user_id)`
获取用户统计信息

**返回**:
```python
{
    'subscription_count': 3,
    'today_tokens_consumed': 1500,
    'today_request_count': 5
}
```

---

## 💰 会员规则

### 会员等级

| 等级 | 月费 | Token额度 | 最大订阅数 | 支持平台 |
|------|------|-----------|-----------|---------|
| **Free** | ¥0 | 10000(注册赠送) | 3 | 东方财富 |
| **Basic** | ¥29.9 | 100000/月 | 10 | 东财/雪球/知乎 |
| **Pro** | ¥99.9 | 500000/月 | 50 | 全平台 |
| **Enterprise** | ¥999 | 9999999/月 | 999 | 全平台+定制 |

详见：`config/membership_rules.py`

### Token成本

| 模型 | 成本(元/1k tokens) |
|------|-------------------|
| deepseek-chat | 0.001 |
| gpt-3.5-turbo | 0.014 |
| gpt-4-turbo | 0.07 |
| gpt-4 | 0.21 |

---

## 🔌 集成示例

### Agent调用示例

```python
# 在 AnalyzerAgent 中使用

class AnalyzerAgent:
    def __init__(self, user_manager: UserManager):
        self.user_mgr = user_manager

    def analyze(self, user_id: str, data: List[Dict]) -> Dict:
        # 1. 检查会员是否有效
        if not self.user_mgr.check_membership_valid(user_id):
            return {'error': '会员已过期，请续费'}

        # 2. 调用AI分析
        prompt = f"分析以下{len(data)}条数据..."
        response = ai_client.chat(prompt)

        # 3. 扣除Token
        success, msg, result = self.user_mgr.deduct_token(
            user_id=user_id,
            amount=response.total_tokens,
            operation="analyze",
            model="deepseek-chat",
            prompt_tokens=response.prompt_tokens,
            completion_tokens=response.completion_tokens
        )

        if not success:
            return {'error': msg}  # Token不足

        return {
            'summary': response.content,
            'tokens_used': result['deducted'],
            'remaining_balance': result['remaining_balance']
        }
```

---

## 🧪 测试覆盖

测试脚本 `tests/test_user_manager.py` 覆盖了15个测试场景：

1. ✅ 数据库初始化
2. ✅ 用户注册（含重复注册）
3. ✅ 查询用户信息
4. ✅ Token余额查询
5. ✅ Token扣除（成功场景）
6. ✅ Token余额不足拦截
7. ✅ Token充值
8. ✅ Token消耗历史查询
9. ✅ 创建订阅
10. ✅ 查询订阅列表
11. ✅ 订阅数限制拦截
12. ✅ 会员升级
13. ✅ 订阅状态更新
14. ✅ 用户统计
15. ✅ 不存在用户处理

运行测试查看完整输出。

---

## 📝 注意事项

### 关于 APIRouter

你问的 `router = APIRouter(prefix="/api/user", tags=["用户管理"])` 是 FastAPI 的写法。

**我们不使用它**，因为：
- ❌ FastAPI Router 是HTTP接口，需要启动Web服务
- ✅ 我们封装的是 **Python类 (UserManager)**，可以直接在代码中调用

**区别**:
```python
# FastAPI写法（HTTP接口）
@router.post("/register")
def register_user(user_id: str):
    ...

# 需要：uvicorn启动服务 → HTTP请求 → 响应

# 我们的写法（直接调用）
user_mgr = UserManager(db_path)
result = user_mgr.register_user(user_id)

# 直接在Python代码中调用，无需HTTP
```

---

## 🚀 进度

1. ✅ 数据库表设计完成
2. ✅ 用户管理工具类完成（UserManager）
3. ✅ 测试脚本完成（15个测试场景通过）
4. ✅ **CrawlerAgent集成完成**（支持会员检查、平台权限控制）
5. ⏳ 集成到 AnalyzerAgent
6. ⏳ 微信公众号/支付集成（有完整方案，见docs/）

---

## 📱 新增：微信支付和会员管理

完整指南见：`docs/WECHAT_PAYMENT_GUIDE.md`

**核心SDK**:
- `wechatpy` - 微信公众号/支付SDK
- `apscheduler` - 定时任务（会员过期检查）

**功能**:
- ✅ 微信支付集成（统一下单、回调处理）
- ✅ 会员过期自动检查（每天凌晨）
- ✅ 每月自动发放会员Token
- ✅ 微信公众号消息处理

**不需要自己写**：现成SDK已完全覆盖！

---

## 📞 联系

- 项目: TrendRadar
- 版本: 1.0
- 日期: 2026-04-23
