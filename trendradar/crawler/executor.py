# coding=utf-8
"""
爬虫执行器 - Infrastructure Layer

职责：
1. 执行实际的网络爬取
2. 调用不同的 Adapter
3. 处理执行错误和重试
"""

import asyncio
from typing import List, Optional, Dict, Type
from datetime import datetime

from .types import (
    QueryParams, CrawlItem, Platform,
    QueryType, CrawlTask, TaskStatus
)


class BaseCrawlerAdapter:
    """
    爬虫适配器基类

    所有具体的平台适配器必须继承此类
    """

    # 支持的平台
    SUPPORTED_PLATFORMS: List[Platform] = []

    # 支持的查询类型
    SUPPORTED_QUERY_TYPES: List[QueryType] = []

    def can_handle(self, query_params: QueryParams) -> bool:
        """
        检查是否能处理此查询

        Args:
            query_params: 查询参数

        Returns:
            是否能处理
        """
        return (
            query_params.platform in self.SUPPORTED_PLATFORMS and
            query_params.query_type in self.SUPPORTED_QUERY_TYPES
        )

    async def crawl(self, query_params: QueryParams) -> List[CrawlItem]:
        """
        执行爬取（抽象方法）

        Args:
            query_params: 查询参数

        Returns:
            爬取结果列表

        Raises:
            NotImplementedError: 子类必须实现
        """
        raise NotImplementedError("Subclass must implement crawl()")

    def get_name(self) -> str:
        """获取适配器名称"""
        return self.__class__.__name__


class CrawlExecutor:
    """
    爬虫执行器

    负责调度不同的爬虫适配器执行实际爬取
    """

    def __init__(self):
        """初始化执行器"""
        self._adapters: List[BaseCrawlerAdapter] = []
        self._adapter_cache: Dict[Platform, BaseCrawlerAdapter] = {}

    def register_adapter(self, adapter: BaseCrawlerAdapter):
        """
        注册爬虫适配器

        Args:
            adapter: 爬虫适配器实例
        """
        self._adapters.append(adapter)

        # 清空缓存，强制重新查找
        self._adapter_cache.clear()

    def get_adapter(self, query_params: QueryParams) -> Optional[BaseCrawlerAdapter]:
        """
        获取适配器

        根据查询参数选择合适的适配器

        Args:
            query_params: 查询参数

        Returns:
            适配器实例，没有合适的返回 None
        """
        # 检查缓存
        cache_key = query_params.platform
        if cache_key in self._adapter_cache:
            adapter = self._adapter_cache[cache_key]
            if adapter.can_handle(query_params):
                return adapter

        # 查找合适的适配器
        for adapter in self._adapters:
            if adapter.can_handle(query_params):
                self._adapter_cache[cache_key] = adapter
                return adapter

        return None

    async def execute(self, query_params: QueryParams) -> List[CrawlItem]:
        """
        执行爬取

        Args:
            query_params: 查询参数

        Returns:
            爬取结果列表

        Raises:
            ValueError: 没有合适的适配器
            Exception: 爬取失败
        """
        # 获取适配器
        adapter = self.get_adapter(query_params)
        if not adapter:
            raise ValueError(
                f"No adapter found for platform={query_params.platform}, "
                f"query_type={query_params.query_type}"
            )

        # 执行爬取
        try:
            items = await adapter.crawl(query_params)
            return items
        except Exception as e:
            raise Exception(
                f"Crawl failed with adapter {adapter.get_name()}: {str(e)}"
            ) from e

    def execute_sync(self, query_params: QueryParams) -> List[CrawlItem]:
        """
        同步执行爬取（阻塞）

        Args:
            query_params: 查询参数

        Returns:
            爬取结果列表
        """
        # 获取或创建事件循环
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # 执行异步方法
        return loop.run_until_complete(self.execute(query_params))

    def get_supported_platforms(self) -> List[Platform]:
        """
        获取所有支持的平台

        Returns:
            平台列表
        """
        platforms = set()
        for adapter in self._adapters:
            platforms.update(adapter.SUPPORTED_PLATFORMS)
        return list(platforms)

    def get_supported_query_types(self, platform: Platform) -> List[QueryType]:
        """
        获取指定平台支持的查询类型

        Args:
            platform: 平台

        Returns:
            查询类型列表
        """
        query_types = set()
        for adapter in self._adapters:
            if platform in adapter.SUPPORTED_PLATFORMS:
                query_types.update(adapter.SUPPORTED_QUERY_TYPES)
        return list(query_types)

    def execute_task(self, task: CrawlTask) -> CrawlTask:
        """
        执行爬取任务（同步）

        更新任务状态并返回

        Args:
            task: 爬取任务

        Returns:
            更新后的任务
        """
        # 标记为运行中
        task.mark_running()

        try:
            # 执行爬取
            items = self.execute_sync(task.query_params)

            # 标记为完成
            task.mark_completed(items)

        except Exception as e:
            # 标记为失败
            error_msg = str(e)
            task.mark_failed(error_msg)

        return task

    async def execute_task_async(self, task: CrawlTask) -> CrawlTask:
        """
        执行爬取任务（异步）

        更新任务状态并返回

        Args:
            task: 爬取任务

        Returns:
            更新后的任务
        """
        # 标记为运行中
        task.mark_running()

        try:
            # 执行爬取
            items = await self.execute(task.query_params)

            # 标记为完成
            task.mark_completed(items)

        except Exception as e:
            # 标记为失败
            error_msg = str(e)
            task.mark_failed(error_msg)

        return task
