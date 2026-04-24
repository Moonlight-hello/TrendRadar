# coding=utf-8
"""
爬虫系统类型定义

所有枚举类型和数据模型，确保类型安全
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta


# ============================================
# 枚举类型定义
# ============================================

class Platform(Enum):
    """
    支持的平台

    不要使用字符串，必须使用枚举值
    """
    # NewsNow API 支持
    ZHIHU = "zhihu"
    WEIBO = "weibo"
    BILIBILI = "bilibili"

    # MediaCrawlerPro 支持
    XIAOHONGSHU = "xhs"
    DOUYIN = "douyin"
    KUAISHOU = "kuaishou"
    TIEBA = "tieba"
    EASTMONEY = "eastmoney"

    def __str__(self) -> str:
        return self.value


class QueryType(Enum):
    """
    查询类型

    不要使用字符串，必须使用枚举值
    """
    SEARCH = auto()          # 搜索帖子
    TRENDING = auto()        # 热榜
    USER_POSTS = auto()      # 用户帖子
    COMMENTS = auto()        # 评论
    POST_DETAIL = auto()     # 帖子详情

    def __str__(self) -> str:
        return self.name.lower()


class TimeRange(Enum):
    """
    时间范围预设

    不要使用字符串，必须使用枚举值
    """
    LAST_HOUR = timedelta(hours=1)
    LAST_3H = timedelta(hours=3)
    LAST_6H = timedelta(hours=6)
    LAST_12H = timedelta(hours=12)
    LAST_24H = timedelta(hours=24)
    LAST_3D = timedelta(days=3)
    LAST_7D = timedelta(days=7)
    LAST_30D = timedelta(days=30)

    def get_time_range(self) -> tuple[datetime, datetime]:
        """获取实际的时间范围"""
        end_time = datetime.now()
        start_time = end_time - self.value
        return (start_time, end_time)

    def __str__(self) -> str:
        return self.name.lower()


class TaskStatus(Enum):
    """
    任务状态

    不要使用字符串，必须使用枚举值
    """
    PENDING = auto()      # 等待执行
    RUNNING = auto()      # 执行中
    COMPLETED = auto()    # 已完成
    FAILED = auto()       # 失败
    CANCELLED = auto()    # 已取消

    def __str__(self) -> str:
        return self.name.lower()


class CacheStrategy(Enum):
    """
    缓存策略

    不要使用字符串，必须使用枚举值
    """
    AUTO = auto()         # 自动决策（有缓存用缓存，无缓存则爬取）
    CACHE_ONLY = auto()   # 仅使用缓存（无缓存返回空）
    FORCE_REFRESH = auto() # 强制刷新（忽略缓存）
    NO_CACHE = auto()     # 不使用缓存（爬取但不保存）

    def __str__(self) -> str:
        return self.name.lower()


class SortOrder(Enum):
    """
    排序方式

    不要使用字符串，必须使用枚举值
    """
    TIME_DESC = auto()    # 时间倒序（最新在前）
    TIME_ASC = auto()     # 时间正序（最早在前）
    HOT_DESC = auto()     # 热度倒序
    HOT_ASC = auto()      # 热度正序

    def __str__(self) -> str:
        return self.name.lower()


# ============================================
# 数据模型定义
# ============================================

@dataclass(frozen=True)
class QueryParams:
    """
    查询参数（不可变）

    所有参数都使用枚举类型，确保类型安全
    """
    # 必需参数
    platform: Platform
    query_type: QueryType

    # 查询条件（根据 query_type 决定哪些必需）
    keyword: Optional[str] = None
    user_id: Optional[str] = None
    post_id: Optional[str] = None

    # 时间范围
    time_range: Optional[TimeRange] = TimeRange.LAST_24H
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    # 结果控制
    limit: int = 50
    offset: int = 0
    sort_order: SortOrder = SortOrder.TIME_DESC

    # 缓存控制
    cache_strategy: CacheStrategy = CacheStrategy.AUTO
    cache_ttl_seconds: int = 3600  # 1小时

    def __post_init__(self):
        """参数验证"""
        # 验证 query_type 对应的必需参数
        if self.query_type == QueryType.SEARCH and not self.keyword:
            raise ValueError("SEARCH requires keyword")
        if self.query_type == QueryType.USER_POSTS and not self.user_id:
            raise ValueError("USER_POSTS requires user_id")
        if self.query_type == QueryType.COMMENTS and not self.post_id:
            raise ValueError("COMMENTS requires post_id")
        if self.query_type == QueryType.POST_DETAIL and not self.post_id:
            raise ValueError("POST_DETAIL requires post_id")

        # 验证 limit
        if self.limit <= 0 or self.limit > 1000:
            raise ValueError("limit must be between 1 and 1000")

        # 验证 offset
        if self.offset < 0:
            raise ValueError("offset must be >= 0")

    def get_time_range_tuple(self) -> tuple[datetime, datetime]:
        """
        获取实际的时间范围

        优先级: start_time/end_time > time_range > 默认24小时
        """
        if self.start_time and self.end_time:
            return (self.start_time, self.end_time)

        if self.time_range:
            return self.time_range.get_time_range()

        # 默认最近24小时
        return TimeRange.LAST_24H.get_time_range()

    def to_cache_key(self) -> str:
        """
        生成缓存键

        格式: platform:query_type:keyword:time_bucket
        """
        parts = [
            str(self.platform),
            str(self.query_type),
            self.keyword or "",
            self.user_id or "",
            self.post_id or "",
        ]

        # 添加时间范围到键中（按小时分组）
        start_time, end_time = self.get_time_range_tuple()
        time_bucket = start_time.strftime("%Y%m%d%H")
        parts.append(time_bucket)

        return ":".join(parts)

    def should_use_cache(self) -> bool:
        """是否应该使用缓存"""
        return self.cache_strategy in (CacheStrategy.AUTO, CacheStrategy.CACHE_ONLY)

    def should_save_cache(self) -> bool:
        """是否应该保存缓存"""
        return self.cache_strategy in (CacheStrategy.AUTO, CacheStrategy.FORCE_REFRESH)


@dataclass
class CrawlItem:
    """
    爬取数据项（标准化格式）

    所有爬虫返回的数据都必须转换成这个格式
    """
    # 基础信息
    id: str                          # 唯一ID
    platform: Platform               # 平台
    content_type: QueryType          # 内容类型

    # 内容
    title: Optional[str] = None      # 标题
    content: Optional[str] = None    # 正文
    url: Optional[str] = None        # 链接

    # 作者信息
    author_id: Optional[str] = None
    author_name: Optional[str] = None

    # 时间
    publish_time: Optional[datetime] = None
    crawl_time: datetime = field(default_factory=datetime.now)

    # 统计数据
    like_count: int = 0
    comment_count: int = 0
    share_count: int = 0
    view_count: int = 0

    # 扩展数据
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "platform": str(self.platform),
            "content_type": str(self.content_type),
            "title": self.title,
            "content": self.content,
            "url": self.url,
            "author_id": self.author_id,
            "author_name": self.author_name,
            "publish_time": self.publish_time.isoformat() if self.publish_time else None,
            "crawl_time": self.crawl_time.isoformat(),
            "like_count": self.like_count,
            "comment_count": self.comment_count,
            "share_count": self.share_count,
            "view_count": self.view_count,
            "extra": self.extra,
        }


@dataclass
class QueryResult:
    """
    查询结果（不可变）

    Service Layer 返回给 Application Layer 的统一格式
    """
    # 状态
    success: bool
    from_cache: bool

    # 数据
    items: List[CrawlItem]

    # 元信息
    query_params: QueryParams
    query_time: datetime = field(default_factory=datetime.now)
    cache_time: Optional[datetime] = None

    # 异步信息
    is_async: bool = False
    task_id: Optional[str] = None
    task_status: Optional[TaskStatus] = None

    # 消息
    message: str = ""
    error: Optional[str] = None

    @property
    def count(self) -> int:
        """数据条数"""
        return len(self.items)

    @property
    def is_empty(self) -> bool:
        """是否为空结果"""
        return self.count == 0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "from_cache": self.from_cache,
            "count": self.count,
            "items": [item.to_dict() for item in self.items],
            "query_time": self.query_time.isoformat(),
            "cache_time": self.cache_time.isoformat() if self.cache_time else None,
            "is_async": self.is_async,
            "task_id": self.task_id,
            "task_status": str(self.task_status) if self.task_status else None,
            "message": self.message,
            "error": self.error,
        }


@dataclass
class CrawlTask:
    """
    爬取任务

    Infrastructure Layer 使用
    """
    id: str
    query_params: QueryParams
    status: TaskStatus = TaskStatus.PENDING

    # 时间
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # 结果
    items: List[CrawlItem] = field(default_factory=list)
    error: Optional[str] = None

    # 执行信息
    adapter_name: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3

    def can_retry(self) -> bool:
        """是否可以重试"""
        return self.retry_count < self.max_retries

    def mark_running(self):
        """标记为运行中"""
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.now()

    def mark_completed(self, items: List[CrawlItem]):
        """标记为完成"""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now()
        self.items = items

    def mark_failed(self, error: str):
        """标记为失败"""
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.now()
        self.error = error
        self.retry_count += 1


# ============================================
# 类型别名
# ============================================

CacheKey = str
TaskId = str
