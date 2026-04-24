# coding=utf-8
"""
爬虫适配器层 - Adapter Layer

职责：
1. 封装不同数据源（NewsNow API、MediaCrawlerPro）
2. 将原始数据转换为统一的 CrawlItem 格式
3. 提供查询指令生成（query primitive generation）
"""

from .newsnow import NewsNowAdapter

__all__ = [
    "NewsNowAdapter",
]
