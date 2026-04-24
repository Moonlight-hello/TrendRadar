# 爬虫集成设计模式与最佳实践

> 日期: 2026-04-24 | 参考业界成熟方案

---

## 🎯 核心目标

1. **统一接口** - 屏蔽底层差异
2. **异步解耦** - 爬虫服务与业务逻辑分离
3. **可扩展性** - 轻松添加新平台
4. **容错机制** - 失败重试、降级处理
5. **可观测性** - 任务状态追踪、日志监控

---

## 📚 参考业界成熟方案

### 1. Scrapy 架构（Python 爬虫框架）

```
Engine (引擎)
  ↓
Scheduler (调度器)
  ↓
Downloader (下载器)
  ↓
Spider (爬虫)
  ↓
Item Pipeline (数据处理)
```

**借鉴点**：
- ✅ 清晰的职责分离
- ✅ 中间件机制（可插拔）
- ✅ 异步处理

### 2. Langchain Tool 抽象

```python
class BaseTool:
    name: str
    description: str

    def _run(self, *args, **kwargs):
        """同步执行"""
        pass

    async def _arun(self, *args, **kwargs):
        """异步执行"""
        pass
```

**借鉴点**：
- ✅ 统一的 Tool 接口
- ✅ 支持同步/异步
- ✅ 声明式描述（name + description）

### 3. Celery 任务队列

```
Client → Broker (Redis/RabbitMQ) → Worker → Result Backend
```

**借鉴点**：
- ✅ 异步任务队列
- ✅ 分布式执行
- ✅ 任务结果追踪

### 4. MCP (Model Context Protocol)

```json
{
  "tools": [
    {
      "name": "get_weather",
      "description": "Get weather information",
      "inputSchema": {...}
    }
  ]
}
```

**借鉴点**：
- ✅ 标准化的协议
- ✅ JSON Schema 验证
- ✅ 工具发现机制

---

## 🏗️ 我们的设计方案

### 整体架构（三层设计）

```
┌───────────────────────────────────────────────────────┐
│                  Application Layer                     │
│            (TrendRadar Agent/API/CLI)                  │
└────────────────────┬──────────────────────────────────┘
                     │
┌────────────────────▼──────────────────────────────────┐
│              Service Layer (统一入口)                   │
│                                                        │
│  ┌────────────────────────────────────────────┐      │
│  │       CrawlerService                        │      │
│  │  - fetch_trending()                         │      │
│  │  - search_posts()                           │      │
│  │  - fetch_comments()                         │      │
│  │  - submit_task() → Task ID                  │      │
│  │  - get_task_status(task_id)                 │      │
│  └────────────────────────────────────────────┘      │
│                                                        │
└────────────────────┬──────────────────────────────────┘
                     │
┌────────────────────▼──────────────────────────────────┐
│            Adapter Layer (适配器层)                     │
│                                                        │
│  ┌──────────────┐        ┌──────────────┐            │
│  │ NewsNowAPI   │        │MediaCrawler  │            │
│  │   Adapter    │        │  Adapter     │            │
│  │              │        │              │            │
│  │ - 同步调用    │        │ - 异步任务    │            │
│  │ - 快速响应    │        │ - 回调机制    │            │
│  │ - 热榜数据    │        │ - 深度抓取    │            │
│  └──────────────┘        └──────────────┘            │
│                                                        │
└────────────────────┬──────────────────────────────────┘
                     │
┌────────────────────▼──────────────────────────────────┐
│          Infrastructure Layer (基础设施)                │
│                                                        │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐     │
│  │TaskManager │  │TaskQueue   │  │TaskStorage │     │
│  │(任务管理)   │  │(Redis/DB)  │  │(SQLite/PG) │     │
│  └────────────┘  └────────────┘  └────────────┘     │
│                                                        │
└───────────────────────────────────────────────────────┘
```

---

## 🎨 设计模式应用

### 1. 适配器模式（Adapter Pattern）

**目的**：统一不同爬虫的接口

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from enum import Enum


class Platform(Enum):
    """支持的平台"""
    ZHIHU = "zhihu"
    WEIBO = "weibo"
    EASTMONEY = "eastmoney"
    XIAOHONGSHU = "xhs"


class CrawlResult:
    """统一的爬取结果"""
    def __init__(
        self,
        success: bool,
        data: List[Dict],
        message: str = "",
        task_id: Optional[str] = None
    ):
        self.success = success
        self.data = data
        self.message = message
        self.task_id = task_id  # 异步任务ID


