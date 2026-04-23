"""
HotNewsScraperTool - 热榜爬虫工具

包装现有的 DataFetcher 为工具
"""

from typing import List, Dict, Any

from ..base import BaseTool


class HotNewsScraperTool(BaseTool):
    """
    热榜爬虫工具

    爬取各平台热榜数据
    """

    def __init__(self):
        """初始化工具"""
        super().__init__()
        self.name = "hot_news_scraper"
        self.description = "Scrape hot news from various platforms"
        self.category = "data_source"
        self.parameters = {
            "platform": {
                "type": "string",
                "description": "Platform name (zhihu, weibo, toutiao, etc.)",
                "required": True
            },
            "limit": {
                "type": "integer",
                "description": "Number of news items to fetch",
                "default": 50,
                "required": False
            }
        }

    def execute(self, platform: str, limit: int = 50, **kwargs) -> Dict[str, Any]:
        """
        执行爬取

        Args:
            platform: 平台名称
            limit: 获取数量
            **kwargs: 其他参数

        Returns:
            爬取结果，格式:
            {
                "platform": "zhihu",
                "items": [...],
                "count": 50
            }
        """
        # 验证参数
        self.validate_params(platform=platform, limit=limit)

        try:
            # 调用现有的 DataFetcher
            from trendradar.crawler.fetcher import DataFetcher

            fetcher = DataFetcher()
            results, id_to_name, failed_ids = fetcher.crawl_websites([platform])

            # 转换格式
            items = []
            if platform in results:
                platform_data = results[platform]
                for title, data in list(platform_data.items())[:limit]:
                    items.append({
                        "title": title,
                        "rank": data.get("ranks", [0])[0] if data.get("ranks") else None,
                        "url": data.get("url"),
                        "mobile_url": data.get("mobileUrl")
                    })

            return {
                "platform": platform,
                "platform_name": id_to_name.get(platform, platform),
                "items": items,
                "count": len(items),
                "success": platform not in failed_ids
            }

        except Exception as e:
            raise Exception(f"Failed to scrape {platform}: {str(e)}")
