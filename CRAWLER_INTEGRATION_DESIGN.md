# TrendRadar 爬虫集成设计方案

> 日期: 2026-04-24

---

## 📖 概念澄清

### 1. API 和服务说明

#### **NewsNow API** (现有)
- **位置**: `trendradar/crawler/fetcher.py`
- **地址**: `https://newsnow.busiyi.world/api/s`
- **功能**: 热榜新闻聚合API
- **支持平台**: 知乎、微博、B站、虎扑等热榜
- **用途**: 获取各平台的热门话题/新闻

#### **New API Gateway** (AI服务，之前混淆了)
- **地址**: `http://45.197.145.24:3000/v1`
- **功能**: AI中转服务（用于LLM调用）
- **用途**: AI分析、文本生成等
- **注意**: 这是AI服务，不是爬虫API！

#### **MediaCrawlerPro** (新集成)
- **位置**: `/Users/wangxinlong/Code/communityspy/MediaCrawlerPro-Python`
- **功能**: 深度社交媒体爬虫
- **支持平台**:
  - 小红书 (xhs)
  - 抖音 (douyin)
  - 快手 (kuaishou)
  - B站 (bilibili)
  - 微博 (weibo)
  - 知乎 (zhihu)
  - 百度贴吧 (tieba)
  - 东方财富 (eastmoney) ✨
- **特点**: 支持搜索、用户主页、评论等深度抓取

---

## 🎯 集成策略

### 数据抓取能力分层

```
┌─────────────────────────────────────────────────┐
│           TrendRadar 数据抓取层                   │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌─────────────────┐      ┌─────────────────┐  │
│  │  NewsNow API    │      │ MediaCrawlerPro │  │
│  │  (热榜聚合)      │      │  (深度抓取)      │  │
│  └─────────────────┘      └─────────────────┘  │
│         ↓                          ↓            │
│  ┌─────────────────────────────────────────┐   │
│  │      统一的 DataSource 接口              │   │
│  │  - fetch_trending()    # 获取热榜       │   │
│  │  - search_posts()      # 搜索帖子       │   │
│  │  - fetch_comments()    # 获取评论       │   │
│  │  - fetch_user_posts()  # 用户帖子       │   │
│  └─────────────────────────────────────────┘   │
│                                                 │
└─────────────────────────────────────────────────┘
```

### 使用场景划分

| 场景 | 使用工具 | 说明 |
|------|---------|------|
| **热榜监控** | NewsNow API | 快速获取各平台热门话题 |
| **深度分析** | MediaCrawlerPro | 搜索关键词、获取评论、分析舆情 |
| **用户追踪** | MediaCrawlerPro | 关注特定用户的发帖 |
| **股票讨论** | MediaCrawlerPro (东方财富) | 股票吧数据抓取 |

---

## 🏗️ 架构设计

### 1. 目录结构

```
trendradar/
├── crawler/
│   ├── __init__.py
│   ├── base.py                    # ✨ 新增: 爬虫基类
│   ├── fetcher.py                 # 现有: NewsNow API
│   ├── adapters/                  # ✨ 新增: 平台适配器
│   │   ├── __init__.py
│   │   ├── newsnow.py            # NewsNow 适配器
│   │   └── mediacrawler.py       # MediaCrawlerPro 适配器
│   └── rss/
│       ├── __init__.py
│       ├── parser.py
│       └── fetcher.py
```

### 2. 统一接口设计

