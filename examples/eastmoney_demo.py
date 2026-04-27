#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
东方财富股吧爬虫示例
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from trendradar.crawler.eastmoney import crawl_eastmoney_stock, crawl_eastmoney_stocks


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


async def example_single_stock():
    """示例1: 爬取单个股票"""
    print("\n=== 示例1: 爬取单个股票 ===\n")

    result = await crawl_eastmoney_stock(
        stock_code="600519",      # 贵州茅台
        max_pages=1,              # 爬取1页
        enable_comments=True,     # 启用评论
        max_comments_per_post=50  # 每个帖子最多50条评论
    )

    print(f"\n✅ 爬取完成!")
    print(f"📊 帖子数: {result['posts_count']}")
    print(f"💬 评论数: {result['comments_count']}")

    # 显示前5条帖子
    print(f"\n📝 帖子示例:")
    for i, post in enumerate(result['posts'][:5], 1):
        print(f"{i}. {post['title']}")
        print(f"   作者: {post['author_name']} | 评论数: {post['comment_count']} | 发布时间: {post['publish_time']}")

    # 显示前5条评论
    if result['comments']:
        print(f"\n💬 评论示例:")
        for i, comment in enumerate(result['comments'][:5], 1):
            print(f"{i}. {comment['author_name']}: {comment['content'][:50]}...")
            print(f"   时间: {comment['create_time']} | 点赞: {comment['like_count']}")

    return result


async def example_multiple_stocks():
    """示例2: 批量爬取多个股票"""
    print("\n=== 示例2: 批量爬取多个股票 ===\n")

    # 定义要爬取的股票列表
    stock_codes = [
        "600519",  # 贵州茅台
        "000858",  # 五粮液
        "000001",  # 平安银行
    ]

    result = await crawl_eastmoney_stocks(
        stock_codes=stock_codes,
        max_pages=1,
        enable_comments=True,
        max_comments_per_post=30
    )

    print(f"\n✅ 爬取完成!")
    print(f"📈 股票数: {result['total_stocks']}")
    print(f"📊 总帖子: {result['total_posts']}")
    print(f"💬 总评论: {result['total_comments']}")

    # 显示每个股票的统计
    print(f"\n📊 各股票统计:")
    for stock_code, data in result['results'].items():
        if 'error' in data:
            print(f"❌ {stock_code}: 爬取失败 - {data['error']}")
        else:
            print(f"✅ {stock_code}: {data['posts_count']} 条帖子, {data['comments_count']} 条评论")

    return result


async def example_save_to_json():
    """示例3: 保存数据到JSON文件"""
    print("\n=== 示例3: 保存数据到JSON ===\n")

    result = await crawl_eastmoney_stock(
        stock_code="600519",
        max_pages=1,
        enable_comments=True,
        max_comments_per_post=20
    )

    # 保存到JSON文件
    output_file = "eastmoney_600519.json"

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"✅ 数据已保存到: {output_file}")
    print(f"📊 帖子数: {result['posts_count']}")
    print(f"💬 评论数: {result['comments_count']}")

    return result


async def example_custom_processing():
    """示例4: 自定义数据处理"""
    print("\n=== 示例4: 自定义数据处理 ===\n")

    result = await crawl_eastmoney_stock(
        stock_code="600519",
        max_pages=1,
        enable_comments=True,
        max_comments_per_post=100
    )

    # 分析数据
    posts = result['posts']
    comments = result['comments']

    # 1. 找出评论最多的帖子
    if posts:
        top_post = max(posts, key=lambda x: x['comment_count'])
        print(f"🔥 评论最多的帖子:")
        print(f"   标题: {top_post['title']}")
        print(f"   评论数: {top_post['comment_count']}")
        print(f"   作者: {top_post['author_name']}")

    # 2. 统计活跃用户
    if comments:
        from collections import Counter
        authors = [c['author_name'] for c in comments]
        top_authors = Counter(authors).most_common(5)

        print(f"\n👥 最活跃的评论用户:")
        for author, count in top_authors:
            print(f"   {author}: {count} 条评论")

    # 3. 统计评论时间分布
    if comments:
        hours = [c['create_time'].split()[1].split(':')[0] for c in comments if c['create_time']]
        hour_dist = Counter(hours)

        print(f"\n⏰ 评论时间分布:")
        for hour in sorted(hour_dist.keys()):
            print(f"   {hour}:00 - {hour_dist[hour]} 条评论")

    return result


async def main():
    """主函数"""
    print("=" * 60)
    print("东方财富股吧爬虫示例")
    print("=" * 60)

    try:
        # 运行示例
        # await example_single_stock()
        # await example_multiple_stocks()
        # await example_save_to_json()
        await example_custom_processing()

    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
