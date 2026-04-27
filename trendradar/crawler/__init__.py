# coding=utf-8
"""
TrendRadar 爬虫系统

分层架构：
- Infrastructure Layer (基础设施层): 数据存储、任务管理、爬虫执行
- Adapter Layer (适配器层): 各平台爬虫适配器
- Service Layer (服务层): 统一的爬虫服务接口
"""

# 原有的 DataFetcher (NewsNow API)
from trendradar.crawler.fetcher import DataFetcher

# 东方财富爬虫模块
from trendradar.crawler.eastmoney import (
    EastMoneyCrawler,
    EastMoneyClient,
    crawl_eastmoney_stock,
    crawl_eastmoney_stocks,
)

# 类型定义（最基础）
from .types import (
    # 枚举
    Platform,
    QueryType,
    TimeRange,
    TaskStatus,
    CacheStrategy,
    SortOrder,

    # 数据模型
    QueryParams,
    CrawlItem,
    QueryResult,
    CrawlTask,

    # 类型别名
    CacheKey,
    TaskId,
)

# Infrastructure Layer
from .repository import DataRepository
from .executor import BaseCrawlerAdapter, CrawlExecutor
from .task_manager import TaskManager

# Adapter Layer
from .adapters import NewsNowAdapter

# Service Layer
from .service import CrawlerService

# 版本信息
__version__ = "6.1.0"

__all__ = [
    # 原有
    "DataFetcher",

    # 东方财富爬虫
    "EastMoneyCrawler",
    "EastMoneyClient",
    "crawl_eastmoney_stock",
    "crawl_eastmoney_stocks",

    # 枚举
    "Platform",
    "QueryType",
    "TimeRange",
    "TaskStatus",
    "CacheStrategy",
    "SortOrder",

    # 数据模型
    "QueryParams",
    "CrawlItem",
    "QueryResult",
    "CrawlTask",

    # 类型别名
    "CacheKey",
    "TaskId",

    # Infrastructure Layer
    "DataRepository",
    "BaseCrawlerAdapter",
    "CrawlExecutor",
    "TaskManager",

    # Adapter Layer
    "NewsNowAdapter",

    # Service Layer
    "CrawlerService",
]
