# coding=utf-8
"""
任务管理器 - Infrastructure Layer

职责：
1. 管理异步爬取任务
2. 任务队列调度
3. 任务状态跟踪
4. 回调通知
"""

import asyncio
import uuid
from typing import Optional, Callable, Dict, List
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from .types import (
    QueryParams, CrawlTask, TaskStatus, TaskId
)
from .repository import DataRepository
from .executor import CrawlExecutor


class TaskManager:
    """
    任务管理器

    管理异步爬取任务的生命周期
    """

    def __init__(
        self,
        repository: DataRepository,
        executor: CrawlExecutor,
        max_workers: int = 5
    ):
        """
        初始化任务管理器

        Args:
            repository: 数据仓库
            executor: 爬虫执行器
            max_workers: 最大并发数
        """
        self.repository = repository
        self.executor = executor
        self.max_workers = max_workers

        # 线程池
        self._thread_pool = ThreadPoolExecutor(max_workers=max_workers)

        # 回调函数
        self._callbacks: Dict[TaskId, Callable[[CrawlTask], None]] = {}

        # 运行中的任务
        self._running_tasks: Dict[TaskId, asyncio.Task] = {}

    def create_task(
        self,
        query_params: QueryParams,
        callback: Optional[Callable[[CrawlTask], None]] = None
    ) -> TaskId:
        """
        创建爬取任务

        Args:
            query_params: 查询参数
            callback: 完成回调函数（可选）

        Returns:
            任务ID
        """
        # 生成任务ID
        task_id = self._generate_task_id()

        # 创建任务对象
        task = CrawlTask(
            id=task_id,
            query_params=query_params,
            status=TaskStatus.PENDING,
            adapter_name=None,
            created_at=datetime.now()
        )

        # 保存到数据库
        self.repository.save_task(task)

        # 注册回调
        if callback:
            self._callbacks[task_id] = callback

        return task_id

    def submit_task(
        self,
        query_params: QueryParams,
        callback: Optional[Callable[[CrawlTask], None]] = None
    ) -> TaskId:
        """
        提交任务并立即开始执行

        Args:
            query_params: 查询参数
            callback: 完成回调函数（可选）

        Returns:
            任务ID
        """
        # 创建任务
        task_id = self.create_task(query_params, callback)

        # 立即开始执行
        self._start_task(task_id)

        return task_id

    def _start_task(self, task_id: TaskId):
        """
        开始执行任务

        Args:
            task_id: 任务ID
        """
        # 获取任务
        task = self.repository.get_task(task_id)
        if not task:
            return

        # 如果任务已在运行中，跳过
        if task_id in self._running_tasks:
            return

        # 提交到线程池执行
        future = self._thread_pool.submit(self._execute_task, task)

        # 记录运行中的任务
        # 注意：这里不是 asyncio.Task，但我们用同样的字典管理
        # TODO: 如果需要真正的异步支持，改用 asyncio

    def _execute_task(self, task: CrawlTask):
        """
        执行任务（在线程池中运行）

        Args:
            task: 爬取任务
        """
        task_id = task.id

        try:
            # 更新状态为运行中
            self.repository.update_task_status(task_id, TaskStatus.RUNNING)

            # 执行爬取
            updated_task = self.executor.execute_task(task)

            # 保存结果到数据库
            self.repository.save_task(updated_task)

            # 保存到缓存（如果任务成功）
            if updated_task.status == TaskStatus.COMPLETED:
                self.repository.save_cache(
                    updated_task.query_params,
                    updated_task.items
                )

            # 调用回调
            if task_id in self._callbacks:
                callback = self._callbacks[task_id]
                callback(updated_task)
                del self._callbacks[task_id]

        except Exception as e:
            # 更新状态为失败
            error_msg = str(e)
            self.repository.update_task_status(
                task_id,
                TaskStatus.FAILED,
                error=error_msg
            )

        finally:
            # 从运行中移除
            if task_id in self._running_tasks:
                del self._running_tasks[task_id]

    def get_task_status(self, task_id: TaskId) -> Optional[TaskStatus]:
        """
        获取任务状态

        Args:
            task_id: 任务ID

        Returns:
            任务状态，不存在返回 None
        """
        task = self.repository.get_task(task_id)
        if task:
            return task.status
        return None

    def wait_for_task(
        self,
        task_id: TaskId,
        timeout: Optional[float] = None
    ) -> Optional[CrawlTask]:
        """
        等待任务完成（阻塞）

        Args:
            task_id: 任务ID
            timeout: 超时时间（秒），None 表示无限等待

        Returns:
            完成的任务，超时返回 None
        """
        import time

        start_time = time.time()

        while True:
            # 获取任务
            task = self.repository.get_task(task_id)
            if not task:
                return None

            # 检查是否完成
            if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
                return task

            # 检查超时
            if timeout is not None:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    return None

            # 短暂休眠
            time.sleep(0.5)

    def cancel_task(self, task_id: TaskId) -> bool:
        """
        取消任务

        Args:
            task_id: 任务ID

        Returns:
            是否成功取消
        """
        # 获取任务
        task = self.repository.get_task(task_id)
        if not task:
            return False

        # 只能取消等待中的任务
        if task.status != TaskStatus.PENDING:
            return False

        # 更新状态
        success = self.repository.update_task_status(task_id, TaskStatus.CANCELLED)

        # 移除回调
        if task_id in self._callbacks:
            del self._callbacks[task_id]

        return success

    def get_pending_tasks(self) -> List[CrawlTask]:
        """
        获取所有等待中的任务

        Returns:
            任务列表
        """
        # TODO: 在 DataRepository 中实现此方法
        return []

    def cleanup_old_tasks(self, days: int = 7) -> int:
        """
        清理旧任务

        Args:
            days: 保留最近几天的任务

        Returns:
            清理的任务数
        """
        # TODO: 在 DataRepository 中实现此方法
        return 0

    def shutdown(self, wait: bool = True):
        """
        关闭任务管理器

        Args:
            wait: 是否等待所有任务完成
        """
        self._thread_pool.shutdown(wait=wait)

    def _generate_task_id(self) -> TaskId:
        """
        生成任务ID

        Returns:
            任务ID
        """
        return f"task_{uuid.uuid4().hex[:16]}"
