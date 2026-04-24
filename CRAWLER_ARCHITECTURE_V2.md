# 爬虫架构设计 V2 - 智能查询与缓存

> 日期: 2026-04-24 | 版本: 2.0

---

## 🎯 核心需求

### 1. 同步查询（读缓存）
- 优先从数据库缓存读取
- 如果有缓存且未过期 → 立即返回
- 支持多样化的查询条件

### 2. 异步查询（触发爬取）
- 如果缓存没有或已过期 → 触发爬取
- 返回任务ID，后台执行
- 完成后写入缓存

### 3. 查询原语生成
- 用户用自然语言描述需求："最近24小时特斯拉的评论"
- Adapter Layer 翻译成具体的查询条件
- 支持复杂查询场景

---

## 🏗️ 三层架构设计（改进版）

```
┌─────────────────────────────────────────────────────────────┐
│              Application Layer (业务层)                      │
│         Agent / API / CLI                                    │
│                                                              │
│  示例查询:                                                    │
│  "获取最近24小时特斯拉在东方财富的讨论"                        │
│  "查询最近7天小红书上关于iPhone的帖子"                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│          Service Layer (服务层 - 智能决策)                   │
│                                                              │
│  ┌───────────────────────────────────────────────┐         │
│  │         CrawlerService                         │         │
│  │                                                │         │
│  │  fetch(query_params) -> Result                 │         │
│  │  ├─ 解析查询参数                               │         │
│  │  ├─ 检查缓存是否可用                           │         │
│  │  ├─ 如果有缓存 → 返回 (同步)                   │         │
│  │  └─ 如果无缓存 → 触发爬取 + 返回TaskID (异步)   │         │
│  └───────────────────────────────────────────────┘         │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│        Adapter Layer (适配层 - 查询原语生成)                 │
│                                                              │
│  ┌────────────────────┐        ┌────────────────────┐      │
│  │ NewsNowAdapter     │        │MediaCrawlerAdapter │      │
│  │                    │        │                    │      │
│  │ build_query()      │        │ build_query()      │      │
│  │ ├─ 生成查询条件     │        │ ├─ 生成查询条件     │      │
│  │ ├─ 查询缓存         │        │ ├─ 查询缓存         │      │
│  │ └─ 触发爬取         │        │ └─ 触发爬取         │      │
│  └────────────────────┘        └────────────────────┘      │
│                                                              │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│      Infrastructure Layer (基础设施层 - 数据访问)            │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │DataRepository│  │ CrawlExecutor│  │ TaskManager  │     │
│  │(数据仓库)     │  │ (爬取执行器)  │  │ (任务管理)    │     │
│  │              │  │              │  │              │     │
│  │query()       │  │execute()     │  │submit()      │     │
│  │insert()      │  │              │  │get_status()  │     │
│  │update()      │  │              │  │              │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
│  ┌──────────────────────────────────────────────┐          │
│  │          Database (SQLite/PostgreSQL)        │          │
│  │                                              │          │
│  │  Tables:                                     │          │
│  │  - crawl_cache (爬取缓存)                     │          │
│  │  - crawl_tasks (爬取任务)                     │          │
│  │  - crawl_results (爬取结果)                   │          │
│  └──────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 数据模型设计

### 1. 查询参数模型

```python
from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime, timedelta
from enum import Enum

class Platform(Enum):
    """支持的平台"""
    ZHIHU = "zhihu"
    WEIBO = "weibo"
    EASTMONEY = "eastmoney"
    XIAOHONGSHU = "xhs"

class TimeRange(Enum):
    """时间范围预设"""
    LAST_HOUR = "last_hour"
    LAST_24H = "last_24h"
    LAST_7D = "last_7d"
    LAST_30D = "last_30d"

