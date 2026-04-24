# 爬虫系统实现文档

> 日期: 2026-04-24 | 版本: 6.1.0

---

## ✅ 实现完成总结

基于 `CRAWLER_ARCHITECTURE_V2.md` 设计，已完成爬虫系统的核心实现。

### 核心特性

1. **严格类型安全** - 所有参数使用枚举值，无字符串硬编码
2. **三层架构** - Infrastructure → Adapter → Service
3. **智能缓存** - 自动决策读缓存或触发爬取
4. **同步+异步** - 支持两种查询模式
5. **统一接口** - 简单、稳定、准确的调用方式

---

## 📁 已实现的文件

```
trendradar/crawler/
├── types.py                    # ✅ 类型定义（枚举 + 数据模型）
├── repository.py               # ✅ Infrastructure: 数据仓库
├── executor.py                 # ✅ Infrastructure: 爬虫执行器
├── task_manager.py             # ✅ Infrastructure: 任务管理器
├── service.py                  # ✅ Service Layer: 爬虫服务
├── adapters/
│   ├── __init__.py            # ✅ Adapter 导出
│   └── newsnow.py             # ✅ NewsNow API 适配器
├── fetcher.py                  # ⚪ 原有的 DataFetcher（保留兼容）
└── __init__.py                 # ✅ 统一导出
```

---

## 🎯 类型系统

### 1. 枚举类型

所有参数都使用枚举值，确保类型安全：

```python
from trendradar.crawler import (
    Platform,       # 平台枚举
    QueryType,      # 查询类型枚举
    TimeRange,      # 时间范围枚举
    CacheStrategy,  # 缓存策略枚举
    TaskStatus,     # 任务状态枚举
    SortOrder,      # 排序方式枚举
)

# 使用示例
Platform.ZHIHU          # 知乎
Platform.WEIBO          # 微博
Platform.BILIBILI       # B站
Platform.XIAOHONGSHU    # 小红书
Platform.DOUYIN         # 抖音

QueryType.TRENDING      # 热榜
QueryType.SEARCH        # 搜索
QueryType.USER_POSTS    # 用户帖子
QueryType.COMMENTS      # 评论

TimeRange.LAST_HOUR     # 最近1小时
TimeRange.LAST_24H      # 最近24小时
TimeRange.LAST_7D       # 最近7天

CacheStrategy.AUTO           # 自动（有缓存用缓存，无缓存则爬取）
CacheStrategy.CACHE_ONLY     # 仅缓存
CacheStrategy.FORCE_REFRESH  # 强制刷新
CacheStrategy.NO_CACHE       # 不使用缓存
```

### 2. 数据模型

```python
from trendradar.crawler import QueryParams, CrawlItem, QueryResult

# 查询参数（不可变）
params = QueryParams(
    platform=Platform.ZHIHU,           # 必需：平台
    query_type=QueryType.TRENDING,     # 必需：查询类型
    limit=50,                          # 可选：数量限制
    time_range=TimeRange.LAST_24H,     # 可选：时间范围
    cache_strategy=CacheStrategy.AUTO, # 可选：缓存策略
    cache_ttl_seconds=3600,            # 可选：缓存过期时间
)

# 爬取数据项（标准化格式）
item = CrawlItem(
    id="zhihu_trending_1_abc123",
    platform=Platform.ZHIHU,
    content_type=QueryType.TRENDING,
    title="标题",
    content="正文",
    url="https://...",
    author_name="作者",
    publish_time=datetime.now(),
    like_count=100,
    # ... 更多字段
)

# 查询结果（统一格式）
result = QueryResult(
    success=True,
    from_cache=False,
    items=[item1, item2, ...],
    query_params=params,
    message="Crawled 50 items",
)
```

---

## 🚀 使用方式

### 1. 初始化服务

```python
from trendradar.crawler import (
    CrawlerService,
    DataRepository,
    CrawlExecutor,
    TaskManager,
    NewsNowAdapter,
)

# 1. 创建数据仓库
repository = DataRepository(db_path="./data/crawler.db")

# 2. 创建爬虫执行器
executor = CrawlExecutor()

# 3. 注册适配器
newsnow_adapter = NewsNowAdapter()
executor.register_adapter(newsnow_adapter)

# 4. 创建任务管理器
task_manager = TaskManager(
    repository=repository,
    executor=executor,
    max_workers=5
)

# 5. 创建爬虫服务
service = CrawlerService(
    repository=repository,
    executor=executor,
    task_manager=task_manager
)
```

### 2. 同步查询（阻塞）

```python
from trendradar.crawler import QueryParams, Platform, QueryType, TimeRange

# 构造查询参数
params = QueryParams(
    platform=Platform.ZHIHU,
    query_type=QueryType.TRENDING,
    limit=50,
    time_range=TimeRange.LAST_24H,
)

# 执行查询（自动缓存策略）
result = service.query(params)

if result.success:
    print(f"获取到 {result.count} 条数据")
    print(f"来源: {'缓存' if result.from_cache else '实时爬取'}")

    for item in result.items:
        print(f"{item.extra['rank']}. {item.title}")
else:
    print(f"查询失败: {result.error}")
```

