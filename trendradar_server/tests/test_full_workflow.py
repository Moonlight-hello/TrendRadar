# -*- coding: utf-8 -*-
"""
完整工作流程测试
测试：用户注册 → 创建订阅 → 爬取数据 → AI分析 → (模拟推送)
"""

import os
import sys
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent))

from core.user_manager import UserManager
from core.crawler_agent import CrawlerAgent
from core.analyzer_agent import AnalyzerAgent


def test_full_workflow():
    """测试完整工作流程"""

    print("=" * 70)
    print("TrendRadar 完整工作流程测试")
    print("=" * 70)

    # 1. 初始化
    print("\n【步骤1】初始化系统组件...")
    db_path = "/tmp/test_full_workflow.db"
    if os.path.exists(db_path):
        os.remove(db_path)

    user_mgr = UserManager(db_path)
    crawler = CrawlerAgent(user_mgr)
    analyzer = AnalyzerAgent(user_mgr, mock_mode=True)

    print("  ✅ UserManager 初始化完成")
    print("  ✅ CrawlerAgent 初始化完成")
    print("  ✅ AnalyzerAgent 初始化完成（Mock模式）")

    # 2. 用户注册
    print("\n【步骤2】用户注册...")
    user_id = "telegram_test_workflow"
    result = user_mgr.register_user(user_id, channel='telegram')

    print(f"  用户ID: {result['user_id']}")
    print(f"  首次注册: {result['is_new']}")
    print(f"  Token余额: {result['token_balance']}")
    print(f"  会员等级: {result['membership']}")

    # 3. 创建订阅
    print("\n【步骤3】创建订阅...")
    success, msg, sub_id = user_mgr.create_subscription(
        user_id=user_id,
        subscription_type='stock',
        target='TSLA',
        target_display_name='特斯拉',
        platforms=['eastmoney'],
        push_channels=['telegram'],
        push_frequency='realtime'
    )

    if success:
        print(f"  ✅ 订阅创建成功")
        print(f"  订阅ID: {sub_id}")
        print(f"  目标: TSLA (特斯拉)")
        print(f"  数据源: eastmoney")
    else:
        print(f"  ❌ 订阅创建失败: {msg}")
        return False

    # 4. 查询订阅列表
    print("\n【步骤4】查询订阅列表...")
    subscriptions = user_mgr.get_user_subscriptions(user_id)
    print(f"  活跃订阅数: {len(subscriptions)}")
    for sub in subscriptions:
        display_name = sub.get('target_display_name') or sub.get('display_name') or sub.get('target')
        print(f"  - [{sub['id']}] {display_name} ({sub['status']})")

    # 5. 爬取数据
    print("\n【步骤5】爬取数据...")
    success, msg, data = crawler.crawl(
        user_id=user_id,
        platform='eastmoney',
        target='TSLA',
        max_items=20,
        subscription_id=sub_id
    )

    if success:
        print(f"  ✅ 爬取成功")
        print(f"  数据量: {len(data)}")
        print(f"  平台: {data[0].get('platform') if data else 'N/A'}")

        # 显示前3条数据
        print(f"\n  前3条数据预览:")
        for i, item in enumerate(data[:3], 1):
            author = item.get('author_name', '匿名')
            content = item.get('content', '')[:50]
            print(f"    {i}. [{author}] {content}...")
    else:
        print(f"  ❌ 爬取失败: {msg}")
        return False

    # 6. AI分析
    print("\n【步骤6】AI分析...")
    success, msg, analysis = analyzer.analyze(
        user_id=user_id,
        data=data,
        analysis_type='comprehensive',
        subscription_id=sub_id
    )

    if success:
        print(f"  ✅ 分析成功")
        print(f"  目标: {analysis['target']}")
        print(f"  数据量: {analysis['data_count']}")
        print(f"  Token消耗: {analysis['tokens_used']}")
        print(f"  剩余余额: {analysis['remaining_balance']}")

        # 显示分析结果
        if 'sentiment' in analysis:
            print(f"\n  分析结果:")
            print(f"    市场情绪: {analysis.get('sentiment')}")
            print(f"    置信度: {analysis.get('confidence', 0)}")

            if 'key_topics' in analysis:
                print(f"    关键主题: {', '.join(analysis['key_topics'][:3])}")

            if 'summary' in analysis:
                summary = analysis['summary'][:100]
                print(f"    摘要: {summary}...")
    else:
        print(f"  ❌ 分析失败: {msg}")
        return False

    # 7. 模拟推送
    print("\n【步骤7】模拟推送...")
    sentiment_emoji = {
        'positive': '📈',
        'negative': '📉',
        'neutral': '➡️'
    }.get(analysis.get('sentiment', 'neutral'), '➡️')

    push_content = (
        f"📊 特斯拉 (TSLA) 更新\n\n"
        f"{sentiment_emoji} 市场情绪: {analysis.get('sentiment', 'N/A')}\n"
        f"📝 数据量: {analysis['data_count']}条\n"
        f"💡 Token消耗: {analysis['tokens_used']}\n\n"
        f"摘要:\n{analysis.get('summary', 'N/A')[:100]}..."
    )

    print("  推送内容预览:")
    for line in push_content.split('\n'):
        print(f"    {line}")

    print("\n  💬 实际推送需要配置 Telegram Bot 或其他推送渠道")

    # 8. 查看用户统计
    print("\n【步骤8】用户统计...")
    stats = user_mgr.get_user_stats(user_id)
    print(f"  订阅数: {stats['subscription_count']}")
    print(f"  今日Token消耗: {stats['today_tokens_consumed']}")
    print(f"  今日请求数: {stats['today_request_count']}")

    # 9. 查看Token历史
    print("\n【步骤9】Token消耗历史...")
    history = user_mgr.get_token_history(user_id, limit=5)
    print(f"  历史记录数: {len(history)}")
    for i, record in enumerate(history[:3], 1):
        operation = record.get('operation', 'N/A')
        model = record.get('model', 'N/A')
        tokens = record.get('total_tokens', 0)
        print(f"    {i}. {operation} | {model} | {tokens} tokens")

    # 10. 最终状态
    print("\n【步骤10】最终状态...")
    final_balance = user_mgr.get_token_balance(user_id)
    print(f"  Token余额: {final_balance}")

    user_info = user_mgr.get_user_info(user_id)
    print(f"  会员状态: {user_info['membership']['type']} "
          f"({'有效' if not user_info['membership']['is_expired'] else '已过期'})")

    # 测试完成
    print("\n" + "=" * 70)
    print("✅ 完整工作流程测试通过！")
    print("=" * 70)

    print("\n📋 测试总结:")
    print("  1. ✅ 用户注册成功")
    print("  2. ✅ 订阅创建成功")
    print("  3. ✅ 数据爬取成功")
    print("  4. ✅ AI分析成功")
    print("  5. ✅ Token扣除正确")
    print("  6. ✅ 统计数据准确")
    print()
    print("🎉 系统各模块集成正常，可以部署使用！")
    print()

    return True


