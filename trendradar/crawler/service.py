# coding=utf-8
"""
爬虫服务层 - Service Layer

职责：
1. 提供统一的爬虫接口（同步 + 异步）
2. 智能缓存策略（自动决策是读缓存还是触发爬取）
3. 结果封装为 QueryResult
"""

from typing import Optional, Callable
from datetime import datetime

from .types import (
    QueryParams, QueryResult, CrawlTask,
    TaskStatus, TaskId, CacheStrategy
)
from .repository import DataRepository
from .executor import CrawlExecutor
from .task_manager import TaskManager


class CrawlerService:
    """
    爬虫服务

    统一的爬虫接口，提供同步和异步两种模式
    """

    def __init__(
        self,
        repository: DataRepository,
        executor: CrawlExecutor,
        task_manager: TaskManager
    ):
        """
        初始化爬虫服务

        Args:
            repository: 数据仓库
            executor: 爬虫执行器
            task_manager: 任务管理器
        """
        self.repository = repository
        self.executor = executor
        self.task_manager = task_manager

    def query(self, query_params: QueryParams) -> QueryResult:
        """
        查询数据（同步模式）

        根据缓存策略自动决策：
        - AUTO: 有缓存用缓存，无缓存则爬取
        - CACHE_ONLY: 仅使用缓存
        - FORCE_REFRESH: 强制刷新（忽略缓存）
        - NO_CACHE: 不使用缓存（爬取但不保存）

        Args:
            query_params: 查询参数

        Returns:
            查询结果
        """
        query_time = datetime.now()

        # 1. 尝试从缓存获取
        if query_params.should_use_cache():
            cached_items = self.repository.query_cache(query_params)
            if cached_items is not None:
                # 缓存命中
                return QueryResult(
                    success=True,
                    from_cache=True,
                    items=cached_items,
                    query_params=query_params,
                    query_time=query_time,
                    message="Data from cache"
                )

        # 2. CACHE_ONLY 模式且缓存未命中
        if query_params.cache_strategy == CacheStrategy.CACHE_ONLY:
            return QueryResult(
                success=False,
                from_cache=False,
                items=[],
                query_params=query_params,
                query_time=query_time,
                message="Cache miss and CACHE_ONLY strategy"
            )

        # 3. 执行爬取
        try:
            items = self.executor.execute_sync(query_params)

            # 4. 保存到缓存（如果需要）
            if query_params.should_save_cache():
                self.repository.save_cache(query_params, items)

            return QueryResult(
                success=True,
                from_cache=False,
                items=items,
                query_params=query_params,
                query_time=query_time,
                message=f"Crawled {len(items)} items"
            )

        except Exception as e:
            # 爬取失败
            return QueryResult(
                success=False,
                from_cache=False,
                items=[],
                query_params=query_params,
                query_time=query_time,
                message="Crawl failed",
                error=str(e)
            )

    def query_async(
        self,
        query_params: QueryParams,
        callback: Optional[Callable[[CrawlTask], None]] = None
    ) -> QueryResult:
        """
        查询数据（异步模式）

        立即返回结果：
        - 如果缓存命中，直接返回数据
        - 如果缓存未命中，提交爬取任务，返回任务ID

        Args:
            query_params: 查询参数
            callback: 任务完成回调（可选）

        Returns:
            查询结果（包含任务ID）
        """
        query_time = datetime.now()

        # 1. 尝试从缓存获取
        if query_params.should_use_cache():
            cached_items = self.repository.query_cache(query_params)
            if cached_items is not None:
                # 缓存命中，直接返回
                return QueryResult(
                    success=True,
                    from_cache=True,
                    items=cached_items,
                    query_params=query_params,
                    query_time=query_time,
                    is_async=False,
                    message="Data from cache"
                )

        # 2. CACHE_ONLY 模式且缓存未命中
        if query_params.cache_strategy == CacheStrategy.CACHE_ONLY:
            return QueryResult(
                success=False,
                from_cache=False,
                items=[],
                query_params=query_params,
                query_time=query_time,
                is_async=False,
                message="Cache miss and CACHE_ONLY strategy"
            )

        # 3. 提交异步爬取任务
        try:
            task_id = self.task_manager.submit_task(query_params, callback)

            return QueryResult(
                success=True,
                from_cache=False,
                items=[],
                query_params=query_params,
                query_time=query_time,
                is_async=True,
                task_id=task_id,
                task_status=TaskStatus.PENDING,
                message=f"Task submitted: {task_id}"
            )

        except Exception as e:
            # 任务提交失败
            return QueryResult(
                success=False,
                from_cache=False,
                items=[],
                query_params=query_params,
                query_time=query_time,
                is_async=False,
                message="Task submission failed",
                error=str(e)
            )

    def get_task_result(self, task_id: TaskId) -> QueryResult:
        """
        获取异步任务结果

        Args:
            task_id: 任务ID

        Returns:
            查询结果
        """
        query_time = datetime.now()

        # 获取任务
        task = self.repository.get_task(task_id)
        if not task:
            return QueryResult(
                success=False,
                from_cache=False,
                items=[],
                query_params=None,  # type: ignore
                query_time=query_time,
                is_async=True,
                task_id=task_id,
                message="Task not found",
                error="Task ID does not exist"
            )

        # 检查任务状态
        if task.status == TaskStatus.COMPLETED:
            return QueryResult(
                success=True,
                from_cache=False,
                items=task.items,
                query_params=task.query_params,
                query_time=query_time,
                is_async=True,
                task_id=task_id,
                task_status=task.status,
                message=f"Task completed with {len(task.items)} items"
            )

        elif task.status == TaskStatus.FAILED:
            return QueryResult(
                success=False,
                from_cache=False,
                items=[],
                query_params=task.query_params,
                query_time=query_time,
                is_async=True,
                task_id=task_id,
                task_status=task.status,
                message="Task failed",
                error=task.error
            )

        else:
            # 任务还在运行中或等待中
            return QueryResult(
                success=True,
                from_cache=False,
                items=[],
                query_params=task.query_params,
                query_time=query_time,
                is_async=True,
                task_id=task_id,
                task_status=task.status,
                message=f"Task status: {task.status}"
            )

    def wait_for_task(
        self,
        task_id: TaskId,
        timeout: Optional[float] = None
    ) -> QueryResult:
        """
        等待异步任务完成（阻塞）

        Args:
            task_id: 任务ID
            timeout: 超时时间（秒）

        Returns:
            查询结果
        """
        # 等待任务完成
        task = self.task_manager.wait_for_task(task_id, timeout)

        if not task:
            # 超时或任务不存在
            return QueryResult(
                success=False,
                from_cache=False,
                items=[],
                query_params=None,  # type: ignore
                query_time=datetime.now(),
                is_async=True,
                task_id=task_id,
                message="Task wait timeout or not found",
                error="Timeout or task does not exist"
            )

        # 返回结果
        return self.get_task_result(task_id)

    def get_stats(self) -> dict:
        """
        获取统计信息

        Returns:
            统计数据
        """
        return self.repository.get_stats()

    def clean_expired_cache(self) -> int:
        """
        清理过期缓存

        Returns:
            清理的记录数
        """
        return self.repository.clean_expired_cache()