class CrawlerAdapter(ABC):
    """
    爬虫适配器基类

    所有爬虫都必须实现这个接口
    """

    @abstractmethod
    def get_name(self) -> str:
        """适配器名称"""
        pass

    @abstractmethod
    def get_supported_platforms(self) -> List[Platform]:
        """支持的平台列表"""
        pass

    @abstractmethod
    def is_async(self) -> bool:
        """是否为异步爬虫"""
        pass

    @abstractmethod
    def fetch_trending(
        self,
        platform: Platform,
        limit: int = 50
    ) -> CrawlResult:
        """获取热榜（同步）"""
        pass

    @abstractmethod
    def search_posts(
        self,
        platform: Platform,
        keyword: str,
        limit: int = 50,
        **kwargs
    ) -> CrawlResult:
        """搜索帖子（可能异步）"""
        pass
```

**优势**：
- ✅ 统一接口，调用方无需关心底层实现
- ✅ 易于添加新的爬虫
- ✅ 支持同步/异步两种模式

---

### 2. 策略模式（Strategy Pattern）

**目的**：根据平台选择不同的抓取策略

```python
class CrawlStrategy:
    """抓取策略"""

    def __init__(self):
        # 平台 → 适配器映射
        self.adapters: Dict[Platform, CrawlerAdapter] = {}

    def register(self, platform: Platform, adapter: CrawlerAdapter):
        """注册适配器"""
        self.adapters[platform] = adapter

    def get_adapter(self, platform: Platform) -> CrawlerAdapter:
        """获取适配器"""
        if platform not in self.adapters:
            raise ValueError(f"Platform {platform} not supported")
        return self.adapters[platform]

    def fetch(self, platform: Platform, **kwargs):
        """执行抓取"""
        adapter = self.get_adapter(platform)
        return adapter.search_posts(platform, **kwargs)
```

**优势**：
- ✅ 运行时动态选择策略
- ✅ 易于扩展新平台
- ✅ 降低耦合

---

### 3. 外观模式（Facade Pattern）

**目的**：提供统一的高层接口

```python
class CrawlerService:
    """
    爬虫服务外观

    对外提供简单易用的接口，隐藏内部复杂性
    """

    def __init__(self):
        self.strategy = CrawlStrategy()
        self.task_manager = TaskManager()

        # 注册适配器
        self._register_adapters()

    def _register_adapters(self):
        """注册所有适配器"""
        # NewsNow - 同步
        newsnow = NewsNowAdapter()
        for platform in newsnow.get_supported_platforms():
            self.strategy.register(platform, newsnow)

        # MediaCrawler - 异步
        mediacrawler = MediaCrawlerAdapter()
        for platform in mediacrawler.get_supported_platforms():
            self.strategy.register(platform, mediacrawler)

    # ========== 简单接口 ==========

    def get_trending(self, platform: str, limit: int = 50) -> Dict:
        """
        获取热榜（简化接口）

        Usage:
            service.get_trending("zhihu", limit=50)
        """
        platform_enum = Platform(platform)
        result = self.strategy.fetch(
            platform_enum,
            limit=limit
        )
        return {
            'success': result.success,
            'data': result.data,
            'message': result.message
        }

    def search(
        self,
        platform: str,
        keyword: str,
        limit: int = 50,
        async_mode: bool = False
    ) -> Dict:
        """
        搜索（自动处理同步/异步）

        Usage:
            # 同步
            service.search("zhihu", "AI", limit=50)

            # 异步
            result = service.search("eastmoney", "特斯拉", async_mode=True)
            task_id = result['task_id']
            status = service.get_task_status(task_id)
        """
        platform_enum = Platform(platform)
        adapter = self.strategy.get_adapter(platform_enum)

        if async_mode or adapter.is_async():
            # 异步模式：提交任务
            task_id = self.task_manager.submit_task(
                adapter=adapter,
                method='search_posts',
                args=(platform_enum, keyword, limit)
            )
            return {
                'success': True,
                'task_id': task_id,
                'status': 'pending',
                'message': '任务已提交'
            }
        else:
            # 同步模式：直接返回结果
            result = adapter.search_posts(platform_enum, keyword, limit)
            return {
                'success': result.success,
                'data': result.data,
                'message': result.message
            }

    def get_task_status(self, task_id: str) -> Dict:
        """查询任务状态"""
        return self.task_manager.get_status(task_id)
