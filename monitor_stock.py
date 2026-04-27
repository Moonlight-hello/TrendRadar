#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票监控脚本 - 监控东方财富股吧
用于实时监控指定股票的帖子和评论
"""

import asyncio
import json
import logging
import sqlite3
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from trendradar.crawler.eastmoney import crawl_eastmoney_stock


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class StockMonitor:
    """股票监控器"""

    def __init__(self, stock_code: str, output_dir: str = "output/stocks",
                 db_path: str = "eastmoney_stocks.db", save_json: bool = True):
        """
        初始化监控器

        Args:
            stock_code: 股票代码
            output_dir: 输出目录
            db_path: 数据库路径
            save_json: 是否同时保存JSON文件
        """
        self.stock_code = stock_code
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path
        self.save_json = save_json
        self._init_db()

    def _init_db(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 创建帖子表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id TEXT UNIQUE,
                stock_code TEXT,
                title TEXT,
                content TEXT,
                publish_time TIMESTAMP,
                user_id TEXT,
                user_nickname TEXT,
                click_count INTEGER DEFAULT 0,
                comment_count INTEGER DEFAULT 0,
                like_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 创建评论表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                comment_id TEXT UNIQUE,
                post_id TEXT,
                content TEXT,
                publish_time TIMESTAMP,
                user_id TEXT,
                user_nickname TEXT,
                like_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_posts_stock_code ON posts(stock_code)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_posts_publish_time ON posts(publish_time)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_comments_post_id ON comments(post_id)")

        conn.commit()
        conn.close()

    def save_to_db(self, data: Dict) -> Dict:
        """
        保存数据到数据库

        Args:
            data: 爬取的数据

        Returns:
            保存结果统计
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        stock_code = data['stock_code']
        posts = data['posts']
        comments = data['comments']

        posts_imported = 0
        posts_skipped = 0
        comments_imported = 0
        comments_skipped = 0

        # 导入帖子
        for post in posts:
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO posts
                    (post_id, stock_code, title, content, publish_time, user_id, user_nickname,
                     click_count, comment_count, like_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    post.get('post_id'),
                    stock_code,
                    post.get('title'),
                    post.get('content', ''),
                    post.get('publish_time'),
                    post.get('author_id'),
                    post.get('author_name'),
                    post.get('read_count', 0),
                    post.get('comment_count', 0),
                    post.get('like_count', 0)
                ))

                if cursor.rowcount > 0:
                    posts_imported += 1
                else:
                    posts_skipped += 1

            except Exception as e:
                logger.error(f"导入帖子失败: {post.get('post_id')} - {e}")

        # 导入评论
        for comment in comments:
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO comments
                    (comment_id, post_id, content, publish_time, user_id, user_nickname, like_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    comment.get('comment_id'),
                    comment.get('post_id'),
                    comment.get('content'),
                    comment.get('create_time'),
                    comment.get('author_id'),
                    comment.get('author_name'),
                    comment.get('like_count', 0)
                ))

                if cursor.rowcount > 0:
                    comments_imported += 1
                else:
                    comments_skipped += 1

            except Exception as e:
                logger.error(f"导入评论失败: {comment.get('comment_id')} - {e}")

        conn.commit()
        conn.close()

        result = {
            "posts_imported": posts_imported,
            "posts_skipped": posts_skipped,
            "comments_imported": comments_imported,
            "comments_skipped": comments_skipped
        }

        logger.info(f"💾 数据已保存到数据库: {self.db_path}")
        logger.info(f"   - 帖子: {posts_imported}条新增, {posts_skipped}条已存在")
        logger.info(f"   - 评论: {comments_imported}条新增, {comments_skipped}条已存在")

        return result

    async def crawl_data(self, max_pages: int = 5, enable_comments: bool = True,
                        max_comments_per_post: int = 100) -> Dict:
        """
        爬取股票数据

        Args:
            max_pages: 最大爬取页数
            enable_comments: 是否启用评论
            max_comments_per_post: 每个帖子最多评论数

        Returns:
            爬取结果
        """
        logger.info(f"开始爬取股票 {self.stock_code} 的数据...")

        result = await crawl_eastmoney_stock(
            stock_code=self.stock_code,
            max_pages=max_pages,
            enable_comments=enable_comments,
            max_comments_per_post=max_comments_per_post
        )

        logger.info(f"✅ 爬取完成！帖子数: {result['posts_count']}, 评论数: {result['comments_count']}")
        return result

    def save_data(self, data: Dict, timestamp: str = None):
        """
        保存数据（到数据库和可选的JSON文件）

        Args:
            data: 爬取的数据
            timestamp: 时间戳
        """
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 保存到数据库（主要存储）
        self.save_to_db(data)

        # 可选：同时保存JSON文件（用于备份或其他用途）
        if self.save_json:
            # 保存完整数据
            output_file = self.output_dir / f"{self.stock_code}_{timestamp}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info(f"📁 JSON备份已保存到: {output_file}")

            # 保存简化的分析数据
            analysis_file = self.output_dir / f"{self.stock_code}_{timestamp}_analysis.json"
            analysis_data = {
                "stock_code": data['stock_code'],
                "timestamp": timestamp,
                "posts_count": data['posts_count'],
                "comments_count": data['comments_count'],
                "top_posts": [
                    {
                        "title": post['title'],
                        "author": post['author_name'],
                        "comment_count": post['comment_count'],
                        "read_count": post['read_count'],
                        "publish_time": post['publish_time']
                    }
                    for post in sorted(data['posts'], key=lambda x: x['comment_count'], reverse=True)[:10]
                ]
            }

            with open(analysis_file, 'w', encoding='utf-8') as f:
                json.dump(analysis_data, f, ensure_ascii=False, indent=2)

            logger.info(f"📊 分析数据已保存到: {analysis_file}")

    def print_summary(self, data: Dict):
        """
        打印数据摘要

        Args:
            data: 爬取的数据
        """
        print("\n" + "=" * 80)
        print(f"📊 股票监控报告 - {self.stock_code}")
        print("=" * 80)

        print(f"\n📈 基本统计:")
        print(f"   - 股票代码: {data['stock_code']}")
        print(f"   - 帖子数量: {data['posts_count']}")
        print(f"   - 评论数量: {data['comments_count']}")

        # 显示最热门的帖子
        if data['posts']:
            print(f"\n🔥 最热门的帖子 (按评论数排序):")
            sorted_posts = sorted(data['posts'], key=lambda x: x['comment_count'], reverse=True)
            for i, post in enumerate(sorted_posts[:5], 1):
                print(f"   {i}. {post['title'][:60]}")
                print(f"      作者: {post['author_name']} | 评论: {post['comment_count']} | 阅读: {post['read_count']} | 时间: {post['publish_time']}")

        # 显示最新的评论
        if data['comments']:
            print(f"\n💬 最新评论 (前10条):")
            for i, comment in enumerate(data['comments'][:10], 1):
                content = comment['content'][:50] + "..." if len(comment['content']) > 50 else comment['content']
                print(f"   {i}. {comment['author_name']}: {content}")
                print(f"      时间: {comment['create_time']} | 点赞: {comment['like_count']}")

        # 统计作者活跃度
        if data['comments']:
            from collections import Counter
            authors = [c['author_name'] for c in data['comments']]
            top_authors = Counter(authors).most_common(10)

            print(f"\n👥 最活跃的评论用户 (Top 10):")
            for rank, (author, count) in enumerate(top_authors, 1):
                print(f"   {rank}. {author}: {count} 条评论")

        print("\n" + "=" * 80)


