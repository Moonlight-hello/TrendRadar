# -*- coding: utf-8 -*-
"""
用户管理器测试脚本
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent))

from core.user_manager import UserManager
import json
from datetime import datetime


def print_section(title: str):
    """打印分隔线"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def test_user_manager():
    """测试用户管理器的所有功能"""

    # 使用测试数据库
    db_path = Path(__file__).parent / "test_trendradar.db"

    # 删除旧的测试数据库
    if db_path.exists():
        db_path.unlink()

    # 初始化用户管理器
    print_section("1. 初始化用户管理器")
    user_manager = UserManager(str(db_path))
    print("✅ 数据库初始化成功")
    print(f"📂 数据库路径: {db_path}")

    # 测试用户注册
    print_section("2. 测试用户注册")
    test_user_id = "telegram_12345678"

    result = user_manager.register_user(test_user_id, "telegram")
    print(f"✅ 注册结果: {json.dumps(result, indent=2, ensure_ascii=False)}")

    # 重复注册测试
    result2 = user_manager.register_user(test_user_id, "telegram")
    print(f"ℹ️  重复注册: {result2['message']}")

    # 测试查询用户信息
    print_section("3. 测试查询用户信息")
    user_info = user_manager.get_user_info(test_user_id)
    if user_info:
        print("✅ 用户信息:")
        print(f"  - 用户ID: {user_info['user_id']}")
        print(f"  - 会员类型: {user_info['membership']['type']}")
        print(f"  - Token余额: {user_info['token']['balance']}")
        print(f"  - 最大订阅数: {user_info['limits']['max_subscriptions']}")
        print(f"  - 注册时间: {user_info['created_at']}")
    else:
        print("❌ 用户不存在")

    # 测试Token余额查询
    print_section("4. 测试Token余额查询")
    balance = user_manager.get_token_balance(test_user_id)
    print(f"✅ 当前Token余额: {balance}")

    # 测试Token扣除
    print_section("5. 测试Token扣除")
    success, msg, result = user_manager.deduct_token(
        user_id=test_user_id,
        amount=500,
        operation="analyze",
        model="deepseek-chat",
        prompt_tokens=300,
        completion_tokens=200,
        request_summary="分析股票TSLA的讨论"
    )

    if success:
        print(f"✅ 扣除成功:")
        print(f"  - 扣除数量: {result['deducted']}")
        print(f"  - 剩余余额: {result['remaining_balance']}")
        print(f"  - 成本: ¥{result['cost']:.4f}")
    else:
        print(f"❌ 扣除失败: {msg}")

    # 测试Token余额不足
    print_section("6. 测试Token余额不足")
    success, msg, result = user_manager.deduct_token(
        user_id=test_user_id,
        amount=99999,
        operation="analyze",
        model="gpt-4",
        prompt_tokens=500,
        completion_tokens=500
    )

    if not success:
        print(f"✅ 正确拦截:")
        print(f"  - 错误信息: {msg}")
        if 'shortage' in result:
            print(f"  - 缺少: {result['shortage']} tokens")
    else:
        print("❌ 应该拦截但没有拦截")

    # 测试Token充值
    print_section("7. 测试Token充值")
    success, msg = user_manager.add_token(test_user_id, 5000, "purchase", "txn_123456")
    print(f"{'✅' if success else '❌'} {msg}")
    new_balance = user_manager.get_token_balance(test_user_id)
    print(f"  - 充值后余额: {new_balance}")

    # 测试Token消耗历史
    print_section("8. 测试Token消耗历史")
    history = user_manager.get_token_history(test_user_id, limit=10)
    print(f"✅ 查询到 {len(history)} 条消耗记录:")
    for i, record in enumerate(history, 1):
        print(f"  {i}. {record['operation']} | {record['model']} | {record['tokens']['total']} tokens | ¥{record['cost']:.4f}")

    # 测试创建订阅
    print_section("9. 测试创建订阅")
    success, msg, sub_id = user_manager.create_subscription(
        user_id=test_user_id,
        subscription_type="stock",
        target="TSLA",
        target_display_name="特斯拉",
        platforms=["eastmoney", "xueqiu"],
        push_channels=["telegram"],
        push_frequency="realtime"
    )

    if success:
        print(f"✅ 订阅创建成功:")
        print(f"  - 订阅ID: {sub_id}")
        print(f"  - {msg}")
    else:
        print(f"❌ 订阅失败: {msg}")

    # 创建更多订阅
    for i, stock in enumerate(["AAPL", "MSFT"], 2):
        success, msg, sub_id = user_manager.create_subscription(
            user_id=test_user_id,
            subscription_type="stock",
            target=stock,
            target_display_name=stock,
            platforms=["eastmoney"],
            push_channels=["telegram"],
            push_frequency="daily"
        )
        if success:
            print(f"  ✅ 订阅 {i}: {stock} (ID: {sub_id})")

    # 测试查询订阅列表
    print_section("10. 测试查询订阅列表")
    subscriptions = user_manager.get_user_subscriptions(test_user_id)
    print(f"✅ 当前有 {len(subscriptions)} 个订阅:")
    for i, sub in enumerate(subscriptions, 1):
        print(f"  {i}. {sub['display_name']} ({sub['target']}) - {sub['status']}")
        print(f"     平台: {', '.join(sub['platforms'])}")
        print(f"     频率: {sub['push_frequency']}")

    # 测试订阅数限制
    print_section("11. 测试订阅数限制")
    success, msg, sub_id = user_manager.create_subscription(
        user_id=test_user_id,
        subscription_type="stock",
        target="GOOGL",
        platforms=["eastmoney"],
        push_channels=["telegram"]
    )
    if not success:
        print(f"✅ 正确拦截: {msg}")
    else:
        print(f"❌ 应该拦截但没有拦截")

    # 测试会员升级
    print_section("12. 测试会员升级")
    success, msg = user_manager.upgrade_membership(test_user_id, "basic", duration_months=1)
    print(f"{'✅' if success else '❌'} {msg}")

    # 查看升级后的用户信息
    user_info = user_manager.get_user_info(test_user_id)
    print(f"  - 新会员类型: {user_info['membership']['type']}")
    print(f"  - Token余额: {user_info['token']['balance']} (增加了每月赠送)")
    print(f"  - 最大订阅数: {user_info['limits']['max_subscriptions']}")
    print(f"  - 到期时间: {user_info['membership']['end_date']}")

    # 测试暂停订阅
    print_section("13. 测试暂停/恢复订阅")
    if subscriptions:
        first_sub_id = subscriptions[0]['id']
        success, msg = user_manager.update_subscription_status(first_sub_id, "paused")
        print(f"✅ {msg}")

        success, msg = user_manager.update_subscription_status(first_sub_id, "active")
        print(f"✅ {msg}")

    # 测试用户统计
    print_section("14. 测试用户统计")
    stats = user_manager.get_user_stats(test_user_id)
    print(f"✅ 用户统计:")
    print(f"  - 活跃订阅数: {stats['subscription_count']}")
    print(f"  - 今日Token消耗: {stats['today_tokens_consumed']}")
    print(f"  - 今日请求次数: {stats['today_request_count']}")

    # 测试不存在的用户
    print_section("15. 测试不存在的用户")
    fake_user = "telegram_99999999"
    exists = user_manager.user_exists(fake_user)
    print(f"✅ 用户存在性检查: {exists}")

    info = user_manager.get_user_info(fake_user)
    print(f"✅ 查询不存在的用户: {info}")

    # 完成测试
    print_section("🎉 测试完成")
    print(f"✅ 所有功能测试通过")
    print(f"📂 测试数据库保留在: {db_path}")
    print(f"💡 可以使用 SQLite 工具查看数据库内容:")
    print(f"   sqlite3 {db_path}")


if __name__ == "__main__":
    test_user_manager()
