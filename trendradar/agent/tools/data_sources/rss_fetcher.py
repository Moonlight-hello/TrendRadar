"""
RSSFetcherTool - RSS 订阅工具

包装现有的 RSSFetcher 为工具
"""

from typing import List, Dict, Any

from ..base import BaseTool


class RSSFetcherTool(BaseTool):
    """
    RSS 订阅工具

    抓取 RSS 源内容
    """

    def __init__(self):
        """初始化工具"""
        super().__init__()
        self.name = "rss_fetcher"
        self.description = "Fetch RSS feed content"
        self.category = "data_source"
        self.parameters = {
            "feed_url": {
                "type": "string",
                "description": "RSS feed URL",
                "required": True
            },
            "max_age_days": {
                "type": "integer",
                "description": "Maximum age of articles in days",
                "default": 3,
                "required": False
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of items to fetch",
                "default": 50,
                "required": False
            }
        }

    def execute(self, feed_url: str, max_age_days: int = 3, limit: int = 50, **kwargs) -> Dict[str, Any]:
        """
        执行 RSS 抓取

        Args:
            feed_url: RSS 源 URL
            max_age_days: 最大文章年龄（天）
            limit: 最大数量
            **kwargs: 其他参数

        Returns:
            抓取结果，格式:
            {
                "feed_url": "https://...",
                "items": [...],
                "count": 20
            }
        """
        # 验证参数
        self.validate_params(feed_url=feed_url, max_age_days=max_age_days, limit=limit)

        try:
            # 调用现有的 RSSFetcher
            from trendradar.crawler.rss.fetcher import RSSFetcher
            from trendradar.core.config import RSSFeedConfig

            fetcher = RSSFetcher()

            # 创建配置
            feed_config = RSSFeedConfig(
                id="temp_feed",
                name="Temporary Feed",
                url=feed_url,
                enabled=True,
                max_age_days=max_age_days
            )

            # 抓取数据
            items, error = fetcher.fetch_feed(feed_config)

            if error:
                raise Exception(f"RSS fetch error: {error}")

            # 转换格式
            result_items = []
            for item in items[:limit]:
                result_items.append({
                    "title": item.title,
                    "url": item.url,
                    "published_at": item.published_at,
                    "summary": item.summary,
                    "author": item.author
                })

            return {
                "feed_url": feed_url,
                "items": result_items,
                "count": len(result_items),
                "success": True
            }

        except Exception as e:
            raise Exception(f"Failed to fetch RSS feed: {str(e)}")