### 3. 异步查询（非阻塞）

```python
# 提交异步任务
result = service.query_async(params)

if result.is_async:
    print(f"任务已提交: {result.task_id}")
    print(f"任务状态: {result.task_status}")

    # 方式1: 等待任务完成（阻塞）
    final_result = service.wait_for_task(result.task_id, timeout=30)

    # 方式2: 轮询任务状态（非阻塞）
    while True:
        status_result = service.get_task_result(result.task_id)
        if status_result.task_status == TaskStatus.COMPLETED:
            print(f"任务完成，获取到 {status_result.count} 条数据")
            break
        elif status_result.task_status == TaskStatus.FAILED:
            print(f"任务失败: {status_result.error}")
            break
        time.sleep(1)
else:
    # 缓存命中，直接返回数据
    print(f"缓存命中，获取到 {result.count} 条数据")
```

### 4. 带回调的异步查询

```python
def on_task_complete(task):
    """任务完成回调"""
    if task.status == TaskStatus.COMPLETED:
        print(f"爬取完成，获取到 {len(task.items)} 条数据")
        # 可以在这里发送通知、更新UI等
    else:
        print(f"爬取失败: {task.error}")

# 提交任务并注册回调
result = service.query_async(params, callback=on_task_complete)
```

### 5. 不同缓存策略

```python
# 策略1: 仅使用缓存（无缓存返回空）
params = QueryParams(
    platform=Platform.WEIBO,
    query_type=QueryType.TRENDING,
    cache_strategy=CacheStrategy.CACHE_ONLY,
)
result = service.query(params)

# 策略2: 强制刷新（忽略缓存）
params = QueryParams(
    platform=Platform.WEIBO,
    query_type=QueryType.TRENDING,
    cache_strategy=CacheStrategy.FORCE_REFRESH,
)
result = service.query(params)

# 策略3: 不使用缓存（爬取但不保存）
params = QueryParams(
    platform=Platform.WEIBO,
    query_type=QueryType.TRENDING,
    cache_strategy=CacheStrategy.NO_CACHE,
)
result = service.query(params)
```

---

## 🔄 数据流程

### 同步查询流程

```
用户调用 service.query(params)
    ↓
1. 检查缓存策略
    ↓
2. 尝试从 Repository 读取缓存
    ↓ (缓存命中)
返回缓存数据 ✓
    ↓ (缓存未命中)
3. Executor 选择适配器
    ↓
4. Adapter 执行爬取
    ↓
5. 保存到 Repository 缓存
    ↓
返回爬取数据 ✓
```

### 异步查询流程

```
用户调用 service.query_async(params)
    ↓
1. 检查缓存策略
    ↓
2. 尝试从 Repository 读取缓存
    ↓ (缓存命中)
立即返回缓存数据 ✓
    ↓ (缓存未命中)
3. TaskManager 创建任务
    ↓
4. 立即返回 task_id ✓
    ↓
[后台执行]
5. Executor 执行爬取
    ↓
6. 保存到 Repository
    ↓
7. 触发回调通知
```

---

## 📊 支持的平台

### 已实现

| 平台 | 枚举值 | 适配器 | 查询类型 |
|-----|-------|--------|---------|
| 知乎 | `Platform.ZHIHU` | NewsNowAdapter | TRENDING |
| 微博 | `Platform.WEIBO` | NewsNowAdapter | TRENDING |
| B站 | `Platform.BILIBILI` | NewsNowAdapter | TRENDING |

### 待实现（MediaCrawlerPro）

| 平台 | 枚举值 | 适配器 | 查询类型 |
|-----|-------|--------|---------|
| 小红书 | `Platform.XIAOHONGSHU` | MediaCrawlerAdapter | SEARCH, USER_POSTS |
| 抖音 | `Platform.DOUYIN` | MediaCrawlerAdapter | SEARCH, USER_POSTS |
| 快手 | `Platform.KUAISHOU` | MediaCrawlerAdapter | SEARCH |
| 贴吧 | `Platform.TIEBA` | MediaCrawlerAdapter | SEARCH |
| 东方财富 | `Platform.EASTMONEY` | MediaCrawlerAdapter | SEARCH, COMMENTS |

---

## 🎨 设计原则

### 1. 类型安全

- ✅ 所有参数使用枚举值
- ✅ 无字符串硬编码
- ✅ `QueryParams` 为不可变对象
- ✅ 完整的参数验证

### 2. 接口稳定

```python
# ✅ 好的设计 - 使用枚举
params = QueryParams(
    platform=Platform.ZHIHU,
    query_type=QueryType.TRENDING,
)

# ❌ 坏的设计 - 使用字符串
params = QueryParams(
    platform="zhihu",      # 容易拼写错误
    query_type="trending", # 没有类型检查
)
```

### 3. 调用简单

```python
# 只需3步
service = create_crawler_service()           # 初始化
params = QueryParams(...)                    # 构造参数
result = service.query(params)               # 执行查询
```

