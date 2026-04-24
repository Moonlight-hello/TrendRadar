# -*- coding: utf-8 -*-
"""
AnalyzerAgent 测试脚本
"""

import os
import sys
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent))

from core.analyzer_agent import AnalyzerAgent
from core.user_manager import UserManager

# 测试数据（模拟从CrawlerAgent获取的标准化数据）
MOCK_DATA = [
    {
        'platform': 'eastmoney',
        'data_type': 'post',
        'target': 'TSLA',
        'content_id': '1',
        'author_id': 'user1',
        'author_name': '投资者A',
        'content': '特斯拉今天表现不错，交付量超预期，看好后市',
        'publish_time': '2026-04-23T10:00:00',
        'metrics': {'likes': 120, 'comments': 15}
    },
    {
        'platform': 'eastmoney',
        'data_type': 'post',
        'target': 'TSLA',
        'content_id': '2',
        'author_id': 'user2',
        'author_name': '分析师B',
        'content': '特斯拉Q1财报即将发布，市场预期较高，但需要关注毛利率变化',
        'publish_time': '2026-04-23T09:30:00',
        'metrics': {'likes': 85, 'comments': 8}
    },
    {
        'platform': 'eastmoney',
        'data_type': 'comment',
        'target': 'TSLA',
        'content_id': '3',
        'author_id': 'user3',
        'author_name': '散户C',
        'content': '我觉得估值有点高了，短期可能会回调',
        'publish_time': '2026-04-23T09:15:00',
        'metrics': {'likes': 45, 'comments': 3}
    },
    {
        'platform': 'eastmoney',
        'data_type': 'post',
        'target': 'TSLA',
        'content_id': '4',
        'author_id': 'user4',
        'author_name': '技术派D',
        'content': 'MACD金叉，BOLL突破上轨，技术面看多',
        'publish_time': '2026-04-23T08:45:00',
        'metrics': {'likes': 200, 'comments': 25}
    },
    {
        'platform': 'eastmoney',
        'data_type': 'post',
        'target': 'TSLA',
        'content_id': '5',
        'author_id': 'user5',
        'author_name': '长线投资者E',
        'content': '特斯拉的自动驾驶技术领先，长期看好，短期波动不影响持仓',
        'publish_time': '2026-04-23T08:30:00',
        'metrics': {'likes': 150, 'comments': 18}
    }
]


def test_analyzer():
    """测试AnalyzerAgent"""

    print("=" * 60)
    print("AnalyzerAgent 测试")
    print("=" * 60)

    # 1. 初始化
    db_path = "/tmp/test_analyzer_agent.db"
    if os.path.exists(db_path):
        os.remove(db_path)

    user_mgr = UserManager(db_path)
    analyzer = AnalyzerAgent(user_mgr, mock_mode=True)  # 使用Mock模式进行测试

    # 2. 注册测试用户
    user_id = "telegram_test_analyzer"
    result = user_mgr.register_user(user_id, channel='telegram')
    print(f"\n1. 用户注册: {result['user_id']} (余额: {result['token_balance']})")

    # 3. 测试综合分析
    print("\n2. 测试综合分析...")
    success, msg, analysis = analyzer.analyze(
        user_id=user_id,
        data=MOCK_DATA,
        analysis_type='comprehensive'
    )

    print(f"   结果: {success}")
    print(f"   消息: {msg}")

    if success and analysis:
        print(f"   目标: {analysis['target']}")
        print(f"   数据量: {analysis['data_count']}")
        print(f"   Token消耗: {analysis['tokens_used']}")
        print(f"   剩余余额: {analysis['remaining_balance']}")
        print(f"\n   分析内容:")

        # 如果有结构化字段，打印它们
        if 'sentiment' in analysis:
            print(f"   - 市场情绪: {analysis.get('sentiment')}")
        if 'key_topics' in analysis:
            print(f"   - 关键主题: {analysis.get('key_topics')}")
        if 'summary' in analysis:
            print(f"   - 摘要: {analysis.get('summary')}")

        # 打印完整内容（限制长度）
        content = analysis.get('content', '')
        print(f"\n   完整分析（前500字）:")
        print(f"   {content[:500]}")
        if len(content) > 500:
            print("   ...")

    # 4. 测试情绪分析
    print("\n3. 测试情绪分析...")
    success, msg, sentiment = analyzer.analyze(
        user_id=user_id,
        data=MOCK_DATA,
        analysis_type='sentiment'
    )

    print(f"   结果: {success}")
    print(f"   消息: {msg}")

    if success and sentiment:
        print(f"   Token消耗: {sentiment['tokens_used']}")
        print(f"   剩余余额: {sentiment['remaining_balance']}")
        print(f"   情绪分析结果: {sentiment.get('content', '')[:300]}")

    # 5. 测试摘要生成
    print("\n4. 测试摘要生成...")
    success, msg, summary = analyzer.analyze(
        user_id=user_id,
        data=MOCK_DATA,
        analysis_type='summary'
    )

    print(f"   结果: {success}")
    print(f"   消息: {msg}")

    if success and summary:
        print(f"   Token消耗: {summary['tokens_used']}")
        print(f"   剩余余额: {summary['remaining_balance']}")
        print(f"   摘要: {summary.get('content', '')}")

    # 6. 检查Token余额
    balance = user_mgr.get_token_balance(user_id)
    print(f"\n5. 最终Token余额: {balance}")

    # 7. 查看Token消耗历史
    history = user_mgr.get_token_history(user_id, limit=10)
    print(f"\n6. Token消耗历史 (共{len(history)}条):")
    for i, record in enumerate(history[:5], 1):
        print(f"   {i}. {record.get('operation', 'N/A')} | "
              f"{record.get('model', 'N/A')} | "
              f"消耗: {record.get('total_tokens', 0)} | "
              f"时间: {record.get('created_at', 'N/A')}")

    # 8. 测试上下文维护
    print("\n7. 测试上下文维护...")

    # 第一次对话
    success, msg, result1 = analyzer.analyze(
        user_id=user_id,
        data=MOCK_DATA[:2],
        analysis_type='summary',
        maintain_context=True
    )

    if success:
        print(f"   第一轮分析完成，Token消耗: {result1['tokens_used']}")

        # 检查上下文
        context = analyzer.get_context(user_id)
        print(f"   上下文消息数: {len(context)}")

    # 9. 测试余额不足
    print("\n8. 测试余额不足情况...")

    # 消耗掉剩余余额
    remaining = user_mgr.get_token_balance(user_id)
    if remaining > 0:
        user_mgr.deduct_token(
            user_id=user_id,
            amount=remaining,
            operation="test",
            model="test"
        )

    success, msg, result = analyzer.analyze(
        user_id=user_id,
        data=MOCK_DATA,
        analysis_type='summary'
    )

    print(f"   结果: {success}")
    print(f"   消息: {msg}")
    assert not success, "应该因为余额不足而失败"

    # 10. 清理上下文
    print("\n9. 清理上下文...")
    analyzer.clear_context(user_id)
    context = analyzer.get_context(user_id)
    print(f"   清理后上下文消息数: {len(context)}")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    test_analyzer()
