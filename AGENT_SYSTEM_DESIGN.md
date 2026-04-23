# TrendRadar Agent System Design

> **基于 Claude Code 架构思想的模块化 Agent 系统设计**
>
> **版本**: v1.0
> **日期**: 2026-04-20
> **作者**: Claude Code AI Assistant

---

## 📑 目录

1. [设计理念](#1-设计理念)
2. [Claude Code 架构借鉴](#2-claude-code-架构借鉴)
3. [三层架构设计](#3-三层架构设计)
4. [Agent 系统设计](#4-agent-系统设计)
5. [工具插件系统](#5-工具插件系统)
6. [数据流设计](#6-数据流设计)
7. [扩展机制](#7-扩展机制)
8. [实施路线图](#8-实施路线图)

---

## 1. 设计理念

### 1.1 核心目标

```
┌─────────────────────────────────────────────────────────┐
│                  核心设计目标                            │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  🎯 痛点: 没空看新闻联播，需要第一手资料                │
│                                                          │
│  💡 解决方案:                                            │
│    • 自动爬取 - 无需人工干预                            │
│    • 智能关注 - 自动过滤和分类                          │
│    • 深度分析 - AI驱动的洞察                            │
│    • 主动推送 - 第一时间通知                            │
│                                                          │
│  🔧 技术方案:                                            │
│    • 模块化 Agent 系统                                   │
│    • 可插拔的工具生态                                    │
│    • 三层架构（Planning → Execution → Reflection）      │
│    • Harness 编排框架                                    │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 1.2 设计原则

#### 1.2.1 模块化 (Modularity)

```
每个模块职责单一、边界清晰
- 数据采集模块: 只负责获取数据
- 分析模块: 只负责数据处理和分析
- 通知模块: 只负责推送通知
- Agent 模块: 只负责编排和决策
```

#### 1.2.2 可扩展性 (Extensibility)

```
易于添加新功能，无需修改核心代码
- 新增数据源: 实现 DataSourceTool 接口
- 新增通知渠道: 实现 NotificationTool 接口
- 新增分析能力: 实现 AnalyzerTool 接口
- 新增 Agent: 继承 BaseAgent 类
```

#### 1.2.3 可组合性 (Composability)

```
小工具组合成大能力
- Tool → Agent → Workflow
- 单一工具 → Agent 编排 → 复杂任务流
```

#### 1.2.4 可观测性 (Observability)

```
每个环节都可追踪、可调试
- 日志: 结构化日志记录
- 追踪: 任务执行链路追踪
- 指标: 性能和成功率监控
```

---

## 2. Claude Code 架构借鉴

### 2.1 三层思考模型

```
┌─────────────────────────────────────────────────────────┐
│              Claude Code 的三层思考模型                  │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Layer 1: Planning (规划层)                             │
│  ├─ 理解用户意图                                         │
│  ├─ 拆解任务步骤                                         │
│  ├─ 选择合适的工具                                       │
│  └─ 制定执行计划                                         │
│                                                          │
│  Layer 2: Execution (执行层)                            │
│  ├─ 调用工具执行任务                                     │
│  ├─ 处理工具返回结果                                     │
│  ├─ 维护执行上下文                                       │
│  └─ 处理异常和重试                                       │
│                                                          │
│  Layer 3: Reflection (反思层)                           │
│  ├─ 评估执行结果                                         │
│  ├─ 总结经验教训                                         │
│  ├─ 优化后续决策                                         │
│  └─ 生成用户反馈                                         │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 2.2 Harness 编排框架

```python
# Harness 框架的核心职责
class AgentHarness:
    """
    Agent 编排器，负责:
    1. 工具注册和发现
    2. Agent 生命周期管理
    3. 上下文传递
    4. 错误处理和重试
    5. 结果聚合
    """

    def __init__(self):
        self.tool_registry = ToolRegistry()
        self.agents = {}
        self.context_manager = ContextManager()

    def register_tool(self, tool: BaseTool):
        """注册工具到工具库"""
        self.tool_registry.register(tool)

    def register_agent(self, agent_name: str, agent: BaseAgent):
        """注册 Agent"""
        self.agents[agent_name] = agent

    def run(self, task: Task) -> Result:
        """执行任务"""
        # Planning: 选择合适的 Agent
        agent = self.select_agent(task)

        # Execution: 执行任务
        result = agent.execute(task, self.tool_registry)

        # Reflection: 反思和优化
        self.reflect(result)

        return result
```

### 2.3 工具系统

```python
# Claude Code 的工具系统特点

1. 统一接口
   - 所有工具实现相同的接口
   - 输入输出格式标准化

2. 自描述
   - 工具提供元数据（name, description, parameters）
   - LLM 可以理解工具的功能

3. 可组合
   - 工具可以调用其他工具
   - 支持工具链

示例:
class ReadFileTool(BaseTool):
    name = "read_file"
    description = "Read content from a file"

    def execute(self, file_path: str) -> str:
        with open(file_path) as f:
            return f.read()

class AnalyzeCodeTool(BaseTool):
    name = "analyze_code"
    description = "Analyze code for issues"

    def execute(self, code: str) -> AnalysisResult:
        # 可以调用其他工具
        return self.analyzer.analyze(code)
```

---

## 3. 三层架构设计

### 3.1 架构总览

```
┌──────────────────────────────────────────────────────────┐
│                    TrendRadar Agent 系统                  │
└──────────────────────────────────────────────────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Layer 1: Planning Layer (规划层)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌──────────────────────────────────────────────────────┐
│           Orchestrator (编排器)                       │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐     │
│  │ Task Planner│  │Agent Selector│  │Tool Resolver│   │
│  └────────────┘  └────────────┘  └────────────┘     │
│                                                       │
│  功能:                                                │
│  • 解析用户需求                                       │
│  • 拆解任务步骤                                       │
│  • 选择合适的 Agent                                   │
│  • 制定执行计划                                       │
└──────────────────────────────────────────────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Layer 2: Execution Layer (执行层)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌──────────────────────────────────────────────────────┐
│               Specialized Agents (专业化 Agent)        │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐     │
│  │Crawler Agent│  │Analyzer Agent│ │Notifier Agent│   │
│  └────────────┘  └────────────┘  └────────────┘     │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐     │
│  │Monitor Agent│  │Reporter Agent│ │Scheduler Agent│  │
│  └────────────┘  └────────────┘  └────────────┘     │
│                                                       │
│  每个 Agent:                                          │
│  • 负责特定领域的任务                                 │
│  • 调用工具完成工作                                   │
│  • 管理局部上下文                                     │
│  • 报告执行结果                                       │
└──────────────────────────────────────────────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Layer 3: Tool Layer (工具层)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌──────────────────────────────────────────────────────┐
│                  Tool Ecosystem (工具生态)             │
│                                                       │
│  ┌─────────────────────────────────────────────┐    │
│  │  Data Source Tools (数据源工具)              │    │
│  ├─────────────────────────────────────────────┤    │
│  │  • HotNewsScraperTool   - 热榜爬虫          │    │
│  │  • RSSFetcherTool       - RSS 订阅          │    │
│  │  • APIDataTool          - API 数据源        │    │
│  │  • WebScraperTool       - 通用网页爬虫      │    │
│  └─────────────────────────────────────────────┘    │
│                                                       │
│  ┌─────────────────────────────────────────────┐    │
│  │  Analyzer Tools (分析工具)                   │    │
│  ├─────────────────────────────────────────────┤    │
│  │  • KeywordMatcherTool   - 关键词匹配        │    │
│  │  • SentimentAnalyzerTool - 情感分析         │    │
│  │  • TrendDetectorTool    - 趋势检测          │    │
│  │  • AnomalyDetectorTool  - 异常检测          │    │
│  │  • AIAnalyzerTool       - AI 深度分析       │    │
│  └─────────────────────────────────────────────┘    │
│                                                       │
│  ┌─────────────────────────────────────────────┐    │
│  │  Notification Tools (通知工具)               │    │
│  ├─────────────────────────────────────────────┤    │
│  │  • FeishuNotifierTool   - 飞书通知          │    │
│  │  • DingTalkNotifierTool - 钉钉通知          │    │
│  │  • TelegramNotifierTool - Telegram 通知     │    │
│  │  • EmailNotifierTool    - 邮件通知          │    │
│  └─────────────────────────────────────────────┘    │
│                                                       │
│  ┌─────────────────────────────────────────────┐    │
│  │  Storage Tools (存储工具)                    │    │
│  ├─────────────────────────────────────────────┤    │
│  │  • SQLiteStorageTool    - SQLite 存储       │    │
│  │  • S3StorageTool        - S3 对象存储       │    │
│  │  • CacheTool             - 缓存工具          │    │
│  └─────────────────────────────────────────────┘    │
│                                                       │
│  ┌─────────────────────────────────────────────┐    │
│  │  Utility Tools (实用工具)                    │    │
│  ├─────────────────────────────────────────────┤    │
│  │  • TimerTool            - 定时调度          │    │
│  │  • FilterTool           - 数据过滤          │    │
│  │  • TransformTool        - 数据转换          │    │
│  │  • ValidationTool       - 数据验证          │    │
│  └─────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Cross-Cutting Concerns (横切关注点)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌──────────────────────────────────────────────────────┐
│  • Context Manager    - 上下文管理                    │
│  • Error Handler      - 错误处理                      │
│  • Logger             - 日志系统                      │
│  • Monitor            - 监控系统                      │
│  • Config Manager     - 配置管理                      │
└──────────────────────────────────────────────────────┘
```

### 3.2 Layer 1: Planning Layer (规划层)

#### 3.2.1 Orchestrator (编排器)

```python
class Orchestrator:
    """
    顶层编排器，负责任务的规划和分配
    """

    def __init__(self):
        self.task_planner = TaskPlanner()
        self.agent_selector = AgentSelector()
        self.tool_resolver = ToolResolver()
        self.context = Context()

    def plan(self, request: UserRequest) -> ExecutionPlan:
        """
        规划执行方案

        输入: 用户请求（如"监控科技新闻"）
        输出: 执行计划
        """
        # 1. 理解意图
        intent = self.understand_intent(request)

        # 2. 拆解任务
        tasks = self.task_planner.decompose(intent)

        # 3. 为每个任务选择 Agent
        plan = ExecutionPlan()
        for task in tasks:
            agent = self.agent_selector.select(task)
            tools = self.tool_resolver.resolve(task)
            plan.add_step(task, agent, tools)

        return plan

    def understand_intent(self, request: UserRequest) -> Intent:
        """
        理解用户意图

        示例:
        "监控科技新闻并推送到飞书"
        →
        Intent(
            action="monitor",
            domain="tech_news",
            output="feishu"
        )
        """
        # 使用 LLM 或规则引擎解析意图
        return self.intent_parser.parse(request)
```

#### 3.2.2 TaskPlanner (任务规划器)

```python
class TaskPlanner:
    """
    任务规划器，负责将复杂任务拆解为子任务
    """

    def decompose(self, intent: Intent) -> List[Task]:
        """
        任务拆解

        示例:
        Intent("监控科技新闻") →
        [
            Task("采集数据", "crawler"),
            Task("过滤关键词", "analyzer"),
            Task("生成报告", "reporter"),
            Task("推送通知", "notifier")
        ]
        """
        tasks = []

        # 根据意图类型选择任务模板
        if intent.action == "monitor":
            tasks.append(Task("collect_data", priority=1))
            tasks.append(Task("analyze_data", priority=2))
            tasks.append(Task("generate_report", priority=3))
            tasks.append(Task("notify", priority=4))

        return tasks
```

#### 3.2.3 AgentSelector (Agent 选择器)

```python
class AgentSelector:
    """
    Agent 选择器，为任务选择最合适的 Agent
    """

    def __init__(self):
        self.agent_registry = {}

    def register(self, agent_type: str, agent_class):
        """注册 Agent"""
        self.agent_registry[agent_type] = agent_class

    def select(self, task: Task) -> BaseAgent:
        """
        为任务选择 Agent

        规则:
        - collect_data → CrawlerAgent
        - analyze_data → AnalyzerAgent
        - notify → NotifierAgent
        """
        agent_type = self.match_agent_type(task)
        agent_class = self.agent_registry.get(agent_type)
        return agent_class()

    def match_agent_type(self, task: Task) -> str:
        """匹配任务类型到 Agent 类型"""
        mapping = {
            "collect_data": "crawler",
            "analyze_data": "analyzer",
            "generate_report": "reporter",
            "notify": "notifier"
        }
        return mapping.get(task.type)
```

### 3.3 Layer 2: Execution Layer (执行层)

#### 3.3.1 BaseAgent (Agent 基类)

```python
from abc import ABC, abstractmethod
from typing import Any, Dict, List

class BaseAgent(ABC):
    """
    Agent 基类，定义所有 Agent 的通用接口
    """

    def __init__(self, name: str):
        self.name = name
        self.context = None
        self.tools = []

    def set_context(self, context: Context):
        """设置执行上下文"""
        self.context = context

    def register_tools(self, tools: List[BaseTool]):
        """注册工具"""
        self.tools = tools

    @abstractmethod
    def plan(self, task: Task) -> List[Action]:
        """
        规划执行步骤
        返回一系列动作
        """
        pass

    @abstractmethod
    def execute(self, task: Task) -> Result:
        """
        执行任务
        """
        pass

    def reflect(self, result: Result) -> Reflection:
        """
        反思执行结果
        """
        return Reflection(
            success=result.success,
            lessons=self.extract_lessons(result),
            improvements=self.suggest_improvements(result)
        )

    def call_tool(self, tool_name: str, **kwargs) -> Any:
        """调用工具"""
        tool = self.find_tool(tool_name)
        if not tool:
            raise ToolNotFoundError(f"Tool {tool_name} not found")

        return tool.execute(**kwargs)

    def find_tool(self, tool_name: str) -> BaseTool:
        """查找工具"""
        for tool in self.tools:
            if tool.name == tool_name:
                return tool
        return None
```

#### 3.3.2 专业化 Agent 设计

##### CrawlerAgent (爬虫 Agent)

```python
class CrawlerAgent(BaseAgent):
    """
    爬虫 Agent
    负责数据采集任务
    """

    def __init__(self):
        super().__init__("CrawlerAgent")

    def plan(self, task: Task) -> List[Action]:
        """
        规划爬取步骤

        示例任务: "采集知乎和微博热榜"
        →
        [
            Action("use_tool", "hot_news_scraper", platform="zhihu"),
            Action("use_tool", "hot_news_scraper", platform="weibo"),
            Action("save_to_storage", storage="sqlite")
        ]
        """
        actions = []

        # 获取数据源列表
        data_sources = task.params.get("data_sources", [])

        for source in data_sources:
            actions.append(Action(
                type="use_tool",
                tool="hot_news_scraper",
                params={"platform": source}
            ))

        # 保存数据
        actions.append(Action(
            type="use_tool",
            tool="sqlite_storage",
            params={"operation": "save"}
        ))

        return actions

    def execute(self, task: Task) -> Result:
        """
        执行爬取任务
        """
        # Planning: 规划步骤
        actions = self.plan(task)

        # Execution: 执行步骤
        results = []
        for action in actions:
            try:
                result = self.execute_action(action)
                results.append(result)
            except Exception as e:
                self.handle_error(action, e)

        # Reflection: 反思
        reflection = self.reflect(Result(
            success=all(r.success for r in results),
            data=results
        ))

        return Result(
            success=True,
            data={"crawled_data": results},
            reflection=reflection
        )

    def execute_action(self, action: Action) -> ActionResult:
        """执行单个动作"""
        if action.type == "use_tool":
            return self.call_tool(action.tool, **action.params)

        return ActionResult(success=False, error="Unknown action type")
```

##### AnalyzerAgent (分析 Agent)

```python
class AnalyzerAgent(BaseAgent):
    """
    分析 Agent
    负责数据分析任务
    """

    def __init__(self):
        super().__init__("AnalyzerAgent")

    def plan(self, task: Task) -> List[Action]:
        """
        规划分析步骤

        示例任务: "分析科技新闻趋势"
        →
        [
            Action("load_data", source="sqlite"),
            Action("use_tool", "keyword_matcher", keywords=["AI", "芯片"]),
            Action("use_tool", "trend_detector"),
            Action("use_tool", "ai_analyzer")
        ]
        """
        return [
            Action("load_data"),
            Action("filter_by_keywords"),
            Action("detect_trends"),
            Action("ai_analysis")
        ]

    def execute(self, task: Task) -> Result:
        """
        执行分析任务
        """
        # 1. 加载数据
        data = self.call_tool("sqlite_storage", operation="load")

        # 2. 关键词过滤
        filtered_data = self.call_tool(
            "keyword_matcher",
            data=data,
            keywords=task.params.get("keywords", [])
        )

        # 3. 趋势检测
        trends = self.call_tool("trend_detector", data=filtered_data)

        # 4. AI 深度分析
        insights = self.call_tool("ai_analyzer", data=filtered_data)

        return Result(
            success=True,
            data={
                "filtered_data": filtered_data,
                "trends": trends,
                "insights": insights
            }
        )
```

##### NotifierAgent (通知 Agent)

```python
class NotifierAgent(BaseAgent):
    """
    通知 Agent
    负责推送通知任务
    """

    def __init__(self):
        super().__init__("NotifierAgent")

    def execute(self, task: Task) -> Result:
        """
        执行推送任务

        支持多渠道并行推送
        """
        content = task.params.get("content")
        channels = task.params.get("channels", [])

        results = []
        for channel in channels:
            try:
                result = self.send_to_channel(channel, content)
                results.append(result)
            except Exception as e:
                self.handle_error(channel, e)

        return Result(
            success=all(r.success for r in results),
            data={"notification_results": results}
        )

    def send_to_channel(self, channel: str, content: str) -> ActionResult:
        """发送到指定渠道"""
        tool_mapping = {
            "feishu": "feishu_notifier",
            "dingtalk": "dingtalk_notifier",
            "telegram": "telegram_notifier"
        }

        tool_name = tool_mapping.get(channel)
        return self.call_tool(tool_name, content=content)
```

##### MonitorAgent (监控 Agent)

```python
class MonitorAgent(BaseAgent):
    """
    监控 Agent
    负责持续监控任务
    """

    def __init__(self):
        super().__init__("MonitorAgent")
        self.scheduler = None

    def execute(self, task: Task) -> Result:
        """
        执行监控任务

        示例:
        - 每小时采集一次数据
        - 检测到新增热点立即推送
        """
        schedule = task.params.get("schedule", "1h")

        # 初始化调度器
        self.scheduler = self.call_tool("timer", interval=schedule)

        while True:
            # 等待下次执行
            self.scheduler.wait()

            # 执行监控任务
            result = self.monitor_once(task)

            # 检查是否需要通知
            if result.has_new_data:
                self.trigger_notification(result.data)

    def monitor_once(self, task: Task) -> MonitorResult:
        """执行一次监控"""
        # 采集数据
        crawler_result = self.call_tool("crawler_agent", task=task)

        # 检测变化
        changes = self.detect_changes(crawler_result.data)

        return MonitorResult(
            has_new_data=len(changes) > 0,
            data=changes
        )
```

### 3.4 Layer 3: Tool Layer (工具层)

#### 3.4.1 BaseTool (工具基类)

```python
from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseTool(ABC):
    """
    工具基类
    定义所有工具的通用接口
    """

    def __init__(self):
        self.name = ""
        self.description = ""
        self.parameters = {}

    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """
        执行工具
        """
        pass

    def validate_params(self, **kwargs) -> bool:
        """验证参数"""
        for param_name, param_spec in self.parameters.items():
            if param_spec.get("required", False):
                if param_name not in kwargs:
                    raise ValueError(f"Missing required parameter: {param_name}")
        return True

    def get_metadata(self) -> Dict:
        """获取工具元数据"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }
```

#### 3.4.2 数据源工具

##### HotNewsScraperTool

```python
class HotNewsScraperTool(BaseTool):
    """
    热榜爬虫工具
    """

    def __init__(self):
        super().__init__()
        self.name = "hot_news_scraper"
        self.description = "Scrape hot news from various platforms"
        self.parameters = {
            "platform": {
                "type": "string",
                "description": "Platform name (zhihu, weibo, etc.)",
                "required": True
            },
            "limit": {
                "type": "integer",
                "description": "Number of news items to fetch",
                "default": 50
            }
        }

    def execute(self, platform: str, limit: int = 50) -> List[NewsItem]:
        """
        执行爬取
        """
        self.validate_params(platform=platform)

        # 调用现有的 DataFetcher
        from trendradar.crawler.fetcher import DataFetcher

        fetcher = DataFetcher()
        results, _, _ = fetcher.crawl_websites([platform])

        # 转换为 NewsItem
        items = self.convert_to_news_items(results)

        return items[:limit]
```

##### RSSFetcherTool

```python
class RSSFetcherTool(BaseTool):
    """
    RSS 订阅工具
    """

    def __init__(self):
        super().__init__()
        self.name = "rss_fetcher"
        self.description = "Fetch RSS feed content"
        self.parameters = {
            "feed_url": {
                "type": "string",
                "description": "RSS feed URL",
                "required": True
            },
            "max_age_days": {
                "type": "integer",
                "description": "Maximum age of articles in days",
                "default": 3
            }
        }

    def execute(self, feed_url: str, max_age_days: int = 3) -> List[RSSItem]:
        """
        执行 RSS 抓取
        """
        from trendradar.crawler.rss.fetcher import RSSFetcher

        fetcher = RSSFetcher()
        items, error = fetcher.fetch_feed({
            "url": feed_url,
            "max_age_days": max_age_days
        })

        return items
```

#### 3.4.3 分析工具

##### KeywordMatcherTool

```python
class KeywordMatcherTool(BaseTool):
    """
    关键词匹配工具
    """

    def __init__(self):
        super().__init__()
        self.name = "keyword_matcher"
        self.description = "Filter news by keywords"
        self.parameters = {
            "data": {
                "type": "array",
                "description": "News items to filter",
                "required": True
            },
            "keywords": {
                "type": "array",
                "description": "Keywords to match",
                "required": True
            }
        }

    def execute(self, data: List[NewsItem], keywords: List[str]) -> List[NewsItem]:
        """
        关键词匹配
        """
        filtered = []
        for item in data:
            if any(keyword in item.title for keyword in keywords):
                filtered.append(item)

        return filtered
```

##### TrendDetectorTool

```python
class TrendDetectorTool(BaseTool):
    """
    趋势检测工具
    """

    def __init__(self):
        super().__init__()
        self.name = "trend_detector"
        self.description = "Detect trending topics"

    def execute(self, data: List[NewsItem]) -> List[Trend]:
        """
        检测趋势
        """
        # 统计词频
        word_counts = self.count_words(data)

        # 识别上升趋势
        trending = self.identify_trending(word_counts)

        return trending
```

##### AIAnalyzerTool

```python
class AIAnalyzerTool(BaseTool):
    """
    AI 深度分析工具
    """

    def __init__(self):
        super().__init__()
        self.name = "ai_analyzer"
        self.description = "AI-powered deep analysis"

    def execute(self, data: List[NewsItem]) -> AIAnalysisResult:
        """
        AI 分析
        """
        from trendradar.ai.analyzer import AIAnalyzer

        analyzer = AIAnalyzer()
        result = analyzer.analyze(data)

        return result
```

#### 3.4.4 通知工具

```python
class FeishuNotifierTool(BaseTool):
    """飞书通知工具"""

    def execute(self, content: str, webhook_url: str) -> bool:
        from trendradar.notification.senders import send_to_feishu
        return send_to_feishu(webhook_url, content)

class DingTalkNotifierTool(BaseTool):
    """钉钉通知工具"""

    def execute(self, content: str, webhook_url: str) -> bool:
        from trendradar.notification.senders import send_to_dingtalk
        return send_to_dingtalk(webhook_url, content)
```

---

## 4. Agent 系统设计

### 4.1 Agent 生命周期

```
┌─────────────────────────────────────────────────────────┐
│                   Agent 生命周期                         │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  1. Initialize (初始化)                                  │
│     ├─ 加载配置                                          │
│     ├─ 注册工具                                          │
│     └─ 初始化上下文                                      │
│                                                          │
│  2. Plan (规划)                                          │
│     ├─ 理解任务                                          │
│     ├─ 拆解步骤                                          │
│     └─ 选择工具                                          │
│                                                          │
│  3. Execute (执行)                                       │
│     ├─ 执行每个步骤                                      │
│     ├─ 调用工具                                          │
│     └─ 收集结果                                          │
│                                                          │
│  4. Reflect (反思)                                       │
│     ├─ 评估结果                                          │
│     ├─ 记录经验                                          │
│     └─ 优化策略                                          │
│                                                          │
│  5. Cleanup (清理)                                       │
│     └─ 释放资源                                          │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 4.2 Agent 协作模式

#### 4.2.1 顺序执行模式

```python
# 任务按顺序执行
workflow = Workflow([
    ("CrawlerAgent", "采集数据"),
    ("AnalyzerAgent", "分析数据"),
    ("ReporterAgent", "生成报告"),
    ("NotifierAgent", "推送通知")
])

result = workflow.execute()
```

#### 4.2.2 并行执行模式

```python
# 多个 Agent 并行执行
parallel_workflow = ParallelWorkflow([
    ("CrawlerAgent", {"platform": "zhihu"}),
    ("CrawlerAgent", {"platform": "weibo"}),
    ("CrawlerAgent", {"platform": "toutiao"})
])

results = parallel_workflow.execute()
```

#### 4.2.3 条件执行模式

```python
# 根据条件选择执行路径
conditional_workflow = ConditionalWorkflow()
conditional_workflow.add_condition(
    lambda result: result.has_new_data,
    then_agent="NotifierAgent",
    else_agent="IdleAgent"
)
```

### 4.3 上下文管理

```python
class Context:
    """
    执行上下文
    在 Agent 之间传递状态和数据
    """

    def __init__(self):
        self.data = {}
        self.metadata = {}
        self.history = []

    def set(self, key: str, value: Any):
        """设置上下文数据"""
        self.data[key] = value
        self.history.append(("set", key, value))

    def get(self, key: str) -> Any:
        """获取上下文数据"""
        return self.data.get(key)

    def update(self, updates: Dict):
        """批量更新"""
        self.data.update(updates)
        self.history.append(("update", updates))

    def snapshot(self) -> Dict:
        """保存快照"""
        return {
            "data": self.data.copy(),
            "metadata": self.metadata.copy(),
            "timestamp": time.time()
        }
```

---

## 5. 工具插件系统

### 5.1 工具注册机制

```python
class ToolRegistry:
    """
    工具注册表
    管理所有可用的工具
    """

    def __init__(self):
        self.tools = {}
        self.categories = {}

    def register(self, tool: BaseTool, category: str = "general"):
        """
        注册工具

        示例:
        registry.register(HotNewsScraperTool(), "data_source")
        """
        self.tools[tool.name] = tool

        if category not in self.categories:
            self.categories[category] = []
        self.categories[category].append(tool.name)

    def get(self, tool_name: str) -> BaseTool:
        """获取工具"""
        return self.tools.get(tool_name)

    def list_tools(self, category: str = None) -> List[str]:
        """列出工具"""
        if category:
            return self.categories.get(category, [])
        return list(self.tools.keys())

    def get_metadata(self, tool_name: str) -> Dict:
        """获取工具元数据"""
        tool = self.get(tool_name)
        if tool:
            return tool.get_metadata()
        return None
```

### 5.2 工具发现机制

```python
class ToolDiscovery:
    """
    工具发现
    自动发现和加载工具
    """

    @staticmethod
    def discover_tools(package_path: str) -> List[BaseTool]:
        """
        发现指定包下的所有工具

        示例:
        tools = ToolDiscovery.discover_tools("trendradar.tools")
        """
        tools = []

        # 扫描包目录
        for module in pkgutil.iter_modules([package_path]):
            if module.name.endswith("_tool"):
                # 加载模块
                mod = importlib.import_module(f"{package_path}.{module.name}")

                # 查找 BaseTool 子类
                for name, obj in inspect.getmembers(mod, inspect.isclass):
                    if issubclass(obj, BaseTool) and obj != BaseTool:
                        tools.append(obj())

        return tools
```

### 5.3 工具组合

```python
class ComposedTool(BaseTool):
    """
    组合工具
    将多个工具组合成一个新工具
    """

    def __init__(self, name: str, tools: List[BaseTool]):
        super().__init__()
        self.name = name
        self.tools = tools

    def execute(self, **kwargs) -> Any:
        """
        顺序执行所有子工具
        """
        result = kwargs

        for tool in self.tools:
            result = tool.execute(**result)

        return result

# 示例:组合工具
news_pipeline = ComposedTool(
    name="news_pipeline",
    tools=[
        HotNewsScraperTool(),
        KeywordMatcherTool(),
        AIAnalyzerTool()
    ]
)
```

---

## 6. 数据流设计

### 6.1 数据流向

```
┌─────────────────────────────────────────────────────────┐
│                     完整数据流                           │
└─────────────────────────────────────────────────────────┘

1. 用户请求 (UserRequest)
   ↓
2. Orchestrator 规划 (ExecutionPlan)
   ↓
3. CrawlerAgent 采集 (RawData)
   ├─ HotNewsScraperTool → List[NewsItem]
   ├─ RSSFetcherTool → List[RSSItem]
   └─ Storage: SQLite 保存
   ↓
4. AnalyzerAgent 分析 (AnalyzedData)
   ├─ KeywordMatcherTool → Filtered Data
   ├─ TrendDetectorTool → Trends
   ├─ AIAnalyzerTool → Insights
   └─ Storage: 保存分析结果
   ↓
5. ReporterAgent 报告 (Report)
   ├─ 格式化数据
   ├─ 生成 HTML/Markdown
   └─ Storage: 保存报告
   ↓
6. NotifierAgent 推送 (NotificationResult)
   ├─ FeishuNotifierTool
   ├─ DingTalkNotifierTool
   └─ TelegramNotifierTool
   ↓
7. 完成 (FinalResult)
```

### 6.2 数据模型

```python
# 原始数据
@dataclass
class NewsItem:
    title: str
    source_id: str
    rank: int
    url: str
    timestamp: datetime

@dataclass
class RSSItem:
    title: str
    feed_id: str
    url: str
    published_at: datetime
    summary: str

# 分析结果
@dataclass
class AnalysisResult:
    keyword_stats: List[KeywordStat]
    trends: List[Trend]
    insights: AIInsights

# 报告
@dataclass
class Report:
    title: str
    content: str
    format: str  # html, markdown, json
    metadata: Dict

# 通知结果
@dataclass
class NotificationResult:
    channel: str
    success: bool
    message: str
```

---

## 7. 扩展机制

### 7.1 添加新的数据源

```python
# Step 1: 实现数据源工具
class MyDataSourceTool(BaseTool):
    def __init__(self):
        super().__init__()
        self.name = "my_data_source"
        self.description = "My custom data source"

    def execute(self, **kwargs) -> List[NewsItem]:
        # 实现数据采集逻辑
        return []

# Step 2: 注册工具
registry.register(MyDataSourceTool(), "data_source")

# Step 3: 在配置中启用
# config/config.yaml
data_sources:
  - type: "my_data_source"
    enabled: true
    params:
      api_url: "https://..."
```

### 7.2 添加新的分析能力

```python
# Step 1: 实现分析工具
class SentimentAnalyzerTool(BaseTool):
    def __init__(self):
        super().__init__()
        self.name = "sentiment_analyzer"
        self.description = "Analyze sentiment of news"

    def execute(self, data: List[NewsItem]) -> List[SentimentResult]:
        # 实现情感分析逻辑
        return []

# Step 2: 注册工具
registry.register(SentimentAnalyzerTool(), "analyzer")

# Step 3: 在 AnalyzerAgent 中使用
class AnalyzerAgent(BaseAgent):
    def execute(self, task: Task) -> Result:
        # ...
        sentiment = self.call_tool("sentiment_analyzer", data=data)
        # ...
```

### 7.3 添加新的 Agent

```python
# Step 1: 继承 BaseAgent
class CustomAgent(BaseAgent):
    def __init__(self):
        super().__init__("CustomAgent")

    def plan(self, task: Task) -> List[Action]:
        # 规划步骤
        return []

    def execute(self, task: Task) -> Result:
        # 执行任务
        return Result(success=True, data={})

# Step 2: 注册 Agent
harness.register_agent("custom", CustomAgent)

# Step 3: 在任务中使用
task = Task(type="custom_task", agent="custom")
result = harness.run(task)
```

---

## 8. 实施路线图

### Phase 1: 核心框架 (2-3周)

```
Week 1: 基础框架
├─ BaseAgent 基类
├─ BaseTool 基类
├─ ToolRegistry 工具注册表
├─ Context 上下文管理
└─ Orchestrator 编排器

Week 2: 工具层实现
├─ HotNewsScraperTool
├─ RSSFetcherTool
├─ KeywordMatcherTool
├─ SQLiteStorageTool
└─ FeishuNotifierTool

Week 3: Agent 层实现
├─ CrawlerAgent
├─ AnalyzerAgent
├─ NotifierAgent
└─ 集成测试
```

### Phase 2: 高级功能 (2-3周)

```
Week 4: AI 能力
├─ AIAnalyzerTool
├─ TrendDetectorTool
├─ SentimentAnalyzerTool
└─ Prompt 管理

Week 5: 监控和调度
├─ MonitorAgent
├─ SchedulerAgent
├─ TimerTool
└─ 告警机制

Week 6: 优化和完善
├─ 性能优化
├─ 错误处理
├─ 日志和监控
└─ 文档完善
```

### Phase 3: 生态建设 (持续)

```
- 工具市场（社区贡献工具）
- Agent 模板库
- 配置可视化编辑器
- Web 管理界面
```

---

## 9. 示例：完整流程

### 9.1 配置 Agent 系统

```yaml
# config/agent_config.yaml

agents:
  crawler:
    class: "CrawlerAgent"
    tools:
      - hot_news_scraper
      - rss_fetcher
      - sqlite_storage

  analyzer:
    class: "AnalyzerAgent"
    tools:
      - keyword_matcher
      - trend_detector
      - ai_analyzer

  notifier:
    class: "NotifierAgent"
    tools:
      - feishu_notifier
      - dingtalk_notifier
      - telegram_notifier

workflows:
  news_monitor:
    name: "新闻监控"
    schedule: "1h"
    steps:
      - agent: "crawler"
        task: "采集数据"
        params:
          platforms: ["zhihu", "weibo"]

      - agent: "analyzer"
        task: "分析数据"
        params:
          keywords: ["AI", "芯片", "新能源"]

      - agent: "notifier"
        task: "推送通知"
        params:
          channels: ["feishu"]
```

### 9.2 启动系统

```python
# main.py

from trendradar.agent import AgentHarness, ToolRegistry
from trendradar.agent.agents import CrawlerAgent, AnalyzerAgent, NotifierAgent
from trendradar.agent.tools import (
    HotNewsScraperTool,
    KeywordMatcherTool,
    FeishuNotifierTool
)

# 1. 初始化
harness = AgentHarness()
registry = ToolRegistry()

# 2. 注册工具
registry.register(HotNewsScraperTool(), "data_source")
registry.register(KeywordMatcherTool(), "analyzer")
registry.register(FeishuNotifierTool(), "notifier")

# 3. 注册 Agent
harness.register_agent("crawler", CrawlerAgent)
harness.register_agent("analyzer", AnalyzerAgent)
harness.register_agent("notifier", NotifierAgent)

# 4. 加载配置
config = load_config("config/agent_config.yaml")
workflow = config["workflows"]["news_monitor"]

# 5. 执行工作流
result = harness.run_workflow(workflow)

print(f"执行结果: {result}")
```

### 9.3 添加自定义工具

```python
# custom_tool.py

from trendradar.agent.tools import BaseTool

class MyCustomTool(BaseTool):
    """自定义工具"""

    def __init__(self):
        super().__init__()
        self.name = "my_custom_tool"
        self.description = "My custom tool for special tasks"

    def execute(self, **kwargs):
        # 实现自定义逻辑
        return "Custom result"

# 注册到系统
registry.register(MyCustomTool(), "custom")
```

---

## 10. 总结

### 10.1 核心优势

```
✓ 模块化设计
  - 每个模块职责单一
  - 易于理解和维护

✓ 可扩展性强
  - 工具插件化
  - Agent 可自由组合

✓ 易于使用
  - 配置驱动
  - 声明式 API

✓ 生产就绪
  - 错误处理完善
  - 监控和日志齐全
```

### 10.2 与现有系统的集成

```
现有 TrendRadar 模块 → Agent 工具

crawler/fetcher.py     → HotNewsScraperTool
crawler/rss/          → RSSFetcherTool
core/analyzer.py      → KeywordMatcherTool
ai/analyzer.py        → AIAnalyzerTool
notification/senders  → NotificationTools
storage/              → StorageTools

优势:
- 复用现有代码
- 渐进式迁移
- 向后兼容
```

### 10.3 未来展望

```
1. AI Agent 自主决策
   - 根据用户行为学习
   - 自动优化推送策略

2. 分布式 Agent
   - 多节点协作
   - 负载均衡

3. Agent 市场
   - 社区贡献 Agent
   - 一键安装

4. 可视化编排
   - 拖拽式配置
   - 实时预览
```

---

**文档版本**: v1.0
**更新日期**: 2026-04-20
**作者**: Claude Code AI Assistant

---

## 附录 A: 代码结构

```
TrendRadar/
├── trendradar/
│   ├── agent/                    # 【新增】Agent 系统
│   │   ├── __init__.py
│   │   ├── base.py               # BaseAgent 基类
│   │   ├── harness.py            # AgentHarness 编排器
│   │   ├── context.py            # Context 上下文
│   │   ├── orchestrator.py       # Orchestrator 编排器
│   │   │
│   │   ├── agents/               # Agent 实现
│   │   │   ├── __init__.py
│   │   │   ├── crawler.py        # CrawlerAgent
│   │   │   ├── analyzer.py       # AnalyzerAgent
│   │   │   ├── notifier.py       # NotifierAgent
│   │   │   ├── monitor.py        # MonitorAgent
│   │   │   └── reporter.py       # ReporterAgent
│   │   │
│   │   └── tools/                # 工具实现
│   │       ├── __init__.py
│   │       ├── base.py           # BaseTool 基类
│   │       ├── registry.py       # ToolRegistry
│   │       ├── discovery.py      # ToolDiscovery
│   │       │
│   │       ├── data_sources/     # 数据源工具
│   │       │   ├── hot_news_scraper.py
│   │       │   ├── rss_fetcher.py
│   │       │   └── api_data.py
│   │       │
│   │       ├── analyzers/        # 分析工具
│   │       │   ├── keyword_matcher.py
│   │       │   ├── trend_detector.py
│   │       │   ├── sentiment_analyzer.py
│   │       │   └── ai_analyzer.py
│   │       │
│   │       ├── notifiers/        # 通知工具
│   │       │   ├── feishu.py
│   │       │   ├── dingtalk.py
│   │       │   └── telegram.py
│   │       │
│   │       ├── storage/          # 存储工具
│   │       │   ├── sqlite.py
│   │       │   └── s3.py
│   │       │
│   │       └── utils/            # 实用工具
│   │           ├── timer.py
│   │           ├── filter.py
│   │           └── transform.py
│   │
│   ├── core/                     # 【保留】核心业务逻辑
│   ├── crawler/                  # 【保留】爬虫模块
│   ├── ai/                       # 【保留】AI 模块
│   ├── notification/             # 【保留】通知模块
│   ├── storage/                  # 【保留】存储模块
│   └── report/                   # 【保留】报告模块
│
├── config/
│   ├── config.yaml               # 【保留】原有配置
│   └── agent_config.yaml         # 【新增】Agent 配置
│
├── examples/
│   ├── basic_agent.py            # 基础 Agent 示例
│   ├── custom_tool.py            # 自定义工具示例
│   └── workflow.py               # 工作流示例
│
└── docs/
    ├── AGENT_SYSTEM_DESIGN.md    # 本文档
    └── AGENT_API_REFERENCE.md    # API 参考文档
```