```python
# trendradar/crawler/base.py

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from enum import Enum


class DataSourceType(Enum):
    """数据源类型"""
    TRENDING = "trending"      # 热榜数据
    SEARCH = "search"          # 搜索数据
    COMMENTS = "comments"      # 评论数据
    USER_POSTS = "user_posts"  # 用户帖子


class Platform(Enum):
    """支持的平台"""
    # NewsNow API 支持
    ZHIHU_HOT = "zhihu"
    WEIBO_HOT = "weibo"
    BILIBILI_HOT = "bilibili"

    # MediaCrawlerPro 支持
    XIAOHONGSHU = "xhs"
    DOUYIN = "douyin"
    KUAISHOU = "kuaishou"
    BILIBILI = "bilibili"
    WEIBO = "weibo"
    ZHIHU = "zhihu"
    TIEBA = "tieba"
    EASTMONEY = "eastmoney"


class CrawlerAdapter(ABC):
    """爬虫适配器基类"""

    @abstractmethod
    def get_supported_platforms(self) -> List[Platform]:
        """获取支持的平台列表"""
        pass

    @abstractmethod
    def fetch_trending(
        self,
        platform: Platform,
        limit: int = 50
    ) -> List[Dict]:
        """
        获取热榜数据

        Returns:
            [
                {
                    'title': '标题',
                    'url': '链接',
                    'hot_value': 热度值,
                    'platform': '平台',
                    'timestamp': '时间戳'
                }
            ]
        """
        pass

    @abstractmethod
    def search_posts(
        self,
        platform: Platform,
        keyword: str,
        limit: int = 50,
        **kwargs
    ) -> List[Dict]:
        """
        搜索帖子

        Returns:
            [
                {
                    'id': '帖子ID',
                    'title': '标题',
                    'content': '内容',
                    'author': '作者',
                    'publish_time': '发布时间',
                    'likes': 点赞数,
                    'comments_count': 评论数,
                    'url': '链接',
                    'platform': '平台'
                }
            ]
        """
        pass

    @abstractmethod
    def fetch_comments(
        self,
        platform: Platform,
        post_id: str,
        limit: int = 100
    ) -> List[Dict]:
        """
        获取评论

        Returns:
            [
                {
                    'id': '评论ID',
                    'content': '评论内容',
                    'author': '作者',
                    'publish_time': '发布时间',
                    'likes': 点赞数,
                    'parent_id': '父评论ID'
                }
            ]
        """
        pass
```

### 3. NewsNow 适配器实现

```python
# trendradar/crawler/adapters/newsnow.py

from typing import List, Dict
from ..base import CrawlerAdapter, Platform, DataSourceType
from ..fetcher import DataFetcher


class NewsNowAdapter(CrawlerAdapter):
    """NewsNow API 适配器"""

    def __init__(self, proxy_url: Optional[str] = None):
        self.fetcher = DataFetcher(proxy_url=proxy_url)
        self._platform_mapping = {
            Platform.ZHIHU_HOT: "zhihu-hot",
            Platform.WEIBO_HOT: "weibo-hot",
            Platform.BILIBILI_HOT: "bilibili-hot",
        }

    def get_supported_platforms(self) -> List[Platform]:
        """NewsNow 支持的平台 (仅热榜)"""
        return list(self._platform_mapping.keys())

    def fetch_trending(
        self,
        platform: Platform,
        limit: int = 50
    ) -> List[Dict]:
        """获取热榜数据"""
        if platform not in self._platform_mapping:
            raise ValueError(f"Platform {platform} not supported by NewsNow")

        api_id = self._platform_mapping[platform]
        response, _, _ = self.fetcher.fetch_data(api_id)

        if not response:
            return []

        # 解析响应并标准化
        data = json.loads(response)
        return self._normalize_trending_data(data, platform)

    def search_posts(self, platform: Platform, keyword: str, **kwargs):
        """NewsNow 不支持搜索"""
        raise NotImplementedError("NewsNow does not support search")

    def fetch_comments(self, platform: Platform, post_id: str, **kwargs):
        """NewsNow 不支持评论抓取"""
        raise NotImplementedError("NewsNow does not support comments")

    def _normalize_trending_data(self, data: Dict, platform: Platform) -> List[Dict]:
        """标准化热榜数据"""
        # 具体实现...
        pass
```

### 4. MediaCrawlerPro 适配器实现