async def monitor_single_stock(stock_code: str, max_pages: int = 5,
                              enable_comments: bool = True,
                              max_comments_per_post: int = 100):
    """
    监控单个股票

    Args:
        stock_code: 股票代码
        max_pages: 最大爬取页数
        enable_comments: 是否启用评论
        max_comments_per_post: 每个帖子最多评论数
    """
    monitor = StockMonitor(stock_code)

    # 爬取数据
    data = await monitor.crawl_data(
        max_pages=max_pages,
        enable_comments=enable_comments,
        max_comments_per_post=max_comments_per_post
    )

    # 保存数据
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    monitor.save_data(data, timestamp)

    # 打印摘要
    monitor.print_summary(data)

    return data


async def monitor_multiple_stocks(stock_codes: List[str], max_pages: int = 3,
                                  enable_comments: bool = True,
                                  max_comments_per_post: int = 50):
    """
    监控多个股票

    Args:
        stock_codes: 股票代码列表
        max_pages: 最大爬取页数
        enable_comments: 是否启用评论
        max_comments_per_post: 每个帖子最多评论数
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    results = {}
    for stock_code in stock_codes:
        try:
            logger.info(f"\n处理股票: {stock_code}")
            monitor = StockMonitor(stock_code)
            data = await monitor.crawl_data(
                max_pages=max_pages,
                enable_comments=enable_comments,
                max_comments_per_post=max_comments_per_post
            )
            monitor.save_data(data, timestamp)
            results[stock_code] = data

            # 延迟，避免请求过快
            await asyncio.sleep(2)

        except Exception as e:
            logger.error(f"❌ 处理股票 {stock_code} 时出错: {e}")
            results[stock_code] = {"error": str(e)}

    # 打印总体统计
    print("\n" + "=" * 80)
    print("📊 批量监控总结")
    print("=" * 80)

    total_posts = 0
    total_comments = 0

    for stock_code, data in results.items():
        if "error" in data:
            print(f"❌ {stock_code}: 失败 - {data['error']}")
        else:
            posts = data['posts_count']
            comments = data['comments_count']
            total_posts += posts
            total_comments += comments
            print(f"✅ {stock_code}: {posts} 条帖子, {comments} 条评论")

    print(f"\n📈 合计: {len(results)} 只股票, {total_posts} 条帖子, {total_comments} 条评论")
    print("=" * 80)

    return results


async def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="东方财富股吧监控工具")
    parser.add_argument("--stock", "-s", type=str, help="股票代码（单个）")
    parser.add_argument("--stocks", "-m", type=str, help="股票代码列表（逗号分隔）")
    parser.add_argument("--pages", "-p", type=int, default=5, help="爬取页数（默认5）")
    parser.add_argument("--comments", "-c", type=int, default=100, help="每个帖子最大评论数（默认100）")
    parser.add_argument("--no-comments", action="store_true", help="不爬取评论")

    args = parser.parse_args()

    # 如果没有参数，使用默认值（监控 000973）
    if not args.stock and not args.stocks:
        print("⚠️  未指定股票代码，使用默认值: 000973")
        args.stock = "000973"

    enable_comments = not args.no_comments

    try:
        if args.stocks:
            # 监控多个股票
            stock_codes = [s.strip() for s in args.stocks.split(",")]
            await monitor_multiple_stocks(
                stock_codes=stock_codes,
                max_pages=args.pages,
                enable_comments=enable_comments,
                max_comments_per_post=args.comments
            )
        else:
            # 监控单个股票
            await monitor_single_stock(
                stock_code=args.stock,
                max_pages=args.pages,
                enable_comments=enable_comments,
                max_comments_per_post=args.comments
            )

        print("\n✅ 监控完成！")

    except Exception as e:
        logger.error(f"❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