### 4. 智能决策

```python
# Service Layer 自动决策：
# - 有缓存 → 返回缓存
# - 无缓存 → 触发爬取
# - 异步模式 → 立即返回 task_id

result = service.query(params)  # 自动处理
```

---

## 🧪 测试示例

### 基础测试

```python
# tests/test_crawler_basic.py

def test_zhihu_trending():
    """测试知乎热榜"""
    service = create_crawler_service()

    params = QueryParams(
        platform=Platform.ZHIHU,
        query_type=QueryType.TRENDING,
        limit=10,
    )

    result = service.query(params)

    assert result.success
    assert len(result.items) <= 10
    assert all(item.platform == Platform.ZHIHU for item in result.items)
    assert all(item.content_type == QueryType.TRENDING for item in result.items)
```

### 缓存测试

```python
def test_cache_hit():
    """测试缓存命中"""
    service = create_crawler_service()

    params = QueryParams(
        platform=Platform.WEIBO,
        query_type=QueryType.TRENDING,
    )

    # 第一次查询（爬取）
    result1 = service.query(params)
    assert not result1.from_cache

    # 第二次查询（缓存）
    result2 = service.query(params)
    assert result2.from_cache
    assert result2.count == result1.count
```

### 异步测试

```python
def test_async_query():
    """测试异步查询"""
    service = create_crawler_service()

    params = QueryParams(
        platform=Platform.BILIBILI,
        query_type=QueryType.TRENDING,
        cache_strategy=CacheStrategy.FORCE_REFRESH,  # 强制刷新确保异步
    )

    # 提交异步任务
    result = service.query_async(params)
    assert result.is_async
    assert result.task_id

    # 等待完成
    final_result = service.wait_for_task(result.task_id, timeout=30)
    assert final_result.success
    assert final_result.count > 0
```

---

## 🔧 工具函数

### 创建服务的辅助函数

```python
# trendradar/crawler/utils.py (待创建)

def create_crawler_service(
    db_path: str = "./data/crawler.db",
    max_workers: int = 5,
    proxy_url: Optional[str] = None,
) -> CrawlerService:
    """
    创建爬虫服务（便捷工厂函数）

    Args:
        db_path: 数据库路径
        max_workers: 最大并发数
        proxy_url: 代理URL

    Returns:
        配置好的爬虫服务
    """
    repository = DataRepository(db_path)
    executor = CrawlExecutor()

    # 注册所有适配器
    executor.register_adapter(NewsNowAdapter(proxy_url=proxy_url))
    # executor.register_adapter(MediaCrawlerAdapter())  # TODO

    task_manager = TaskManager(repository, executor, max_workers)

    return CrawlerService(repository, executor, task_manager)
```

---

## 📈 下一步计划

### 1. MediaCrawlerPro 集成 (优先级: 高)

```python
# trendradar/crawler/adapters/mediacrawler.py
class MediaCrawlerAdapter(BaseCrawlerAdapter):
    """
    MediaCrawlerPro 适配器

    支持平台: 小红书、抖音、快手、贴吧、东方财富
    支持查询: SEARCH, USER_POSTS, COMMENTS
    """
    SUPPORTED_PLATFORMS = [
        Platform.XIAOHONGSHU,
        Platform.DOUYIN,
        Platform.KUAISHOU,
        Platform.TIEBA,
        Platform.EASTMONEY,
    ]
```

### 2. 查询指令生成 (优先级: 中)

```python
# 为 Agent 提供自然语言查询指令
adapter = executor.get_adapter(params)
instructions = adapter.get_query_instructions(params)
# "获取知乎热榜数据，时间范围：最近24小时，数量限制：50条"
```

### 3. SKILL/MCP 封装 (优先级: 中)

```python
# mcp_server/crawler_skill.py
@skill("crawler")
async def crawl_skill(query: str) -> QueryResult:
    """
    爬虫技能接口

    Agent 可以通过自然语言调用
    """
    # 解析 query → QueryParams
    # 调用 service.query()
    # 返回结果
```

### 4. 统计和监控 (优先级: 低)

```python
# 添加统计功能
stats = service.get_stats()
# {
#     "cache": {"total": 100, "valid": 80, "expired": 20},
#     "tasks": {"pending": 5, "running": 2, "completed": 93}
# }
```

---

## ✅ 实现检查清单

- [x] 类型定义 (`types.py`)
- [x] 数据仓库 (`repository.py`)
- [x] 爬虫执行器 (`executor.py`)
- [x] 任务管理器 (`task_manager.py`)
- [x] NewsNow 适配器 (`adapters/newsnow.py`)
- [x] 爬虫服务 (`service.py`)
- [x] 统一导出 (`__init__.py`)
- [x] 使用文档 (本文档)
- [ ] 单元测试
- [ ] MediaCrawlerPro 适配器
- [ ] 查询指令生成
- [ ] SKILL/MCP 封装
- [ ] 集成到 FastAPI 服务

---

**实现完成！准备进行测试和 MediaCrawlerPro 集成。** 🎉
