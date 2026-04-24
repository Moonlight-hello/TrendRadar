# 微信公众号/小程序 支付和会员管理指南

> 版本: 1.0 | 更新: 2026-04-23

---

## 🎯 方案选择

### 方案1：微信官方SDK（推荐）✅

**Python SDK**: `wechatpy`

```bash
pip install wechatpy
```

**功能覆盖**:
- ✅ 微信公众号消息处理
- ✅ 微信支付（JSAPI/H5/扫码）
- ✅ 用户管理（OpenID获取）
- ✅ 模板消息推送
- ✅ 小程序支持

**优点**:
- 官方维护，稳定可靠
- 文档完善
- 社区活跃

---

## 📦 集成方案

### 1. 微信支付集成

```python
# trendradar_server/core/wechat_payment.py

from wechatpy.pay import WeChatPay
from user_manager import UserManager
from typing import Tuple

class WeChatPaymentManager:
    """微信支付管理器"""

    def __init__(self, user_manager: UserManager):
        self.user_mgr = user_manager

        # 微信支付配置
        self.wechat_pay = WeChatPay(
            appid='your_appid',              # 公众号AppID
            api_key='your_api_key',          # 商户API密钥
            mch_id='your_mch_id',            # 商户号
            mch_cert='/path/to/cert.pem',    # 商户证书
            mch_key='/path/to/key.pem'       # 商户密钥
        )

    def create_token_order(
        self,
        user_id: str,
        openid: str,
        package_type: str,  # 'token_10k', 'token_100k'等
        client_ip: str
    ) -> Tuple[bool, str, dict]:
        """
        创建Token充值订单

        Args:
            user_id: 用户ID
            openid: 微信OpenID
            package_type: 套餐类型
            client_ip: 用户IP

        Returns:
            (成功?, 消息, 预支付信息)
        """
        # 1. 获取套餐配置
        from config.membership_rules import TOKEN_PACKAGES

        if package_type not in TOKEN_PACKAGES:
            return False, "无效的套餐类型", {}

        package = TOKEN_PACKAGES[package_type]

        # 2. 创建订单记录
        import uuid
        order_id = str(uuid.uuid4())

        # 插入到 token_purchases 表
        conn = self.user_mgr._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO token_purchases (
                user_id, package_type, token_amount, price,
                payment_method, payment_status, transaction_id
            ) VALUES (?, ?, ?, ?, 'wechat', 'pending', ?)
        """, (user_id, package_type, package['amount'], package['price'], order_id))
        conn.commit()
        conn.close()

        # 3. 调用微信统一下单API
        result = self.wechat_pay.order.create(
            trade_type='JSAPI',              # 公众号支付
            body=f"TrendRadar-{package['name']}",
            out_trade_no=order_id,
            total_fee=int(package['price'] * 100),  # 单位：分
            notify_url='https://your-domain.com/api/wechat/payment/callback',
            user_id=openid,
            client_ip=client_ip
        )

        # 4. 返回预支付信息
        prepay_params = self.wechat_pay.jsapi.get_jsapi_params(result['prepay_id'])

        return True, "订单创建成功", {
            'order_id': order_id,
            'prepay_params': prepay_params  # 前端调用微信支付需要
        }

    def handle_payment_callback(self, xml_data: str) -> Tuple[bool, str]:
        """
        处理微信支付回调

        Args:
            xml_data: 微信回调的XML数据

        Returns:
            (成功?, 消息)
        """
        # 1. 解析和验证回调数据
        result = self.wechat_pay.parse_payment_result(xml_data)

        order_id = result['out_trade_no']
        transaction_id = result['transaction_id']

        # 2. 查询订单
        conn = self.user_mgr._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT user_id, token_amount, payment_status
            FROM token_purchases
            WHERE transaction_id = ?
        """, (order_id,))
        row = cursor.fetchone()

        if not row:
            return False, "订单不存在"

        user_id = row['user_id']
        token_amount = row['token_amount']
        payment_status = row['payment_status']

        if payment_status == 'completed':
            return True, "订单已处理"

        # 3. 更新订单状态
        from datetime import datetime
        now = datetime.now().isoformat()

        cursor.execute("""
            UPDATE token_purchases
            SET payment_status = 'completed', paid_at = ?
            WHERE transaction_id = ?
        """, (now, order_id))

        # 4. 增加用户Token余额
        self.user_mgr.add_token(
            user_id=user_id,
            amount=token_amount,
            source='purchase',
            transaction_id=transaction_id
        )

        conn.commit()
        conn.close()

        return True, "支付成功，Token已充值"

    def create_membership_order(
        self,
        user_id: str,
        openid: str,
        membership_type: str,  # 'basic', 'pro'
        duration_months: int,
        client_ip: str
    ) -> Tuple[bool, str, dict]:
        """创建会员订单（类似Token订单）"""
        from config.membership_rules import MEMBERSHIP_TIERS

        if membership_type not in MEMBERSHIP_TIERS:
            return False, "无效的会员类型", {}

        tier = MEMBERSHIP_TIERS[membership_type]
        price = tier['price_monthly'] * duration_months

        # 类似Token订单流程...
        # ...

        return True, "会员订单创建成功", {}
```