```

**优势**：
- ✅ 接口简单易用
- ✅ 自动处理同步/异步
- ✅ 隐藏复杂的内部逻辑

---

### 4. 观察者模式（Observer Pattern）

**目的**：异步回调通知

```python
class TaskObserver(ABC):
    """任务观察者"""

    @abstractmethod
    def on_task_complete(self, task_id: str, result: Dict):
        """任务完成回调"""
        pass

    @abstractmethod
    def on_task_failed(self, task_id: str, error: str):
        """任务失败回调"""
        pass


class TaskManager:
    """任务管理器"""

    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.observers: List[TaskObserver] = []

    def add_observer(self, observer: TaskObserver):
        """添加观察者"""
        self.observers.append(observer)

    def submit_task(self, adapter, method, args) -> str:
        """提交任务"""
        task_id = self._generate_task_id()
        task = Task(task_id, adapter, method, args)
        self.tasks[task_id] = task

        # 异步执行
        self._execute_async(task)

        return task_id

    def _execute_async(self, task: Task):
        """异步执行任务"""
        import threading

        def worker():
            try:
                # 执行任务
                result = task.execute()
                task.status = "completed"
                task.result = result

                # 通知观察者
                for observer in self.observers:
                    observer.on_task_complete(task.id, result)

            except Exception as e:
                task.status = "failed"
                task.error = str(e)

                # 通知观察者
                for observer in self.observers:
                    observer.on_task_failed(task.id, str(e))

        thread = threading.Thread(target=worker)
        thread.daemon = True
        thread.start()
```

**优势**：
- ✅ 解耦任务执行和结果处理
- ✅ 支持多个观察者
- ✅ 易于扩展通知方式

---

## 🔧 实现细节

### 1. NewsNow Adapter（同步）

```python
class NewsNowAdapter(CrawlerAdapter):
    """NewsNow API 适配器（同步）"""

    def get_name(self) -> str:
        return "NewsNow"

    def is_async(self) -> bool:
        return False  # 同步

    def get_supported_platforms(self) -> List[Platform]:
        return [Platform.ZHIHU, Platform.WEIBO]

    def fetch_trending(self, platform: Platform, limit: int = 50):
        """同步获取热榜"""
        from trendradar.crawler import DataFetcher

        fetcher = DataFetcher()
        response, _, _ = fetcher.fetch_data(platform.value)

        if not response:
            return CrawlResult(False, [], "Failed to fetch")

        # 解析和标准化
        data = self._parse_response(response)
        return CrawlResult(True, data[:limit], "Success")

    def search_posts(self, platform, keyword, limit, **kwargs):
        """NewsNow 不支持搜索"""
        raise NotImplementedError("NewsNow does not support search")
```

### 2. MediaCrawler Adapter（异步）

```python
class MediaCrawlerAdapter(CrawlerAdapter):
    """MediaCrawlerPro 适配器（异步）"""

    def __init__(self, mediacrawler_path: str = None):
        self.path = mediacrawler_path or \
            "/Users/wangxinlong/Code/communityspy/MediaCrawlerPro-Python"

        # 动态导入（延迟加载）
        self._crawler = None

    def get_name(self) -> str:
        return "MediaCrawlerPro"

    def is_async(self) -> bool:
        return True  # 异步

    def get_supported_platforms(self) -> List[Platform]:
        return [
            Platform.XIAOHONGSHU,
            Platform.EASTMONEY,
            # ... 更多平台
        ]

    def search_posts(self, platform, keyword, limit, **kwargs):
        """
        异步搜索（返回任务ID）

        实际的抓取会在后台执行
        """
        # 返回未完成的结果，包含 task_id
        task_id = self._submit_crawl_task(platform, keyword, limit)

        return CrawlResult(
            success=True,
            data=[],
            message="Task submitted",
            task_id=task_id
        )

    def _submit_crawl_task(self, platform, keyword, limit) -> str:
        """提交爬取任务到 MediaCrawlerPro"""
        # 这里可以：
        # 1. 直接调用 MediaCrawlerPro 的 Python API
        # 2. 或者调用 MediaCrawlerPro 的 HTTP 服务
        # 3. 或者使用消息队列（Celery/RQ）

        # 示例：使用 subprocess 调用
        import subprocess
        task_id = str(uuid.uuid4())

        cmd = [
            "python", f"{self.path}/main.py",
            "--platform", platform.value,
            "--type", "search",
            "--keywords", keyword,
            "--max-count", str(limit),
            "--task-id", task_id
        ]

        # 后台执行
        subprocess.Popen(cmd, cwd=self.path)

        return task_id
