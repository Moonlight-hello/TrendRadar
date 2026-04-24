# coding=utf-8
"""
NewsNow API 适配器 - Adapter Layer

职责：
1. 封装 NewsNow API (https://newsnow.busiyi.world/api/s)
2. 将原始数据转换为标准 CrawlItem 格式
3. 支持热榜数据获取
"""

import json
import random
import time
from typing import List, Optional
from datetime import datetime

import requests

from ..types import (
    QueryParams, CrawlItem, Platform, QueryType
)
from ..executor import BaseCrawlerAdapter


class NewsNowAdapter(BaseCrawlerAdapter):
    """
    NewsNow API 适配器

    支持平台: 知乎、微博、B站
    支持查询类型: TRENDING (热榜)
    """

    # 支持的平台
    SUPPORTED_PLATFORMS = [
        Platform.ZHIHU,
        Platform.WEIBO,
        Platform.BILIBILI,
    ]

    # 支持的查询类型
    SUPPORTED_QUERY_TYPES = [
        QueryType.TRENDING,
    ]

    # 平台ID映射 (NewsNow API 使用的ID)
    PLATFORM_ID_MAP = {
        Platform.ZHIHU: "zhihu",
        Platform.WEIBO: "weibo",
        Platform.BILIBILI: "bilibili",
    }

    # API配置
    API_URL = "https://newsnow.busiyi.world/api/s"
    DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Connection": "keep-alive",
        "Cache-Control": "no-cache",
    }

    def __init__(self, proxy_url: Optional[str] = None):
        """
        初始化适配器

        Args:
            proxy_url: 代理服务器 URL（可选）
        """
        self.proxy_url = proxy_url

    async def crawl(self, query_params: QueryParams) -> List[CrawlItem]:
        """
        执行爬取

        Args:
            query_params: 查询参数

        Returns:
            爬取结果列表
        """
        # 验证参数
        if not self.can_handle(query_params):
            raise ValueError(
                f"NewsNowAdapter cannot handle platform={query_params.platform}, "
                f"query_type={query_params.query_type}"
            )

        # 获取平台ID
        platform_id = self.PLATFORM_ID_MAP.get(query_params.platform)
        if not platform_id:
            raise ValueError(f"Unknown platform: {query_params.platform}")

        # 构建请求
        url = f"{self.API_URL}?id={platform_id}&latest"

        proxies = None
        if self.proxy_url:
            proxies = {"http": self.proxy_url, "https": self.proxy_url}

        # 发送请求（带重试）
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.get(
                    url,
                    proxies=proxies,
                    headers=self.DEFAULT_HEADERS,
                    timeout=10,
                    verify=False,
                )
                response.raise_for_status()

                # 解析响应
                data = response.json()

                # 检查状态
                status = data.get("status", "unknown")
                if status not in ["success", "cache"]:
                    raise ValueError(f"API returned status: {status}")

                # 转换为 CrawlItem
                items = self._parse_items(data, query_params)

                # 应用限制
                if query_params.limit > 0:
                    items = items[:query_params.limit]

                return items

            except Exception as e:
                if attempt < max_retries - 1:
                    # 重试等待
                    wait_time = random.uniform(2, 4) + attempt * random.uniform(1, 2)
                    time.sleep(wait_time)
                else:
                    # 最后一次重试失败
                    raise Exception(
                        f"NewsNow API request failed after {max_retries} attempts: {str(e)}"
                    ) from e

        return []

    def _parse_items(
        self,
        data: dict,
        query_params: QueryParams
    ) -> List[CrawlItem]:
        """
        解析 NewsNow API 响应

        Args:
            data: API 响应数据
            query_params: 查询参数

        Returns:
            CrawlItem 列表
        """
        items = []
        crawl_time = datetime.now()

        for index, raw_item in enumerate(data.get("items", []), 1):
            # 获取标题
            title = raw_item.get("title")
            if not title or not str(title).strip():
                continue
            title = str(title).strip()

            # 获取 URL
            url = raw_item.get("url", "")
            mobile_url = raw_item.get("mobileUrl", "")

            # 获取其他字段
            extra = raw_item.get("extra", {})

            # 构造 CrawlItem
            item = CrawlItem(
                id=self._generate_item_id(query_params.platform, index, title),
                platform=query_params.platform,
                content_type=query_params.query_type,
                title=title,
                content=None,  # NewsNow API 不返回正文
                url=url or mobile_url,
                author_id=None,
                author_name=None,
                publish_time=None,  # NewsNow API 不返回发布时间
                crawl_time=crawl_time,
                like_count=0,
                comment_count=0,
                share_count=0,
                view_count=0,
                extra={
                    "rank": index,
                    "mobile_url": mobile_url,
                    **extra
                }
            )

            items.append(item)

        return items

    def _generate_item_id(
        self,
        platform: Platform,
        rank: int,
        title: str
    ) -> str:
        """
        生成数据项ID

        Args:
            platform: 平台
            rank: 排名
            title: 标题

        Returns:
            唯一ID
        """
        # 使用平台+排名+标题哈希
        import hashlib
        title_hash = hashlib.md5(title.encode('utf-8')).hexdigest()[:8]
        return f"{platform.value}_trending_{rank}_{title_hash}"

    def get_query_instructions(self, query_params: QueryParams) -> str:
        """
        生成查询指令（自然语言描述）

        用于 Agent 理解查询需求

        Args:
            query_params: 查询参数

        Returns:
            查询指令字符串
        """
        platform_name = {
            Platform.ZHIHU: "知乎",
            Platform.WEIBO: "微博",
            Platform.BILIBILI: "B站",
        }.get(query_params.platform, str(query_params.platform))

        time_range_desc = self._get_time_range_description(query_params)

        return (
            f"获取{platform_name}热榜数据，"
            f"时间范围：{time_range_desc}，"
            f"数量限制：{query_params.limit}条"
        )

    def _get_time_range_description(self, query_params: QueryParams) -> str:
        """获取时间范围描述"""
        if query_params.time_range:
            time_range_map = {
                "last_hour": "最近1小时",
                "last_3h": "最近3小时",
                "last_6h": "最近6小时",
                "last_12h": "最近12小时",
                "last_24h": "最近24小时",
                "last_3d": "最近3天",
                "last_7d": "最近7天",
                "last_30d": "最近30天",
            }
            return time_range_map.get(str(query_params.time_range), "最近24小时")

        start_time, end_time = query_params.get_time_range_tuple()
        return f"{start_time.strftime('%Y-%m-%d %H:%M')} 至 {end_time.strftime('%Y-%m-%d %H:%M')}"