---

### 2. 会员过期检查（定时任务）

```python
# trendradar_server/core/membership_scheduler.py

from apscheduler.schedulers.background import BackgroundScheduler
from user_manager import UserManager
from datetime import datetime, timedelta
import sqlite3

class MembershipScheduler:
    """会员过期检查和自动续费管理"""

    def __init__(self, user_manager: UserManager):
        self.user_mgr = user_manager
        self.scheduler = BackgroundScheduler()

    def start(self):
        """启动定时任务"""

        # 每天凌晨2点检查会员过期
        self.scheduler.add_job(
            self.check_expired_memberships,
            'cron',
            hour=2,
            minute=0
        )

        # 每月1号发放会员Token
        self.scheduler.add_job(
            self.grant_monthly_tokens,
            'cron',
            day=1,
            hour=0,
            minute=0
        )

        # 每天凌晨重置每日请求计数
        self.scheduler.add_job(
            self.reset_daily_limits,
            'cron',
            hour=0,
            minute=0
        )

        self.scheduler.start()
        print("✅ 会员管理定时任务已启动")

    def check_expired_memberships(self):
        """检查并处理过期会员"""
        conn = self.user_mgr._get_connection()
        cursor = conn.cursor()

        now = datetime.now().isoformat()

        # 查找所有过期会员
        cursor.execute("""
            SELECT user_id, membership_type, membership_end_date
            FROM users
            WHERE membership_status = 'active'
              AND membership_end_date IS NOT NULL
              AND membership_end_date < ?
        """, (now,))

        expired_users = cursor.fetchall()

        for row in expired_users:
            user_id = row['user_id']

            # 更新为过期状态
            cursor.execute("""
                UPDATE users
                SET membership_status = 'expired',
                    membership_type = 'free',
                    max_subscriptions = 3,
                    max_daily_requests = 10
                WHERE user_id = ?
            """, (user_id,))

            print(f"⚠️  用户 {user_id} 会员已过期")

            # TODO: 发送过期通知（微信模板消息）
            # self.send_expiry_notification(user_id)

        conn.commit()
        conn.close()

        if expired_users:
            print(f"✅ 处理了 {len(expired_users)} 个过期会员")

    def grant_monthly_tokens(self):
        """每月发放会员Token"""
        conn = self.user_mgr._get_connection()
        cursor = conn.cursor()

        from config.membership_rules import MEMBERSHIP_TIERS

        # 查找所有活跃会员
        cursor.execute("""
            SELECT user_id, membership_type
            FROM users
            WHERE membership_status = 'active'
              AND membership_type != 'free'
        """)

        members = cursor.fetchall()

        for row in members:
            user_id = row['user_id']
            membership_type = row['membership_type']

            # 获取每月Token额度
            tier = MEMBERSHIP_TIERS[membership_type]
            monthly_tokens = tier['monthly_tokens']

            # 发放Token
            cursor.execute("""
                UPDATE users
                SET token_balance = token_balance + ?
                WHERE user_id = ?
            """, (monthly_tokens, user_id))

            print(f"✅ 用户 {user_id} 获得每月Token: {monthly_tokens}")

        conn.commit()
        conn.close()

        if members:
            print(f"✅ 已为 {len(members)} 个会员发放每月Token")

    def reset_daily_limits(self):
        """重置每日请求计数（如果需要）"""
        # 如果你在数据库中存储了每日计数，在这里重置
        # 或者使用Redis存储，设置过期时间为1天
        pass

    def stop(self):
        """停止定时任务"""
        self.scheduler.shutdown()
```

---

### 3. 微信公众号消息处理

