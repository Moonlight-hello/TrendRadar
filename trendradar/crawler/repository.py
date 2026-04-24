# coding=utf-8
"""
数据仓库 - Infrastructure Layer

职责：
1. 查询缓存数据
2. 保存爬取结果
3. 管理缓存过期
"""

import sqlite3
import json
from typing import Optional, List
from datetime import datetime, timedelta
from pathlib import Path

from .types import (
    QueryParams, CrawlItem, CrawlTask,
    Platform, QueryType, TaskStatus,
    CacheKey, TaskId
)


class DataRepository:
    """
    数据仓库

    提供统一的数据访问接口，屏蔽底层存储细节
    """

    def __init__(self, db_path: str):
        """
        初始化数据仓库

        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self._ensure_db_dir()
        self._init_database()

    def _ensure_db_dir(self):
        """确保数据库目录存在"""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

    def _init_database(self):
        """初始化数据库表结构"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 爬取缓存表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS crawl_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cache_key TEXT UNIQUE NOT NULL,

                -- 查询参数
                platform TEXT NOT NULL,
                query_type TEXT NOT NULL,
                keyword TEXT,
                user_id TEXT,
                post_id TEXT,

                -- 时间信息
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,

                -- 数据
                items TEXT NOT NULL,  -- JSON array
                item_count INTEGER NOT NULL,

                -- 索引
                INDEX idx_cache_key (cache_key),
                INDEX idx_platform_query (platform, query_type),
                INDEX idx_expires (expires_at)
            )
        """)

        # 爬取任务表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS crawl_tasks (
                id TEXT PRIMARY KEY,

                -- 查询参数
                query_params TEXT NOT NULL,  -- JSON

                -- 任务状态
                status TEXT NOT NULL,
                adapter_name TEXT,

                -- 时间信息
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,

                -- 结果
                items TEXT,  -- JSON array
                item_count INTEGER DEFAULT 0,
                error TEXT,

                -- 重试信息
                retry_count INTEGER DEFAULT 0,
                max_retries INTEGER DEFAULT 3,

                -- 索引
                INDEX idx_status (status),
                INDEX idx_created (created_at)
            )
        """)

        conn.commit()
        conn.close()

    # ========== 缓存查询接口 ==========

    def query_cache(
        self,
        query_params: QueryParams
    ) -> Optional[List[CrawlItem]]:
        """
        查询缓存

        Args:
            query_params: 查询参数

        Returns:
            如果缓存存在且有效，返回数据列表；否则返回 None
        """
        # 检查是否应该使用缓存
        if not query_params.should_use_cache():
            return None

        cache_key = query_params.to_cache_key()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT items, created_at, expires_at
            FROM crawl_cache
            WHERE cache_key = ?
              AND expires_at > datetime('now')
        """, (cache_key,))

        row = cursor.fetchone()
        conn.close()

        if row:
            items_json, created_at, expires_at = row
            items_data = json.loads(items_json)

            # 反序列化为 CrawlItem 对象
            items = [self._dict_to_crawl_item(item) for item in items_data]
            return items

        return None

    def save_cache(
        self,
        query_params: QueryParams,
        items: List[CrawlItem]
    ) -> bool:
        """
        保存到缓存

        Args:
            query_params: 查询参数
            items: 爬取数据

        Returns:
            是否保存成功
        """
        # 检查是否应该保存缓存
        if not query_params.should_save_cache():
            return False

        cache_key = query_params.to_cache_key()
        start_time, end_time = query_params.get_time_range_tuple()
        expires_at = datetime.now() + timedelta(seconds=query_params.cache_ttl_seconds)

        # 序列化 items
        items_json = json.dumps(
            [item.to_dict() for item in items],
            ensure_ascii=False
        )

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO crawl_cache (
                cache_key, platform, query_type, keyword, user_id, post_id,
                start_time, end_time, expires_at,
                items, item_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            cache_key,
            str(query_params.platform),
            str(query_params.query_type),
            query_params.keyword,
            query_params.user_id,
            query_params.post_id,
            start_time,
            end_time,
            expires_at,
            items_json,
            len(items)
        ))

        conn.commit()
        conn.close()

        return True

    def delete_cache(self, cache_key: CacheKey) -> bool:
        """
        删除缓存

        Args:
            cache_key: 缓存键

        Returns:
            是否删除成功
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM crawl_cache
            WHERE cache_key = ?
        """, (cache_key,))

        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()

        return deleted

    def clean_expired_cache(self) -> int:
        """
        清理过期缓存

        Returns:
            清理的记录数
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM crawl_cache
            WHERE expires_at < datetime('now')
        """)

        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()

        return deleted_count

    # ========== 任务管理接口 ==========

    def save_task(self, task: CrawlTask) -> bool:
        """
        保存任务

        Args:
            task: 爬取任务

        Returns:
            是否保存成功
        """
        # 序列化 query_params
        query_params_json = json.dumps({
            "platform": str(task.query_params.platform),
            "query_type": str(task.query_params.query_type),
            "keyword": task.query_params.keyword,
            "user_id": task.query_params.user_id,
            "post_id": task.query_params.post_id,
            "limit": task.query_params.limit,
        }, ensure_ascii=False)

        # 序列化 items（如果有）
        items_json = None
        if task.items:
            items_json = json.dumps(
                [item.to_dict() for item in task.items],
                ensure_ascii=False
            )

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO crawl_tasks (
                id, query_params, status, adapter_name,
                created_at, started_at, completed_at,
                items, item_count, error,
                retry_count, max_retries
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            task.id,
            query_params_json,
            str(task.status),
            task.adapter_name,
            task.created_at,
            task.started_at,
            task.completed_at,
            items_json,
            len(task.items),
            task.error,
            task.retry_count,
            task.max_retries
        ))

        conn.commit()
        conn.close()

        return True

    def get_task(self, task_id: TaskId) -> Optional[CrawlTask]:
        """
        获取任务

        Args:
            task_id: 任务ID

        Returns:
            任务对象，不存在返回 None
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, query_params, status, adapter_name,
                   created_at, started_at, completed_at,
                   items, error, retry_count, max_retries
            FROM crawl_tasks
            WHERE id = ?
        """, (task_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        # 解析行数据
        (
            task_id, query_params_json, status_str, adapter_name,
            created_at, started_at, completed_at,
            items_json, error, retry_count, max_retries
        ) = row

        # 反序列化 query_params（简化版）
        # TODO: 完整的 QueryParams 反序列化
        query_params_dict = json.loads(query_params_json)

        # 反序列化 items
        items = []
        if items_json:
            items_data = json.loads(items_json)
            items = [self._dict_to_crawl_item(item) for item in items_data]

        # 构造 CrawlTask
        # 注意：这里需要完整的 QueryParams，暂时简化处理
        # TODO: 完善 QueryParams 的序列化/反序列化

        return None  # TODO: 实现完整的反序列化

    def update_task_status(
        self,
        task_id: TaskId,
        status: TaskStatus,
        error: Optional[str] = None
    ) -> bool:
        """
        更新任务状态

        Args:
            task_id: 任务ID
            status: 新状态
            error: 错误信息（如果失败）

        Returns:
            是否更新成功
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        now = datetime.now()

        if status == TaskStatus.RUNNING:
            cursor.execute("""
                UPDATE crawl_tasks
                SET status = ?, started_at = ?
                WHERE id = ?
            """, (str(status), now, task_id))

        elif status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
            cursor.execute("""
                UPDATE crawl_tasks
                SET status = ?, completed_at = ?, error = ?
                WHERE id = ?
            """, (str(status), now, error, task_id))

        else:
            cursor.execute("""
                UPDATE crawl_tasks
                SET status = ?
                WHERE id = ?
            """, (str(status), task_id))

        updated = cursor.rowcount > 0
        conn.commit()
        conn.close()

        return updated

    # ========== 辅助方法 ==========

    def _dict_to_crawl_item(self, data: dict) -> CrawlItem:
        """字典转 CrawlItem"""
        return CrawlItem(
            id=data["id"],
            platform=Platform(data["platform"]),
            content_type=QueryType[data["content_type"].upper()],
            title=data.get("title"),
            content=data.get("content"),
            url=data.get("url"),
            author_id=data.get("author_id"),
            author_name=data.get("author_name"),
            publish_time=datetime.fromisoformat(data["publish_time"]) if data.get("publish_time") else None,
            crawl_time=datetime.fromisoformat(data["crawl_time"]),
            like_count=data.get("like_count", 0),
            comment_count=data.get("comment_count", 0),
            share_count=data.get("share_count", 0),
            view_count=data.get("view_count", 0),
            extra=data.get("extra", {})
        )

    def get_stats(self) -> dict:
        """
        获取统计信息

        Returns:
            统计数据字典
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 缓存统计
        cursor.execute("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN expires_at > datetime('now') THEN 1 ELSE 0 END) as valid
            FROM crawl_cache
        """)
        cache_total, cache_valid = cursor.fetchone()

        # 任务统计
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM crawl_tasks
            GROUP BY status
        """)
        task_stats = {row[0]: row[1] for row in cursor.fetchall()}

        conn.close()

        return {
            "cache": {
                "total": cache_total or 0,
                "valid": cache_valid or 0,
                "expired": (cache_total or 0) - (cache_valid or 0)
            },
            "tasks": task_stats
        }