@dataclass
class QueryParams:
    """
    统一的查询参数

    支持多种查询方式：
    1. 平台 + 关键词 + 时间范围
    2. 平台 + 用户 + 时间范围
    3. 平台 + 热榜
    """
    # 基础参数
    platform: Platform
    query_type: str  # "search", "trending", "user_posts", "comments"

    # 搜索参数
    keyword: Optional[str] = None
    user_id: Optional[str] = None
    post_id: Optional[str] = None

    # 时间范围（两种方式）
    time_range: Optional[TimeRange] = None  # 预设范围
    start_time: Optional[datetime] = None   # 自定义起始时间
    end_time: Optional[datetime] = None     # 自定义结束时间

    # 结果限制
    limit: int = 50

    # 缓存控制
    use_cache: bool = True      # 是否使用缓存
    cache_ttl: int = 3600       # 缓存有效期（秒）
    force_refresh: bool = False # 强制刷新（忽略缓存）

    def get_time_range_tuple(self) -> tuple[datetime, datetime]:
        """获取实际的时间范围"""
        if self.start_time and self.end_time:
            return (self.start_time, self.end_time)

        if self.time_range:
            end = datetime.now()
            if self.time_range == TimeRange.LAST_HOUR:
                start = end - timedelta(hours=1)
            elif self.time_range == TimeRange.LAST_24H:
                start = end - timedelta(hours=24)
            elif self.time_range == TimeRange.LAST_7D:
                start = end - timedelta(days=7)
            elif self.time_range == TimeRange.LAST_30D:
                start = end - timedelta(days=30)
            return (start, end)

        # 默认最近24小时
        end = datetime.now()
        start = end - timedelta(hours=24)
        return (start, end)

    def to_cache_key(self) -> str:
        """生成缓存键"""
        parts = [
            self.platform.value,
            self.query_type,
            self.keyword or "",
            self.user_id or "",
            self.post_id or "",
        ]
        # 添加时间范围到键中（按小时分组）
        start, end = self.get_time_range_tuple()
        parts.append(start.strftime("%Y%m%d%H"))
        return ":".join(parts)
```

### 2. 查询结果模型

```python
@dataclass
class QueryResult:
    """查询结果"""
    # 状态
    success: bool
    from_cache: bool  # 是否来自缓存

    # 数据
    data: List[dict]
    count: int

    # 元信息
    query_params: QueryParams
    query_time: datetime
    cache_time: Optional[datetime] = None  # 缓存时间

    # 异步信息（如果是异步查询）
    is_async: bool = False
    task_id: Optional[str] = None

    # 消息
    message: str = ""
```

---

## 💾 Infrastructure Layer 设计

### 1. DataRepository（数据仓库）

```python
from typing import List, Optional, Dict
from datetime import datetime
import sqlite3
import json

class DataRepository:
    """
    数据仓库 - 统一的数据访问接口

    职责：
    1. 查询缓存数据
    2. 保存爬取结果
    3. 管理缓存过期
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 爬取缓存表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS crawl_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cache_key TEXT UNIQUE NOT NULL,
                platform TEXT NOT NULL,
                query_type TEXT NOT NULL,
                keyword TEXT,

                -- 时间信息
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,

                -- 数据
                data TEXT NOT NULL,  -- JSON
                count INTEGER NOT NULL,

                -- 索引
                INDEX idx_cache_key (cache_key),
                INDEX idx_platform (platform),
                INDEX idx_expires (expires_at)
            )
        """)

        # 爬取任务表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS crawl_tasks (
                id TEXT PRIMARY KEY,
                platform TEXT NOT NULL,
                query_params TEXT NOT NULL,  -- JSON
                status TEXT NOT NULL,  -- pending/running/completed/failed

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,

                result TEXT,  -- JSON
                error TEXT,

                INDEX idx_status (status),
                INDEX idx_created (created_at)
            )
        """)

        conn.commit()
        conn.close()

    def query_cache(
        self,
        query_params: QueryParams
    ) -> Optional[List[Dict]]:
        """
        查询缓存

        Returns:
            如果缓存存在且有效，返回数据；否则返回 None
        """
        if not query_params.use_cache or query_params.force_refresh:
            return None

        cache_key = query_params.to_cache_key()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT data, created_at, expires_at
            FROM crawl_cache
            WHERE cache_key = ?
              AND expires_at > datetime('now')
        """, (cache_key,))

        row = cursor.fetchone()
        conn.close()

        if row:
            data_json, created_at, expires_at = row
            data = json.loads(data_json)

            # 检查时间范围是否匹配
            # TODO: 更精确的时间范围匹配

            return data

        return None

    def save_cache(
        self,
        query_params: QueryParams,
        data: List[Dict]
    ) -> bool:
        """保存到缓存"""
        cache_key = query_params.to_cache_key()
        start_time, end_time = query_params.get_time_range_tuple()
        expires_at = datetime.now() + timedelta(seconds=query_params.cache_ttl)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO crawl_cache (
                cache_key, platform, query_type, keyword,
                start_time, end_time, expires_at,
                data, count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            cache_key,
            query_params.platform.value,
            query_params.query_type,
            query_params.keyword,
            start_time,
            end_time,
            expires_at,
            json.dumps(data, ensure_ascii=False),
            len(data)
        ))

        conn.commit()
        conn.close()
        return True

    def clean_expired_cache(self):
        """清理过期缓存"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM crawl_cache
            WHERE expires_at < datetime('now')
        """)

        deleted = cursor.rowcount
        conn.commit()
        conn.close()

        return deleted
