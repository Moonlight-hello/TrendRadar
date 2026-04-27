#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查询股票数据库
"""

import sqlite3
import sys
from datetime import datetime, timedelta


class StockDBQuery:
    """股票数据库查询器"""

    def __init__(self, db_path: str = "eastmoney_stocks.db"):
        """初始化查询器"""
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row  # 使结果可以像字典一样访问

    def get_stats(self):
        """获取统计信息"""
        cursor = self.conn.cursor()

        # 总体统计
        cursor.execute("SELECT COUNT(*) FROM posts")
        total_posts = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM comments")
        total_comments = cursor.fetchone()[0]

        # 按股票统计
        cursor.execute("""
            SELECT stock_code, COUNT(*) as post_count
            FROM posts
            GROUP BY stock_code
        """)
        stocks = cursor.fetchall()

        print("\n" + "="*80)
        print("📊 数据库统计")
        print("="*80)
        print(f"数据库: {self.db_path}")
        print(f"总帖子数: {total_posts}")
        print(f"总评论数: {total_comments}")
        print(f"股票数量: {len(stocks)}")

        if stocks:
            print(f"\n各股票数据:")
            for row in stocks:
                stock_code = row['stock_code']
                post_count = row['post_count']

                cursor.execute("""
                    SELECT COUNT(*) FROM comments
                    WHERE post_id IN (SELECT post_id FROM posts WHERE stock_code=?)
                """, (stock_code,))
                comment_count = cursor.fetchone()[0]

                cursor.execute("""
                    SELECT MIN(publish_time), MAX(publish_time)
                    FROM posts WHERE stock_code=?
                """, (stock_code,))
                time_range = cursor.fetchone()

                print(f"  {stock_code}: {post_count}帖 + {comment_count}评 | 时间: {time_range[0]} ~ {time_range[1]}")

    def get_stock_detail(self, stock_code: str, days: int = 7):
        """
        获取股票详细信息

        Args:
            stock_code: 股票代码
            days: 查询最近N天的数据
        """
        cursor = self.conn.cursor()

        # 计算时间范围
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        print("\n" + "="*80)
        print(f"📈 股票 {stock_code} 详细信息 (最近{days}天)")
        print("="*80)

        # 基本统计
        cursor.execute("""
            SELECT COUNT(*) FROM posts
            WHERE stock_code=? AND publish_time >= ?
        """, (stock_code, start_date.strftime("%Y-%m-%d")))
        recent_posts = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*) FROM comments
            WHERE post_id IN (SELECT post_id FROM posts WHERE stock_code=?)
            AND publish_time >= ?
        """, (stock_code, start_date.strftime("%Y-%m-%d")))
        recent_comments = cursor.fetchone()[0]

        print(f"\n最近{days}天统计:")
        print(f"  新帖子: {recent_posts}条")
        print(f"  新评论: {recent_comments}条")

        # 最热帖子
        cursor.execute("""
            SELECT title, user_nickname, comment_count, click_count, publish_time
            FROM posts
            WHERE stock_code=?
            ORDER BY comment_count DESC
            LIMIT 10
        """, (stock_code,))

        print(f"\n🔥 最热帖子 (Top 10):")
        for i, row in enumerate(cursor.fetchall(), 1):
            print(f"  {i}. {row['title'][:60]}")
            print(f"     作者:{row['user_nickname']} | 评论:{row['comment_count']} | 阅读:{row['click_count']} | {row['publish_time']}")

        # 最新帖子
        cursor.execute("""
            SELECT title, user_nickname, comment_count, publish_time
            FROM posts
            WHERE stock_code=?
            ORDER BY publish_time DESC
            LIMIT 10
        """, (stock_code,))

        print(f"\n🆕 最新帖子 (Top 10):")
        for i, row in enumerate(cursor.fetchall(), 1):
            print(f"  {i}. {row['title'][:60]}")
            print(f"     作者:{row['user_nickname']} | 评论:{row['comment_count']} | {row['publish_time']}")

        # 最活跃用户
        cursor.execute("""
            SELECT user_nickname, COUNT(*) as post_count
            FROM posts
            WHERE stock_code=?
            GROUP BY user_nickname
            ORDER BY post_count DESC
            LIMIT 10
        """, (stock_code,))

        print(f"\n👥 最活跃发帖用户 (Top 10):")
        for i, row in enumerate(cursor.fetchall(), 1):
            print(f"  {i}. {row['user_nickname']}: {row['post_count']}条帖子")

    def search_posts(self, stock_code: str, keyword: str, limit: int = 20):
        """
        搜索帖子

        Args:
            stock_code: 股票代码
            keyword: 关键词
            limit: 返回数量
        """
        cursor = self.conn.cursor()

        print("\n" + "="*80)
        print(f"🔍 搜索结果: 股票={stock_code}, 关键词={keyword}")
        print("="*80)

        cursor.execute("""
            SELECT title, user_nickname, comment_count, publish_time
            FROM posts
            WHERE stock_code=? AND title LIKE ?
            ORDER BY publish_time DESC
            LIMIT ?
        """, (stock_code, f"%{keyword}%", limit))

        results = cursor.fetchall()

        if results:
            print(f"\n找到 {len(results)} 条结果:")
            for i, row in enumerate(results, 1):
                print(f"\n{i}. {row['title']}")
                print(f"   作者:{row['user_nickname']} | 评论:{row['comment_count']} | {row['publish_time']}")
        else:
            print("\n未找到匹配结果")

    def get_latest_comments(self, stock_code: str, limit: int = 20):
        """
        获取最新评论

        Args:
            stock_code: 股票代码
            limit: 返回数量
        """
        cursor = self.conn.cursor()

        print("\n" + "="*80)
        print(f"💬 股票 {stock_code} 最新评论")
        print("="*80)

        cursor.execute("""
            SELECT c.content, c.user_nickname, c.publish_time, c.like_count, p.title
            FROM comments c
            JOIN posts p ON c.post_id = p.post_id
            WHERE p.stock_code=?
            ORDER BY c.publish_time DESC
            LIMIT ?
        """, (stock_code, limit))

        for i, row in enumerate(cursor.fetchall(), 1):
            content = row['content'][:80] + "..." if len(row['content']) > 80 else row['content']
            print(f"\n{i}. {row['user_nickname']}: {content}")
            print(f"   帖子: {row['title'][:50]}")
            print(f"   时间: {row['publish_time']} | 点赞: {row['like_count']}")

    def close(self):
        """关闭连接"""
        if self.conn:
            self.conn.close()


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="查询股票数据库")
    parser.add_argument("--db", type=str, default="eastmoney_stocks.db", help="数据库路径")
    parser.add_argument("--stats", action="store_true", help="显示统计信息")
    parser.add_argument("--stock", "-s", type=str, help="股票代码")
    parser.add_argument("--days", "-d", type=int, default=7, help="查询最近N天（默认7）")
    parser.add_argument("--search", type=str, help="搜索关键词")
    parser.add_argument("--comments", "-c", action="store_true", help="显示最新评论")
    parser.add_argument("--limit", "-l", type=int, default=20, help="显示数量（默认20）")

    args = parser.parse_args()

    query = StockDBQuery(args.db)

    try:
        if args.stats:
            # 显示统计信息
            query.get_stats()

        elif args.stock:
            if args.search:
                # 搜索帖子
                query.search_posts(args.stock, args.search, args.limit)
            elif args.comments:
                # 显示最新评论
                query.get_latest_comments(args.stock, args.limit)
            else:
                # 显示股票详情
                query.get_stock_detail(args.stock, args.days)

        else:
            # 默认显示统计
            query.get_stats()

    finally:
        query.close()


if __name__ == "__main__":
    main()