```python
# trendradar/crawler/adapters/mediacrawler.py

import sys
from pathlib import Path
from typing import List, Dict, Optional
from ..base import CrawlerAdapter, Platform


class MediaCrawlerAdapter(CrawlerAdapter):
    """MediaCrawlerPro 适配器"""

    def __init__(self, mediacrawler_path: Optional[str] = None):
        """
        初始化 MediaCrawlerPro 适配器

        Args:
            mediacrawler_path: MediaCrawlerPro 项目路径
                默认: /Users/wangxinlong/Code/communityspy/MediaCrawlerPro-Python
        """
        self.mediacrawler_path = mediacrawler_path or \
            "/Users/wangxinlong/Code/communityspy/MediaCrawlerPro-Python"

        # 动态导入 MediaCrawlerPro
        if self.mediacrawler_path not in sys.path:
            sys.path.insert(0, self.mediacrawler_path)

        self._init_crawlers()

    def _init_crawlers(self):
        """初始化各平台爬虫"""
        try:
            # 动态导入平台爬虫
            from media_platform.xhs import XiaoHongShuCrawler
            from media_platform.douyin import DouyinCrawler
            from media_platform.bilibili import BilibiliCrawler
            from media_platform.weibo import WeiboCrawler
            from media_platform.zhihu import ZhihuCrawler
            from media_platform.tieba import TiebaCrawler
            from media_platform.eastmoney import EastMoneyCrawler

            self.crawlers = {
                Platform.XIAOHONGSHU: XiaoHongShuCrawler(),
                Platform.DOUYIN: DouyinCrawler(),
                Platform.BILIBILI: BilibiliCrawler(),
                Platform.WEIBO: WeiboCrawler(),
                Platform.ZHIHU: ZhihuCrawler(),
                Platform.TIEBA: TiebaCrawler(),
                Platform.EASTMONEY: EastMoneyCrawler(),
            }
        except ImportError as e:
            raise RuntimeError(
                f"Failed to import MediaCrawlerPro: {e}\n"
                f"Please ensure MediaCrawlerPro is installed at {self.mediacrawler_path}"
            )

    def get_supported_platforms(self) -> List[Platform]:
        """MediaCrawlerPro 支持的平台"""
        return list(self.crawlers.keys())

    def fetch_trending(self, platform: Platform, limit: int = 50):
        """MediaCrawlerPro 不直接支持热榜 (通过搜索实现)"""
        # 可以通过搜索热门关键词实现
        raise NotImplementedError("Use search_posts instead")

    def search_posts(
        self,
        platform: Platform,
        keyword: str,
        limit: int = 50,
        **kwargs
    ) -> List[Dict]:
        """搜索帖子"""
        if platform not in self.crawlers:
            raise ValueError(f"Platform {platform} not supported")

        crawler = self.crawlers[platform]

        # 调用 MediaCrawlerPro 的搜索接口
        results = crawler.search(
            keyword=keyword,
            max_count=limit,
            **kwargs
        )

        # 标准化数据格式
        return self._normalize_posts(results, platform)

    def fetch_comments(
        self,
        platform: Platform,
        post_id: str,
        limit: int = 100
    ) -> List[Dict]:
        """获取评论"""
        if platform not in self.crawlers:
            raise ValueError(f"Platform {platform} not supported")

        crawler = self.crawlers[platform]
        comments = crawler.get_comments(post_id, max_count=limit)

        return self._normalize_comments(comments, platform)

    def _normalize_posts(self, data: List, platform: Platform) -> List[Dict]:
        """标准化帖子数据"""
        # 具体实现...
        pass

    def _normalize_comments(self, data: List, platform: Platform) -> List[Dict]:
        """标准化评论数据"""
        # 具体实现...
        pass
```

### 5. 统一的爬虫管理器

```python
# trendradar/crawler/__init__.py

from typing import List, Dict, Optional
from .base import Platform, DataSourceType
from .adapters.newsnow import NewsNowAdapter
from .adapters.mediacrawler import MediaCrawlerAdapter


class CrawlerManager:
    """爬虫管理器 - 统一入口"""

    def __init__(
        self,
        enable_newsnow: bool = True,
        enable_mediacrawler: bool = True,
        mediacrawler_path: Optional[str] = None,
        proxy_url: Optional[str] = None
    ):
        """
        初始化爬虫管理器

        Args:
            enable_newsnow: 启用 NewsNow API
            enable_mediacrawler: 启用 MediaCrawlerPro
            mediacrawler_path: MediaCrawlerPro 路径
            proxy_url: 代理地址
        """
        self.adapters = {}

        if enable_newsnow:
            self.adapters['newsnow'] = NewsNowAdapter(proxy_url)

        if enable_mediacrawler:
            try:
                self.adapters['mediacrawler'] = MediaCrawlerAdapter(mediacrawler_path)
            except RuntimeError as e:
                print(f"Warning: MediaCrawlerPro not available: {e}")

    def get_trending(
        self,
        platform: Platform,
        limit: int = 50
    ) -> List[Dict]:
        """
        获取热榜数据 (优先使用 NewsNow)

        Args:
            platform: 平台
            limit: 数量限制
        """
        # 优先使用 NewsNow (快速)
        if 'newsnow' in self.adapters:
            adapter = self.adapters['newsnow']
            if platform in adapter.get_supported_platforms():
                return adapter.fetch_trending(platform, limit)

        raise ValueError(f"Trending not supported for {platform}")

    def search(
        self,
        platform: Platform,
        keyword: str,
        limit: int = 50,
        **kwargs
    ) -> List[Dict]:
        """
        搜索帖子 (使用 MediaCrawlerPro)

        Args:
            platform: 平台
            keyword: 关键词
            limit: 数量限制
        """
        if 'mediacrawler' not in self.adapters:
            raise RuntimeError("MediaCrawlerPro not available")

        adapter = self.adapters['mediacrawler']
        if platform not in adapter.get_supported_platforms():
            raise ValueError(f"Platform {platform} not supported by MediaCrawlerPro")

        return adapter.search_posts(platform, keyword, limit, **kwargs)

    def get_comments(
        self,
        platform: Platform,
        post_id: str,
        limit: int = 100
    ) -> List[Dict]:
        """获取评论 (使用 MediaCrawlerPro)"""
        if 'mediacrawler' not in self.adapters:
            raise RuntimeError("MediaCrawlerPro not available")

        return self.adapters['mediacrawler'].fetch_comments(platform, post_id, limit)


# 便捷函数
def create_crawler_manager(**kwargs) -> CrawlerManager:
    """创建爬虫管理器"""
    return CrawlerManager(**kwargs)
```

