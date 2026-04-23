"""
CommunitySpy Tool - TrendRadar Agent 工具适配器

将 EastMoneyCommentSpider 封装为符合 TrendRadar Agent 系统的工具
"""

from typing import Dict, Any, List, Optional
from pathlib import Path

from ...base import BaseTool
from .spider import EastMoneyCommentSpider


class CommunitySpyTool(BaseTool):
    """
    CommunitySpy 工具

    爬取东方财富股吧的帖子和评论数据
    """

    def __init__(self):
        """初始化工具"""
        super().__init__()
        self.name = "communityspy"
        self.description = "Crawl posts and comments from East Money stock forum"
        self.category = "data_source"

        self.parameters = {
            "stock_code": {
                "type": "string",
                "description": "Stock code (e.g., '301293')",
                "required": True
            },
            "max_pages": {
                "type": "integer",
                "description": "Maximum number of pages to crawl",
                "default": 10,
                "required": False
            },
            "max_posts": {
                "type": "integer",
                "description": "Maximum number of posts to crawl",
                "default": 100,
                "required": False
            },
            "include_comments": {
                "type": "boolean",
                "description": "Whether to crawl comments",
                "default": True,
                "required": False
            },
            "delay": {
                "type": "number",
                "description": "Delay between requests (seconds)",
                "default": 1.0,
                "required": False
            },
            "db_path": {
                "type": "string",
                "description": "Database file path (optional)",
                "required": False
            }
        }

    def execute(self,
                stock_code: str,
                max_pages: int = 10,
                max_posts: int = 100,
                include_comments: bool = True,
                delay: float = 1.0,
                db_path: Optional[str] = None,
                **kwargs) -> Dict[str, Any]:
        """
        执行爬取任务

        Args:
            stock_code: 股票代码
            max_pages: 最大页数
            max_posts: 最大帖子数
            include_comments: 是否爬取评论
            delay: 请求延迟
            db_path: 数据库路径
            **kwargs: 其他参数

        Returns:
            爬取结果，格式:
            {
                "success": True/False,
                "stock_code": "301293",
                "stats": {
                    "posts_count": 100,
                    "comments_count": 500,
                    "errors": []
                },
                "db_path": "eastmoney_301293.db"
            }
        """
        # 验证参数
        self.validate_params(stock_code=stock_code)

        try:
            # 创建爬虫实例
            with EastMoneyCommentSpider(stock_code, db_path) as spider:
                # 执行爬取
                stats = spider.crawl(
                    max_pages=max_pages,
                    max_posts=max_posts,
                    include_comments=include_comments,
                    delay=delay
                )

                return {
                    "success": True,
                    "stock_code": stock_code,
                    "stats": stats,
                    "db_path": spider.db_path,
                    "message": f"成功爬取 {stats['posts_count']} 条帖子、{stats['comments_count']} 条评论和 {stats.get('replies_count', 0)} 条回复"
                }

        except Exception as e:
            return {
                "success": False,
                "stock_code": stock_code,
                "error": str(e),
                "message": f"爬取失败: {str(e)}"
            }


class CommunitySpyQueryTool(BaseTool):
    """
    CommunitySpy 查询工具

    从数据库中查询已爬取的数据
    """

    def __init__(self):
        """初始化工具"""
        super().__init__()
        self.name = "communityspy_query"
        self.description = "Query crawled data from CommunitySpy database"
        self.category = "data_source"

        self.parameters = {
            "db_path": {
                "type": "string",
                "description": "Database file path",
                "required": True
            },
            "query_type": {
                "type": "string",
                "description": "Query type: posts, comments, replies, or stats",
                "default": "posts",
                "required": False
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of results",
                "default": 100,
                "required": False
            },
            "start_date": {
                "type": "string",
                "description": "Start date (YYYY-MM-DD)",
                "required": False
            },
            "end_date": {
                "type": "string",
                "description": "End date (YYYY-MM-DD)",
                "required": False
            }
        }

    def execute(self,
                db_path: str,
                query_type: str = "posts",
                limit: int = 100,
                start_date: Optional[str] = None,
                end_date: Optional[str] = None,
                **kwargs) -> Dict[str, Any]:
        """
        执行查询

        Args:
            db_path: 数据库路径
            query_type: 查询类型 (posts, comments, stats)
            limit: 结果数量限制
            start_date: 开始日期
            end_date: 结束日期
            **kwargs: 其他参数

        Returns:
            查询结果
        """
        import sqlite3

        # 验证参数
        self.validate_params(db_path=db_path)

        # 检查数据库是否存在
        db_file = Path(db_path)
        if not db_file.exists():
            return {
                "success": False,
                "error": f"Database not found: {db_path}"
            }

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # 根据查询类型执行不同的查询
            if query_type == "posts":
                sql = "SELECT * FROM posts"
                conditions = []
                params = []

                if start_date:
                    conditions.append("publish_time >= ?")
                    params.append(start_date)

                if end_date:
                    conditions.append("publish_time <= ?")
                    params.append(end_date)

                if conditions:
                    sql += " WHERE " + " AND ".join(conditions)

                sql += f" ORDER BY publish_time DESC LIMIT {limit}"

                cursor.execute(sql, params)
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()

                results = [dict(zip(columns, row)) for row in rows]

                return {
                    "success": True,
                    "query_type": "posts",
                    "count": len(results),
                    "data": results
                }

            elif query_type == "comments":
                sql = "SELECT * FROM comments"
                conditions = []
                params = []

                if start_date:
                    conditions.append("publish_time >= ?")
                    params.append(start_date)

                if end_date:
                    conditions.append("publish_time <= ?")
                    params.append(end_date)

                if conditions:
                    sql += " WHERE " + " AND ".join(conditions)

                sql += f" ORDER BY publish_time DESC LIMIT {limit}"

                cursor.execute(sql, params)
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()

                results = [dict(zip(columns, row)) for row in rows]

                return {
                    "success": True,
                    "query_type": "comments",
                    "count": len(results),
                    "data": results
                }

            elif query_type == "replies":
                sql = "SELECT * FROM replies"
                conditions = []
                params = []

                if start_date:
                    conditions.append("publish_time >= ?")
                    params.append(start_date)

                if end_date:
                    conditions.append("publish_time <= ?")
                    params.append(end_date)

                if conditions:
                    sql += " WHERE " + " AND ".join(conditions)

                sql += f" ORDER BY publish_time DESC LIMIT {limit}"

                cursor.execute(sql, params)
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()

                results = [dict(zip(columns, row)) for row in rows]

                return {
                    "success": True,
                    "query_type": "replies",
                    "count": len(results),
                    "data": results
                }

            elif query_type == "stats":
                # 统计信息
                cursor.execute("SELECT COUNT(*) FROM posts")
                posts_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM comments")
                comments_count = cursor.fetchone()[0]

                # 检查replies表是否存在
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='replies'")
                has_replies = cursor.fetchone() is not None

                replies_count = 0
                if has_replies:
                    cursor.execute("SELECT COUNT(*) FROM replies")
                    replies_count = cursor.fetchone()[0]

                return {
                    "success": True,
                    "query_type": "stats",
                    "stats": {
                        "posts_count": posts_count,
                        "comments_count": comments_count,
                        "replies_count": replies_count
                    }
                }

            else:
                return {
                    "success": False,
                    "error": f"Unknown query type: {query_type}"
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            conn.close()
