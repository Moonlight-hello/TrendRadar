#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试东方财富爬虫功能
"""

import asyncio
import logging
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from trendradar.crawler.eastmoney import crawl_eastmoney_stock


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


async def test_crawl():
    """测试爬取功能"""
    print("\n" + "="*60)
    print("测试东方财富爬虫")
    print("="*60 + "\n")

    # 爬取一个股票的少量数据进行测试
    result = await crawl_eastmoney_stock(
        stock_code="000973",      # 贵州茅台
        max_pages=1,              # 只爬1页
        enable_comments=True,     # 启用评论
        max_comments_per_post=10  # 每个帖子最多10条评论
    )

    print(f"\n✅ 测试完成!\n")
    print(f"📊 统计信息:")
    print(f"   - 股票代码: {result['stock_code']}")
    print(f"   - 帖子数量: {result['posts_count']}")
    print(f"   - 评论数量: {result['comments_count']}")

    if result['posts']:
        print(f"\n📝 帖子示例 (前3条):")
        for i, post in enumerate(result['posts'][:3], 1):
            print(f"   {i}. {post['title'][:50]}...")
            print(f"      作者: {post['author_name']} | 评论: {post['comment_count']} | 时间: {post['publish_time']}")

    if result['comments']:
        print(f"\n💬 评论示例 (前3条):")
        for i, comment in enumerate(result['comments'][:3], 1):
            content = comment['content'][:40] + "..." if len(comment['content']) > 40 else comment['content']
            print(f"   {i}. {comment['author_name']}: {content}")

    print(f"\n{'='*60}")
    print("✅ 所有测试通过!")
    print("="*60 + "\n")

    return result


if __name__ == "__main__":
    asyncio.run(test_crawl())