---

## 📝 使用示例

### 1. 获取热榜数据

```python
from trendradar.crawler import create_crawler_manager, Platform

# 创建管理器
crawler = create_crawler_manager()

# 获取知乎热榜
trending = crawler.get_trending(Platform.ZHIHU_HOT, limit=50)

for item in trending:
    print(f"{item['title']} - 热度: {item['hot_value']}")
```

### 2. 搜索股票讨论 (东方财富)

```python
# 搜索特斯拉相关讨论
posts = crawler.search(
    platform=Platform.EASTMONEY,
    keyword="特斯拉",
    limit=100
)

for post in posts:
    print(f"{post['author']}: {post['content'][:50]}...")
```

### 3. 获取帖子评论

```python
# 获取某个帖子的评论
comments = crawler.get_comments(
    platform=Platform.EASTMONEY,
    post_id="123456",
    limit=200
)

for comment in comments:
    print(f"{comment['author']}: {comment['content']}")
```

### 4. 在 TrendRadar Agent 中使用

```python
from trendradar.agent import BaseAgent
from trendradar.crawler import create_crawler_manager, Platform

class StockMonitorAgent(BaseAgent):
    """股票监控Agent"""

    def __init__(self):
        super().__init__()
        self.crawler = create_crawler_manager()

    def monitor_stock(self, stock_code: str):
        """监控股票讨论"""
        # 1. 搜索相关帖子
        posts = self.crawler.search(
            platform=Platform.EASTMONEY,
            keyword=stock_code,
            limit=50
        )

        # 2. 获取评论
        for post in posts[:5]:  # 只获取前5个帖子的评论
            comments = self.crawler.get_comments(
                platform=Platform.EASTMONEY,
                post_id=post['id'],
                limit=50
            )

            # 3. AI分析
            analysis = self.analyze_sentiment(posts, comments)

            # 4. 生成报告
            self.generate_report(stock_code, analysis)
```

---

## ✅ 优势

1. **统一接口**: 不管底层用什么爬虫，上层代码不变
2. **灵活切换**: 可以根据需求启用/禁用不同的数据源
3. **易于扩展**: 添加新的爬虫只需实现 `CrawlerAdapter`
4. **降低耦合**: MediaCrawlerPro 可用则用，不可用也不影响其他功能
5. **性能优化**: 热榜用快速的 API，深度分析用专业爬虫

---

## 🔧 配置管理

```yaml
# config/crawler_config.yaml

crawler:
  # NewsNow API 配置
  newsnow:
    enabled: true
    api_url: "https://newsnow.busiyi.world/api/s"
    proxy: null

  # MediaCrawlerPro 配置
  mediacrawler:
    enabled: true
    path: "/Users/wangxinlong/Code/communityspy/MediaCrawlerPro-Python"

    # 平台配置
    platforms:
      eastmoney:
        enabled: true
        max_retries: 3

      xiaohongshu:
        enabled: true
        account_pool: true  # 使用账号池
```

---

## 🎯 下一步行动

1. 实现 `CrawlerAdapter` 基类
2. 实现 `NewsNowAdapter`
3. 实现 `MediaCrawlerAdapter`
4. 实现 `CrawlerManager`
5. 编写单元测试
6. 集成到现有 Agent 系统

**是否开始实现？**