```python
# trendradar_server/api/wechat_api.py

from fastapi import APIRouter, Request, Response
from wechatpy import parse_message, create_reply
from wechatpy.utils import check_signature
from wechatpy.exceptions import InvalidSignatureException
from core.user_manager import UserManager

router = APIRouter(prefix="/api/wechat")

WECHAT_TOKEN = "your_wechat_token"  # 公众号配置的Token
user_mgr = UserManager("/path/to/trendradar.db")

@router.get("/message")
async def wechat_verify(
    signature: str,
    timestamp: str,
    nonce: str,
    echostr: str
):
    """微信服务器验证"""
    try:
        check_signature(WECHAT_TOKEN, signature, timestamp, nonce)
        return Response(content=echostr)
    except InvalidSignatureException:
        return Response(content="Invalid signature", status_code=403)

@router.post("/message")
async def wechat_message(request: Request):
    """处理微信消息"""
    xml_data = await request.body()

    # 解析消息
    msg = parse_message(xml_data)

    # 处理不同类型消息
    if msg.type == 'text':
        # 文本消息
        user_openid = msg.source
        content = msg.content

        # 自动注册用户
        user_id = f"wechat_{user_openid}"
        if not user_mgr.user_exists(user_id):
            user_mgr.register_user(user_id, channel='wechat')

        # 命令处理
        if content == '查询余额':
            user_info = user_mgr.get_user_info(user_id)
            reply_text = f"Token余额：{user_info['token']['balance']}\n会员类型：{user_info['membership']['type']}"
            reply = create_reply(reply_text, msg)

        elif content == '我的订阅':
            subs = user_mgr.get_user_subscriptions(user_id)
            reply_text = f"当前订阅数：{len(subs)}\n" + "\n".join([f"{i+1}. {s['display_name']}" for i, s in enumerate(subs)])
            reply = create_reply(reply_text, msg)

        else:
            reply_text = "欢迎使用TrendRadar！\n回复"查询余额"查看Token余额\n回复"我的订阅"查看订阅列表"
            reply = create_reply(reply_text, msg)

        return Response(content=reply.render(), media_type='application/xml')

    elif msg.type == 'event':
        # 事件消息（关注/取消关注）
        if msg.event == 'subscribe':
            # 用户关注公众号
            user_openid = msg.source
            user_id = f"wechat_{user_openid}"

            # 自动注册
            result = user_mgr.register_user(user_id, channel='wechat')

            welcome_text = f"感谢关注TrendRadar！\n{result['welcome_message']}\n\n回复"帮助"查看使用指南"
            reply = create_reply(welcome_text, msg)
            return Response(content=reply.render(), media_type='application/xml')

    return Response(content='success')
```

---

## 🔧 FastAPI完整集成

```python
# trendradar_server/main.py

from fastapi import FastAPI
from core.user_manager import UserManager
from core.wechat_payment import WeChatPaymentManager
from core.membership_scheduler import MembershipScheduler
from api.wechat_api import router as wechat_router

app = FastAPI(title="TrendRadar Server")

# 初始化
user_mgr = UserManager("/data/trendradar.db")
payment_mgr = WeChatPaymentManager(user_mgr)
scheduler = MembershipScheduler(user_mgr)

# 启动定时任务
scheduler.start()

# 注册路由
app.include_router(wechat_router)

@app.on_event("shutdown")
def shutdown_event():
    scheduler.stop()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

## 📱 前端接入示例

### 微信小程序调用支付

```javascript
// 小程序端

// 1. 创建订单
wx.request({
  url: 'https://your-domain.com/api/wechat/create-order',
  method: 'POST',
  data: {
    user_id: 'telegram_123',
    package_type: 'token_100k'
  },
  success: (res) => {
    const { prepay_params } = res.data;

    // 2. 调起微信支付
    wx.requestPayment({
      ...prepay_params,
      success: () => {
        wx.showToast({ title: '支付成功', icon: 'success' });
        // 刷新余额
      },
      fail: () => {
        wx.showToast({ title: '支付失败', icon: 'none' });
      }
    });
  }
});
```

---

## 🎁 其他推荐SDK

### 1. **支付宝支付**

```bash
pip install alipay-sdk-python
```

### 2. **Stripe（国际支付）**

```bash
pip install stripe
```

### 3. **统一支付网关（推荐）**

如果你需要支持多种支付方式，推荐使用：

**Ping++**（https://www.pingxx.com/）
- 支持微信、支付宝、银联等
- 统一API接口
- Python SDK完善

```bash
pip install pingpp
```

---

## 📊 数据流程图

```
用户端（微信/小程序）
    ↓
[选择套餐] → [调起支付]
    ↓
TrendRadar Server
    ├─ 创建订单（pending）
    ├─ 调用微信统一下单API
    └─ 返回预支付信息
    ↓
微信支付服务器
    ├─ 用户完成支付
    └─ 回调通知 TrendRadar
    ↓
TrendRadar Server
    ├─ 验证回调签名
    ├─ 更新订单状态（completed）
    └─ 增加用户Token/升级会员
    ↓
定时任务（APScheduler）
    ├─ 每天检查会员过期
    ├─ 每月发放会员Token
    └─ 发送通知消息
```

---

## ✅ 总结

**你不需要自己写付费和过期管理系统！**

推荐方案：
1. ✅ **微信支付**: 使用 `wechatpy` SDK
2. ✅ **会员过期**: 使用 `APScheduler` 定时任务
3. ✅ **用户管理**: 已有的 `UserManager` 类
4. ✅ **支付回调**: FastAPI + wechatpy

**代码量估计**:
- 微信支付集成: ~200行
- 定时任务: ~100行
- 微信消息处理: ~150行
- **总计**: ~450行代码即可完成

**开发时间估计**: 2-3天（包括测试）

---

## 📚 参考文档

- wechatpy文档: https://wechatpy.readthedocs.io/
- 微信支付官方文档: https://pay.weixin.qq.com/
- APScheduler文档: https://apscheduler.readthedocs.io/