```

### 2. CrawlExecutor（爬取执行器）

```python
class CrawlExecutor:
    """
    爬取执行器

    职责：
    1. 执行实际的网络爬取
    2. 调用具体的爬虫适配器
    """

    def __init__(self):
        self.adapters: Dict[Platform, 'CrawlerAdapter'] = {}

    def register_adapter(self, platform: Platform, adapter: 'CrawlerAdapter'):
        """注册适配器"""
        self.adapters[platform] = adapter

    def execute(self, query_params: QueryParams) -> List[Dict]:
        """
        执行爬取

        Returns:
            爬取的数据列表
        """
        if query_params.platform not in self.adapters:
            raise ValueError(f"Platform {query_params.platform} not supported")

        adapter = self.adapters[query_params.platform]

        # 调用适配器的爬取方法
        if query_params.query_type == "search":
            return adapter.search_posts(query_params)
        elif query_params.query_type == "trending":
            return adapter.fetch_trending(query_params)
        elif query_params.query_type == "comments":
            return adapter.fetch_comments(query_params)
        else:
            raise ValueError(f"Unknown query type: {query_params.query_type}")
```

---

## 🔌 Adapter Layer 设计（查询原语生成）

```python
from abc import ABC, abstractmethod

class CrawlerAdapter(ABC):
    """
    爬虫适配器基类

    职责：
    1. 将 QueryParams 翻译成具体的爬取命令
    2. 决定是查询缓存还是触发爬取
    3. 执行爬取并返回标准化数据
    """

    def __init__(
        self,
        data_repo: DataRepository,
        crawl_executor: CrawlExecutor
    ):
        self.data_repo = data_repo
        self.crawl_executor = crawl_executor

    @abstractmethod
    def get_name(self) -> str:
        """适配器名称"""
        pass

    @abstractmethod
    def get_supported_platforms(self) -> List[Platform]:
        """支持的平台"""
        pass

    def build_query(
        self,
        query_params: QueryParams
    ) -> QueryResult:
        """
        构建查询（核心方法）

        流程：
        1. 检查缓存
        2. 如果有缓存且有效 → 返回缓存数据（同步）
        3. 如果无缓存 → 触发爬取（异步）
        """
        # 1. 尝试从缓存读取
        cached_data = self.data_repo.query_cache(query_params)

        if cached_data is not None:
            # 缓存命中
            return QueryResult(
                success=True,
                from_cache=True,
                data=cached_data,
                count=len(cached_data),
                query_params=query_params,
                query_time=datetime.now(),
                message="Data from cache"
            )

        # 2. 缓存未命中，需要爬取
        if self.is_async_adapter():
            # 异步适配器：提交任务
            task_id = self._submit_crawl_task(query_params)

            return QueryResult(
                success=True,
                from_cache=False,
                data=[],
                count=0,
                query_params=query_params,
                query_time=datetime.now(),
                is_async=True,
                task_id=task_id,
                message="Crawl task submitted"
            )
        else:
            # 同步适配器：立即爬取
            data = self._execute_crawl(query_params)

            # 保存到缓存
            self.data_repo.save_cache(query_params, data)

            return QueryResult(
                success=True,
                from_cache=False,
                data=data,
                count=len(data),
                query_params=query_params,
                query_time=datetime.now(),
                message="Data crawled successfully"
            )

    @abstractmethod
    def is_async_adapter(self) -> bool:
        """是否为异步适配器"""
        pass

    @abstractmethod
    def search_posts(self, query_params: QueryParams) -> List[Dict]:
        """搜索帖子"""
        pass

    @abstractmethod
    def fetch_trending(self, query_params: QueryParams) -> List[Dict]:
        """获取热榜"""
        pass

    @abstractmethod
    def fetch_comments(self, query_params: QueryParams) -> List[Dict]:
        """获取评论"""
        pass


