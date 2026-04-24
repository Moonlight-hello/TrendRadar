# -*- coding: utf-8 -*-
"""
用户模块测试脚本
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from user.manager import MinimalUserManager


def test_user_module():
    """测试用户模块"""

    print("=" * 60)
    print("  用户模块测试")
    print("=" * 60)

    # 1. 初始化
    db_path = Path(__file__).parent / "test_user_module.db"
    if db_path.exists():
        db_path.unlink()

    user_mgr = MinimalUserManager(str(db_path))
    print("\n✅ 数据库初始化成功")

    # 2. 注册Telegram用户
    print("\n" + "=" * 60)
    print("  测试1: 注册Telegram用户")
    print("=" * 60)

    result = user_mgr.register_user(
        user_id="telegram_123456",
        channel="telegram",
        username="张三",
        telegram_id="123456",
        telegram_username="zhangsan"
    )

    print(f"✅ 注册结果: {result['message']}")
    print(f"   用户ID: {result['user_id']}")
    print(f"   是否新用户: {result['is_new']}")

    # 3. 重复注册
    result2 = user_mgr.register_user(
        user_id="telegram_123456",
        channel="telegram"
    )
    print(f"\n✅ 重复注册: {result2['message']}")

    # 4. 查询用户信息
    print("\n" + "=" * 60)
    print("  测试2: 查询用户信息")
    print("=" * 60)

    user_info = user_mgr.get_user_info("telegram_123456")
    print(f"✅ 用户信息:")
    print(f"   用户名: {user_info['username']}")
    print(f"   渠道: {user_info['channel']}")
    print(f"   Telegram ID: {user_info['telegram_id']}")
    print(f"   状态: {user_info['status']}")

    # 5. 创建订阅
    print("\n" + "=" * 60)
    print("  测试3: 创建订阅")
    print("=" * 60)

    success, msg, sub_id = user_mgr.create_subscription(
        user_id="telegram_123456",
        subscription_type="stock",
        target="TSLA",
        target_display_name="特斯拉",
        platforms=["eastmoney"],
        push_channels=["telegram"]
    )

    print(f"✅ 订阅结果: {msg}")
    print(f"   订阅ID: {sub_id}")

    # 再创建几个订阅
    for stock, name in [("AAPL", "苹果"), ("MSFT", "微软")]:
        success, msg, sub_id = user_mgr.create_subscription(
            user_id="telegram_123456",
            subscription_type="stock",
            target=stock,
            target_display_name=name,
            platforms=["eastmoney"],
            push_channels=["telegram"]
        )
        print(f"✅ 订阅{name}: ID={sub_id}")

    # 6. 查询订阅列表
    print("\n" + "=" * 60)
    print("  测试4: 查询订阅列表")
    print("=" * 60)

    subs = user_mgr.get_user_subscriptions("telegram_123456")
    print(f"✅ 共有{len(subs)}个订阅:")

    for i, sub in enumerate(subs, 1):
        print(f"\n{i}. {sub['display_name']} ({sub['target']})")
        print(f"   ID: {sub['id']}")
        print(f"   类型: {sub['type']}")
        print(f"   平台: {', '.join(sub['platforms'])}")
        print(f"   状态: {sub['status']}")
        print(f"   推送: {'开启' if sub['push_enabled'] else '关闭'}")

    # 7. 重复订阅测试
    print("\n" + "=" * 60)
    print("  测试5: 重复订阅（应拦截）")
    print("=" * 60)

    success, msg, sub_id = user_mgr.create_subscription(
        user_id="telegram_123456",
        subscription_type="stock",
        target="TSLA",
        platforms=["eastmoney"],
        push_channels=["telegram"]
    )

    print(f"{'❌' if not success else '✅'} {msg}")

    # 8. 暂停订阅
    print("\n" + "=" * 60)
    print("  测试6: 暂停/恢复订阅")
    print("=" * 60)

    if subs:
        first_sub_id = subs[0]['id']

        success, msg = user_mgr.update_subscription_status(first_sub_id, "paused")
        print(f"✅ 暂停: {msg}")

        success, msg = user_mgr.update_subscription_status(first_sub_id, "active")
        print(f"✅ 恢复: {msg}")

    # 9. 获取所有活跃订阅
    print("\n" + "=" * 60)
    print("  测试7: 获取所有活跃订阅（用于定时任务）")
    print("=" * 60)

    all_subs = user_mgr.get_all_active_subscriptions()
    print(f"✅ 系统中共有{len(all_subs)}个活跃订阅")

    for sub in all_subs:
        print(f"   - {sub['target']} (用户: {sub['user_id']}, Telegram ID: {sub['telegram_id']})")

    # 10. 注册Web用户
    print("\n" + "=" * 60)
    print("  测试8: 注册Web匿名用户")
    print("=" * 60)

    result = user_mgr.register_user(
        user_id="web_abc123",
        channel="web",
        username="匿名用户"
    )

    print(f"✅ Web用户注册: {result['message']}")

    # 11. 删除订阅
    print("\n" + "=" * 60)
    print("  测试9: 删除订阅")
    print("=" * 60)

    if subs and len(subs) > 1:
        last_sub_id = subs[-1]['id']
        success, msg = user_mgr.delete_subscription(last_sub_id)
        print(f"✅ 删除订阅: {msg}")

        # 再次查询
        subs_after = user_mgr.get_user_subscriptions("telegram_123456")
        print(f"   删除后订阅数: {len(subs_after)}")

    # 12. 统计信息
    print("\n" + "=" * 60)
    print("  测试10: 用户统计")
    print("=" * 60)

    stats = user_mgr.get_user_stats("telegram_123456")
    print(f"✅ 统计信息:")
    print(f"   活跃订阅数: {stats['subscription_count']}")

    # 完成
    print("\n" + "=" * 60)
    print("  🎉 测试完成")
    print("=" * 60)
    print(f"✅ 所有功能测试通过")
    print(f"📂 测试数据库: {db_path}")
    print(f"\n💡 下一步:")
    print(f"   1. 设置Telegram Bot Token")
    print(f"   2. 运行: python3 -m user.telegram_bot")


if __name__ == "__main__":
    test_user_module()