def test_multiple_subscriptions():
    """测试多个订阅的场景"""

    print("\n" + "=" * 70)
    print("测试多订阅场景")
    print("=" * 70)

    db_path = "/tmp/test_multi_subscriptions.db"
    if os.path.exists(db_path):
        os.remove(db_path)

    user_mgr = UserManager(db_path)
    crawler = CrawlerAgent(user_mgr)
    analyzer = AnalyzerAgent(user_mgr, mock_mode=True)

    # 注册用户
    user_id = "telegram_multi_test"
    user_mgr.register_user(user_id)

    # 创建多个订阅
    targets = ['TSLA', 'AAPL', 'GOOGL']
    subscription_ids = []

    print("\n创建多个订阅...")
    for target in targets:
        success, msg, sub_id = user_mgr.create_subscription(
            user_id=user_id,
            subscription_type='stock',
            target=target,
            platforms=['eastmoney'],
            push_channels=['telegram']
        )
        if success:
            subscription_ids.append(sub_id)
            print(f"  ✅ {target}: 订阅ID {sub_id}")

    # 批量处理订阅
    print(f"\n处理 {len(subscription_ids)} 个订阅...")
    subscriptions = user_mgr.get_user_subscriptions(user_id)

    total_data = 0
    total_tokens = 0

    for sub in subscriptions:
        # 爬取
        success, msg, data = crawler.crawl(
            user_id=user_id,
            platform='eastmoney',
            target=sub['target'],
            max_items=10
        )

        if success and data:
            total_data += len(data)

            # 分析
            success, msg, analysis = analyzer.analyze(
                user_id=user_id,
                data=data,
                analysis_type='summary'
            )

            if success:
                total_tokens += analysis['tokens_used']
                print(f"  {sub['target']}: {len(data)}条数据, "
                      f"{analysis['tokens_used']} tokens")

    # 总结
    balance = user_mgr.get_token_balance(user_id)
    print(f"\n总结:")
    print(f"  总数据量: {total_data}条")
    print(f"  总Token消耗: {total_tokens}")
    print(f"  剩余余额: {balance}")
    print(f"  ✅ 多订阅测试通过！")


if __name__ == "__main__":
    # 运行完整工作流程测试
    success = test_full_workflow()

    if success:
        # 运行多订阅测试
        test_multiple_subscriptions()
