#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将JSON数据导入到SQLite数据库
"""

import json
import sqlite3
import sys
from pathlib import Path
from datetime import datetime


class StockDataImporter:
    """股票数据导入器"""

    def __init__(self, db_path: str = "eastmoney_stocks.db"):
        """
        初始化导入器

        Args:
            db_path: 数据库路径
        """
        self.db_path = db_path
        self.conn = None
        self.cursor = None

    def connect(self):
        """连接数据库"""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        print(f"✅ 已连接到数据库: {self.db_path}")

    def create_tables(self):
        """创建表结构"""
        # 帖子表
        self.cursor.execute("""
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

        # 评论表
        self.cursor.execute("""
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
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_posts_stock_code ON posts(stock_code)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_posts_publish_time ON posts(publish_time)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_comments_post_id ON comments(post_id)")

        self.conn.commit()
        print("✅ 表结构已创建/验证")

    def import_json_data(self, json_file: str):
        """
        导入JSON数据

        Args:
            json_file: JSON文件路径
        """
        print(f"\n开始导入数据: {json_file}")

        # 读取JSON
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        stock_code = data['stock_code']
        posts = data['posts']
        comments = data['comments']

        print(f"📊 数据概况: 股票{stock_code}, {len(posts)}条帖子, {len(comments)}条评论")

        # 导入帖子
        posts_imported = 0
        posts_skipped = 0

        for post in posts:
            try:
                self.cursor.execute("""
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

                if self.cursor.rowcount > 0:
                    posts_imported += 1
                else:
                    posts_skipped += 1

            except Exception as e:
                print(f"❌ 导入帖子失败: {post.get('post_id')} - {e}")

        # 导入评论
        comments_imported = 0
        comments_skipped = 0

        for comment in comments:
            try:
                self.cursor.execute("""
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

                if self.cursor.rowcount > 0:
                    comments_imported += 1
                else:
                    comments_skipped += 1

            except Exception as e:
                print(f"❌ 导入评论失败: {comment.get('comment_id')} - {e}")

        self.conn.commit()

        print(f"\n✅ 导入完成!")
        print(f"   - 帖子: {posts_imported}条新增, {posts_skipped}条已存在")
        print(f"   - 评论: {comments_imported}条新增, {comments_skipped}条已存在")

        return {
            "posts_imported": posts_imported,
            "posts_skipped": posts_skipped,
            "comments_imported": comments_imported,
            "comments_skipped": comments_skipped
        }

    def get_stats(self):
        """获取数据库统计信息"""
        # 股票统计
        self.cursor.execute("""
            SELECT stock_code, COUNT(*) as post_count
            FROM posts
            GROUP BY stock_code
        """)
        stock_stats = self.cursor.fetchall()

        # 总计
        self.cursor.execute("SELECT COUNT(*) FROM posts")
        total_posts = self.cursor.fetchone()[0]

        self.cursor.execute("SELECT COUNT(*) FROM comments")
        total_comments = self.cursor.fetchone()[0]

        print(f"\n📊 数据库统计:")
        print(f"   - 总帖子数: {total_posts}")
        print(f"   - 总评论数: {total_comments}")
        print(f"   - 股票数量: {len(stock_stats)}")

        if stock_stats:
            print(f"\n   各股票统计:")
            for stock_code, count in stock_stats:
                self.cursor.execute(
                    "SELECT COUNT(*) FROM comments WHERE post_id IN (SELECT post_id FROM posts WHERE stock_code=?)",
                    (stock_code,)
                )
                comment_count = self.cursor.fetchone()[0]
                print(f"   - {stock_code}: {count}条帖子, {comment_count}条评论")

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            print(f"\n✅ 数据库连接已关闭")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="将JSON数据导入到SQLite数据库")
    parser.add_argument("--file", "-f", type=str, help="JSON文件路径")
    parser.add_argument("--dir", "-d", type=str, help="JSON文件目录（导入目录下所有JSON）")
    parser.add_argument("--db", type=str, default="eastmoney_stocks.db", help="数据库路径（默认: eastmoney_stocks.db）")
    parser.add_argument("--stats", action="store_true", help="只显示统计信息")

    args = parser.parse_args()

    # 创建导入器
    importer = StockDataImporter(args.db)

    try:
        importer.connect()
        importer.create_tables()

        # 只显示统计
        if args.stats:
            importer.get_stats()
            return

        # 导入单个文件
        if args.file:
            importer.import_json_data(args.file)
            importer.get_stats()

        # 导入目录
        elif args.dir:
            json_files = list(Path(args.dir).glob("*.json"))
            # 排除分析文件
            json_files = [f for f in json_files if 'analysis' not in f.name and 'sentiment' not in f.name]

            print(f"📁 找到 {len(json_files)} 个JSON文件")

            for json_file in json_files:
                try:
                    importer.import_json_data(str(json_file))
                except Exception as e:
                    print(f"❌ 处理文件失败: {json_file} - {e}")

            importer.get_stats()

        else:
            print("❌ 请指定 --file 或 --dir 参数")
            parser.print_help()

    except Exception as e:
        print(f"❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()

    finally:
        importer.close()


if __name__ == "__main__":
    main()