```

---

## 📊 任务状态管理

### Task 模型

```python
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Any

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class Task:
    id: str
    adapter_name: str
    method: str
    args: tuple
    kwargs: dict
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
```

### 存储（SQLite）

```sql
CREATE TABLE tasks (
    id TEXT PRIMARY KEY,
    adapter_name TEXT NOT NULL,
    method TEXT NOT NULL,
    args TEXT,  -- JSON
    kwargs TEXT,  -- JSON
    status TEXT NOT NULL,
    result TEXT,  -- JSON
    error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX idx_status ON tasks(status);
CREATE INDEX idx_created_at ON tasks(created_at);
```

---

## 🎯 使用示例

### 场景1：获取热榜（同步）

```python
from trendradar.crawler import CrawlerService

service = CrawlerService()

# 简单调用
result = service.get_trending("zhihu", limit=50)

print(f"Success: {result['success']}")
print(f"Count: {len(result['data'])}")
```

### 场景2：搜索股票讨论（异步）

```python
# 提交任务
result = service.search(
    platform="eastmoney",
    keyword="特斯拉",
    limit=100,
    async_mode=True
)

task_id = result['task_id']
print(f"Task ID: {task_id}")

# 轮询状态
import time
while True:
    status = service.get_task_status(task_id)
    print(f"Status: {status['status']}")

    if status['status'] == 'completed':
        data = status['result']['data']
        print(f"Got {len(data)} posts")
        break

    elif status['status'] == 'failed':
        print(f"Error: {status['error']}")
        break

    time.sleep(5)
```

### 场景3：在 Agent 中使用

```python
from trendradar.agent import BaseAgent
from trendradar.crawler import CrawlerService

class StockMonitorAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.crawler = CrawlerService()

    def run(self, stock_code: str):
        # 1. 搜索讨论
        result = self.crawler.search(
            platform="eastmoney",
            keyword=stock_code,
            async_mode=True
        )

        task_id = result['task_id']

        # 2. 注册回调
        self.crawler.task_manager.add_observer(
            StockAnalysisObserver(self, stock_code)
        )

        return f"Monitoring started for {stock_code}"


class StockAnalysisObserver(TaskObserver):
    def __init__(self, agent, stock_code):
        self.agent = agent
        self.stock_code = stock_code

    def on_task_complete(self, task_id, result):
        # 任务完成，进行分析
        posts = result['data']
        analysis = self.agent.analyze(posts)
        self.agent.report(self.stock_code, analysis)

    def on_task_failed(self, task_id, error):
        print(f"Failed to crawl {self.stock_code}: {error}")
```

---

## ✅ 设计优势

1. **清晰的职责分离**
   - Service Layer：业务逻辑
   - Adapter Layer：平台适配
   - Infrastructure Layer：基础设施

2. **统一的接口**
   - 所有爬虫实现相同的 `CrawlerAdapter` 接口
   - 调用方无需关心底层差异

3. **同步/异步透明**
   - Service Layer 自动处理
   - 用户可以选择模式

4. **易于扩展**
   - 添加新平台：实现 `CrawlerAdapter`
   - 添加新功能：扩展 `CrawlerService`

5. **可测试性强**
   - 每层独立测试
   - Mock 适配器

---

## 🚀 下一步实现

按以下顺序实现：

1. **基础接口** (1小时)
   - `CrawlerAdapter` 基类
   - `CrawlResult` 模型
   - `Platform` 枚举

2. **NewsNow Adapter** (30分钟)
   - 包装现有的 `DataFetcher`
   - 同步实现

3. **Task Manager** (1小时)
   - 任务模型
   - SQLite 存储
   - 状态查询

4. **MediaCrawler Adapter** (2小时)
   - 异步任务提交
   - 回调机制
   - 结果读取

5. **CrawlerService** (1小时)
   - 外观模式实现
   - 统一接口

6. **测试和文档** (1小时)

**总计：约 6.5 小时**

---

**准备好开始实现了吗？** 🎯