# ===== 具体实现 =====

class NewsNowAdapter(CrawlerAdapter):
    """NewsNow 适配器（同步）"""

    def get_name(self) -> str:
        return "NewsNow"

    def get_supported_platforms(self) -> List[Platform]:
        return [Platform.ZHIHU, Platform.WEIBO]

    def is_async_adapter(self) -> bool:
        return False  # 同步

    def fetch_trending(self, query_params: QueryParams) -> List[Dict]:
        """获取热榜"""
        from trendradar.crawler import DataFetcher

        fetcher = DataFetcher()
        response, _, _ = fetcher.fetch_data(query_params.platform.value)

        if not response:
            return []

        # 解析和标准化
        data = json.loads(response)
        items = data.get("data", [])

        # 标准化格式
        return self._normalize_data(items, query_params)

    def search_posts(self, query_params: QueryParams) -> List[Dict]:
        """NewsNow 不支持搜索"""
        raise NotImplementedError("NewsNow does not support search")

    def _normalize_data(self, items: List, query_params: QueryParams) -> List[Dict]:
        """标准化数据格式"""
        result = []
        for item in items[:query_params.limit]:
            result.append({
                "id": item.get("id"),
                "title": item.get("title"),
                "url": item.get("url"),
                "hot_value": item.get("hot"),
                "platform": query_params.platform.value,
                "created_at": datetime.now().isoformat(),
            })
        return result


