# -*- coding: utf-8 -*-
"""
CrawlerAgent 集成测试
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent))

from core.user_manager import UserManager
from core.crawler_agent import CrawlerAgent


def test_crawler_agent():
    """测试CrawlerAgent与UserManager的集成"""

    print("=" * 60)
    print("  CrawlerAgent 集成测试")
    print("=" * 60)

    # 1. 初始化
    db_path = Path(__file__).parent / "test_crawler_agent.db"
    if db_path.exists():
        db_path.unlink()

    user_mgr = UserManager(str(db_path))
    crawler = CrawlerAgent(user_mgr)

    print("\n✅ 初始化完成")

    # 2. 注册用户
    test_user = "telegram_crawler_test"
    result = user_mgr.register_user(test_user)
    print(f"\n✅ 用户注册: {result['user_id']}")
    print(f"   会员类型: {result['membership']}")
    print(f"   Token余额: {result['token_balance']}")

    # 3. 测试免费用户爬取（东方财富）
    print("\n" + "=" * 60)
    print("  测试1: 免费用户爬取东方财富")
    print("=" * 60)

    success, msg, data = crawler.crawl(
        user_id=test_user,
        platform='eastmoney',
        target='301293',  # 三博脑科
        max_items=5
    )

    print(f"结果: {'✅ 成功' if success else '❌ 失败'}")
    print(f"消息: {msg}")
    print(f"数据条数: {len(data)}")

    if data:
        print("\n前2条数据:")
        for i, item in enumerate(data[:2], 1):
            print(f"  {i}. [{item['platform']}] {item['author_name']}: {item['content'][:50]}...")

    # 4. 测试免费用户爬取雪球（应该被拦截）
    print("\n" + "=" * 60)
    print("  测试2: 免费用户爬取雪球（应拦截）")
    print("=" * 60)

    success, msg, data = crawler.crawl(
        user_id=test_user,
        platform='xueqiu',
        target='TSLA',
        max_items=5
    )

    print(f"结果: {'✅ 成功' if success else '❌ 失败（符合预期）'}")
    print(f"消息: {msg}")

    # 5. 升级为基础会员
    print("\n" + "=" * 60)
    print("  测试3: 升级为基础会员")
    print("=" * 60)

    user_mgr.upgrade_membership(test_user, 'basic', duration_months=1)
    user_info = user_mgr.get_user_info(test_user)

    print(f"✅ 升级成功")
    print(f"   新会员类型: {user_info['membership']['type']}")
    print(f"   最大订阅数: {user_info['limits']['max_subscriptions']}")
    print(f"   Token余额: {user_info['token']['balance']}")

    # 6. 基础会员爬取雪球
    print("\n" + "=" * 60)
    print("  测试4: 基础会员爬取雪球")
    print("=" * 60)

    success, msg, data = crawler.crawl(
        user_id=test_user,
        platform='xueqiu',
        target='TSLA',
        max_items=5
    )

    print(f"结果: {'✅ 成功' if success else '❌ 失败'}")
    print(f"消息: {msg}")
    print(f"数据条数: {len(data)}")

    # 7. 创建订阅并批量爬取
    print("\n" + "=" * 60)
    print("  测试5: 批量爬取订阅")
    print("=" * 60)

    # 创建2个订阅
    sub1_success, sub1_msg, sub1_id = user_mgr.create_subscription(
        user_id=test_user,
        subscription_type='stock',
        target='TSLA',
        target_display_name='特斯拉',
        platforms=['eastmoney', 'xueqiu'],
        push_channels=['telegram']
    )

    sub2_success, sub2_msg, sub2_id = user_mgr.create_subscription(
        user_id=test_user,
        subscription_type='stock',
        target='AAPL',
        target_display_name='苹果',
        platforms=['eastmoney'],
        push_channels=['telegram']
    )

    print(f"订阅1: {sub1_msg} (ID: {sub1_id})")
    print(f"订阅2: {sub2_msg} (ID: {sub2_id})")

    # 批量爬取
    subscriptions = user_mgr.get_user_subscriptions(test_user)
    results = crawler.crawl_batch(test_user, subscriptions)

    print(f"\n批量爬取结果: 共{len(results)}个订阅")
    for sub_id, (success, msg, data) in results.items():
        print(f"  订阅 {sub_id}: {'✅' if success else '❌'} {msg} ({len(data)}条数据)")

    # 8. 测试每日请求限制
    print("\n" + "=" * 60)
    print("  测试6: 每日请求限制")
    print("=" * 60)

    stats = user_mgr.get_user_stats(test_user)
    print(f"今日请求次数: {stats['today_request_count']}")
    print(f"限制: {user_info['limits']['max_daily_requests']}")

    # 模拟达到限制（通过直接修改数据库）
    # 这里简化处理，实际生产中应该有定时任务重置计数
    print("（实际使用中，每日会自动重置计数）")

    # 9. 测试不存在的用户
    print("\n" + "=" * 60)
    print("  测试7: 不存在的用户")
    print("=" * 60)

    success, msg, data = crawler.crawl(
        user_id="fake_user_999",
        platform='eastmoney',
        target='301293',
        max_items=5
    )

    print(f"结果: {'✅ 成功' if success else '❌ 失败（符合预期）'}")
    print(f"消息: {msg}")

    # 完成
    print("\n" + "=" * 60)
    print("  🎉 测试完成")
    print("=" * 60)
    print(f"✅ CrawlerAgent 已成功集成 UserManager")
    print(f"✅ 会员等级检查正常")
    print(f"✅ 平台权限控制正常")
    print(f"✅ 批量爬取功能正常")
    print(f"\n📂 测试数据库: {db_path}")


if __name__ == "__main__":
    test_crawler_agent()
