# TrendRadar Agent System - 快速开始

## 📚 简介

TrendRadar Agent System 是基于 Claude Code 架构思想设计的模块化 Agent 系统。它将 TrendRadar 的各项功能重构为可插拔的工具和专业化的 Agent，提供更灵活、更强大的自动化能力。

## 🎯 核心特性

- **三层架构**: Planning → Execution → Reflection
- **模块化设计**: Agent + Tool + Context 清晰分离
- **可扩展性**: 轻松添加新工具和新 Agent
- **工作流编排**: 支持复杂的多步骤任务
- **上下文管理**: Agent 之间无缝传递数据

## 🚀 快速开始

### 1. 基本用法

```python
from trendradar.agent import AgentHarness, Task
from trendradar.agent.agents import CrawlerAgent
from trendradar.agent.tools.data_sources import HotNewsScraperTool

# 1. 初始化编排器
harness = AgentHarness()

# 2. 注册工具
harness.register_tool(HotNewsScraperTool(), "data_source")

# 3. 注册 Agent
harness.register_agent("crawler", CrawlerAgent)

# 4. 创建并执行任务
task = Task(
    type="collect_data",
    params={
        "data_sources": [
            {"type": "hot_news", "platform": "zhihu"}
        ]
    }
)

result = harness.run(task, agent_name="crawler")
print(f"Success: {result.success}")
```

### 2. 工作流示例

```python
# 定义多步骤工作流
workflow = [
    {
        "agent": "crawler",
        "task": {
            "type": "collect_data",
            "params": {"data_sources": [{"type": "hot_news", "platform": "zhihu"}]}
        }
    },
    {
        "agent": "analyzer",
        "task": {
            "type": "analyze_data",
            "params": {"keywords": ["AI", "芯片"]}
        }
    },
    {
        "agent": "notifier",
        "task": {
            "type": "notify",
            "params": {"channels": ["feishu"]}
        }
    }
]

# 执行工作流
results = harness.run_workflow(workflow)
```

### 3. 自定义工具

```python
from trendradar.agent.tools.base import BaseTool

class MyCustomTool(BaseTool):
    """自定义工具"""

    def __init__(self):
        super().__init__()
        self.name = "my_tool"
        self.description = "My custom tool"
        self.parameters = {
            "input": {"type": "string", "required": True}
        }

    def execute(self, input: str, **kwargs):
        # 实现自定义逻辑
        return f"Processed: {input}"

# 注册工具
harness.register_tool(MyCustomTool(), "custom")
```

### 4. 自定义 Agent

```python
from trendradar.agent.base import BaseAgent, Task, Result, Action

class MyCustomAgent(BaseAgent):
    """自定义 Agent"""

    def __init__(self):
        super().__init__("MyCustomAgent")

    def plan(self, task: Task):
        # 规划执行步骤
        return [
            Action(type="use_tool", tool="my_tool", params={"input": "test"})
        ]

    def execute(self, task: Task) -> Result:
        # 执行任务
        actions = self.plan(task)
        results = [self.execute_action(action) for action in actions]

        return Result(
            success=True,
            data={"results": results}
        )

# 注册 Agent
harness.register_agent("my_agent", MyCustomAgent)
```

## 📁 项目结构

```
trendradar/
├── agent/                      # Agent 系统
│   ├── base.py                 # BaseAgent 基类
│   ├── context.py              # Context 上下文管理
│   ├── harness.py              # AgentHarness 编排器
│   │
│   ├── agents/                 # Agent 实现
│   │   ├── crawler.py          # 爬虫 Agent
│   │   ├── analyzer.py         # 分析 Agent
│   │   ├── notifier.py         # 通知 Agent
│   │   └── ...
│   │
│   └── tools/                  # 工具实现
│       ├── base.py             # BaseTool 基类
│       ├── registry.py         # ToolRegistry 注册表
│       │
│       ├── data_sources/       # 数据源工具
│       │   ├── hot_news_scraper.py
│       │   └── rss_fetcher.py
│       │
│       ├── analyzers/          # 分析工具
│       ├── notifiers/          # 通知工具
│       └── storage/            # 存储工具
```

## 🔧 可用的 Agent

| Agent | 功能 | 使用场景 |
|-------|------|---------|
| `CrawlerAgent` | 数据采集 | 爬取新闻、RSS 订阅 |
| `AnalyzerAgent` | 数据分析 | 关键词过滤、趋势检测 |
| `NotifierAgent` | 通知推送 | 多渠道消息推送 |
| `MonitorAgent` | 持续监控 | 定时采集和告警 |
| `ReporterAgent` | 报告生成 | 生成分析报告 |

## 🛠️ 可用的工具

### 数据源工具

- `HotNewsScraperTool`: 热榜爬虫
- `RSSFetcherTool`: RSS 订阅
- `APIDataTool`: API 数据源

### 分析工具

- `KeywordMatcherTool`: 关键词匹配
- `TrendDetectorTool`: 趋势检测
- `SentimentAnalyzerTool`: 情感分析
- `AIAnalyzerTool`: AI 深度分析

### 通知工具

- `FeishuNotifierTool`: 飞书通知
- `DingTalkNotifierTool`: 钉钉通知
- `TelegramNotifierTool`: Telegram 通知
- `EmailNotifierTool`: 邮件通知

### 存储工具

- `SQLiteStorageTool`: SQLite 存储
- `S3StorageTool`: S3 对象存储

## 📖 详细文档

- [完整设计文档](AGENT_SYSTEM_DESIGN.md) - 架构设计和实现细节
- [API 参考](docs/agent_api_reference.md) - API 文档
- [示例代码](examples/agent_system_demo.py) - 完整示例

## 🤝 贡献

欢迎贡献新的工具和 Agent！

1. 实现 `BaseTool` 或 `BaseAgent`
2. 添加测试
3. 更新文档
4. 提交 PR

## 📝 许可证

与 TrendRadar 主项目保持一致

---

**更新日期**: 2026-04-20
**版本**: v1.0