class MediaCrawlerAdapter(CrawlerAdapter):
    """MediaCrawler 适配器（异步）"""

    def __init__(
        self,
        data_repo: DataRepository,
        crawl_executor: CrawlExecutor,
        mediacrawler_path: str = None
    ):
        super().__init__(data_repo, crawl_executor)
        self.mediacrawler_path = mediacrawler_path or \
            "/Users/wangxinlong/Code/communityspy/MediaCrawlerPro-Python"

    def get_name(self) -> str:
        return "MediaCrawlerPro"

    def get_supported_platforms(self) -> List[Platform]:
        return [Platform.EASTMONEY, Platform.XIAOHONGSHU]

    def is_async_adapter(self) -> bool:
        return True  # 异步

    def search_posts(self, query_params: QueryParams) -> List[Dict]:
        """
        搜索帖子（异步执行）

        这里只是提交任务，不等待结果
        """
        # 实际的爬取会在后台执行
        # 这里返回空列表，真实数据会通过回调写入数据库
        return []

    def _submit_crawl_task(self, query_params: QueryParams) -> str:
        """提交爬取任务"""
        import subprocess
        import uuid

        task_id = str(uuid.uuid4())

        # 构建命令
        cmd = [
            "python3", f"{self.mediacrawler_path}/main.py",
            "--platform", query_params.platform.value,
            "--type", "search",
            "--keywords", query_params.keyword,
            "--max-count", str(query_params.limit),
            "--task-id", task_id,
        ]

        # 后台执行
        subprocess.Popen(
            cmd,
            cwd=self.mediacrawler_path,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        return task_id
```

---

## 🎯 Service Layer 设计（智能决策）

```python
class CrawlerService:
    """
    爬虫服务（外观模式）

    提供简单易用的查询接口
    """

    def __init__(
        self,
        db_path: str = "./data/crawler.db"
    ):
        # 初始化基础设施层
        self.data_repo = DataRepository(db_path)
        self.crawl_executor = CrawlExecutor()
        self.task_manager = TaskManager(db_path)

        # 初始化适配器
        self.adapters: Dict[Platform, CrawlerAdapter] = {}
        self._init_adapters()

    def _init_adapters(self):
        """初始化所有适配器"""
        # NewsNow
        newsnow = NewsNowAdapter(self.data_repo, self.crawl_executor)
        for platform in newsnow.get_supported_platforms():
            self.adapters[platform] = newsnow

        # MediaCrawler
        mediacrawler = MediaCrawlerAdapter(self.data_repo, self.crawl_executor)
        for platform in mediacrawler.get_supported_platforms():
            self.adapters[platform] = mediacrawler

    # ========== 简化的查询接口 ==========

    def fetch(
        self,
        platform: str,
        keyword: str = None,
        time_range: str = "last_24h",
        limit: int = 50,
        use_cache: bool = True,
        force_refresh: bool = False
    ) -> QueryResult:
        """
        统一的查询接口

        Examples:
            # 搜索（优先使用缓存）
            result = service.fetch(
                platform="eastmoney",
                keyword="特斯拉",
                time_range="last_24h"
            )

            # 热榜（强制刷新）
            result = service.fetch(
                platform="zhihu",
                force_refresh=True
            )
        """
        # 构建查询参数
        query_params = QueryParams(
            platform=Platform(platform),
            query_type="search" if keyword else "trending",
            keyword=keyword,
            time_range=TimeRange(time_range),
            limit=limit,
            use_cache=use_cache,
            force_refresh=force_refresh
        )

        # 获取适配器
        if query_params.platform not in self.adapters:
            raise ValueError(f"Platform {platform} not supported")

        adapter = self.adapters[query_params.platform]

        # 执行查询（适配器会自动决定是读缓存还是爬取）
        return adapter.build_query(query_params)

    def get_task_status(self, task_id: str) -> Dict:
        """查询任务状态"""
        return self.task_manager.get_status(task_id)
```

---

## 📝 使用示例

### 场景1：查询股票评论（智能缓存）

```python
from trendradar.crawler import CrawlerService

service = CrawlerService()

# 第一次查询 - 触发爬取
result = service.fetch(
    platform="eastmoney",
    keyword="特斯拉",
    time_range="last_24h",
    limit=100
)

if result.is_async:
    print(f"任务已提交: {result.task_id}")
    # 等待完成...
else:
    print(f"获取 {result.count} 条数据")

# 第二次查询 - 从缓存读取（秒级响应）
result2 = service.fetch(
    platform="eastmoney",
    keyword="特斯拉",
    time_range="last_24h"
)

print(f"来自缓存: {result2.from_cache}")  # True
```

### 场景2：强制刷新

```python
# 忽略缓存，强制重新爬取
result = service.fetch(
    platform="eastmoney",
    keyword="特斯拉",
    force_refresh=True  # 关键参数
)
```

### 场景3：在 Agent 中使用

```python
from trendradar.agent import BaseAgent
from trendradar.crawler import CrawlerService

class StockAnalysisAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.crawler = CrawlerService()

    def analyze_stock(self, stock_code: str):
        """分析股票"""

        # 查询最近讨论（自动使用缓存）
        result = self.crawler.fetch(
            platform="eastmoney",
            keyword=stock_code,
            time_range="last_24h"
        )

        if result.from_cache:
            print(f"使用缓存数据（{result.count}条）")
        elif result.is_async:
            print(f"后台爬取中: {result.task_id}")
            # 等待或注册回调
            return
        else:
            print(f"实时爬取完成（{result.count}条）")

        # AI分析
        analysis = self.ai_analyze(result.data)
        return analysis
```

---

## ✅ 设计优势

1. **智能缓存决策**
   - 有缓存 → 立即返回（毫秒级）
   - 无缓存 → 触发爬取（分钟级）
   - 用户无需关心底层逻辑

2. **统一查询接口**
   - 所有平台使用相同的 `fetch()` 方法
   - 参数语义化（time_range="last_24h"）
   - 支持灵活的查询条件

3. **查询原语生成**
   - Adapter Layer 负责翻译查询条件
   - 支持多样化的语言描述
   - 易于扩展新的查询类型

4. **同步/异步透明**
   - Service Layer 自动处理
   - 返回值统一（QueryResult）
   - 支持强制模式选择

---

**这个设计符合您的要求吗？** 🎯
