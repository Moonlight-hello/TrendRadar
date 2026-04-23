"""
TrendRadar Agent System Demo

演示如何使用 Agent 系统
"""

import logging
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from trendradar.agent import AgentHarness, Task
from trendradar.agent.agents import CrawlerAgent, AnalyzerAgent
from trendradar.agent.tools.data_sources import HotNewsScraperTool, RSSFetcherTool


def setup_logging():
    """配置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)


def demo_basic_usage():
    """
    演示基本用法

    1. 初始化 AgentHarness
    2. 注册工具
    3. 注册 Agent
    4. 执行任务
    """
    logger = setup_logging()
    logger.info("=== Demo 1: Basic Usage ===")

    # 1. 初始化编排器
    harness = AgentHarness(logger=logger)

    # 2. 注册工具
    harness.register_tool(HotNewsScraperTool(), "data_source")
    harness.register_tool(RSSFetcherTool(), "data_source")

    # 3. 注册 Agent
    harness.register_agent("crawler", CrawlerAgent)

    # 4. 创建任务
    task = Task(
        type="collect_data",
        params={
            "data_sources": [
                {"type": "hot_news", "platform": "zhihu"},
                {"type": "hot_news", "platform": "weibo"}
            ],
            "storage": "sqlite"
        }
    )

    # 5. 执行任务
    result = harness.run(task, agent_name="crawler")

    # 6. 查看结果
    logger.info(f"Task result: success={result.success}")
    if result.success:
        logger.info(f"Crawled data: {result.data}")
    else:
        logger.error(f"Task failed: {result.error}")

    return result


def demo_workflow():
    """
    演示工作流

    演示多个 Agent 协作完成复杂任务
    """
    logger = setup_logging()
    logger.info("=== Demo 2: Workflow ===")

    # 1. 初始化编排器
    harness = AgentHarness(logger=logger)

    # 2. 注册工具
    harness.register_tool(HotNewsScraperTool(), "data_source")

    # 3. 注册 Agent
    harness.register_agent("crawler", CrawlerAgent)
    harness.register_agent("analyzer", AnalyzerAgent)

    # 4. 定义工作流
    workflow = [
        {
            "agent": "crawler",
            "task": {
                "type": "collect_data",
                "params": {
                    "data_sources": [
                        {"type": "hot_news", "platform": "zhihu"}
                    ]
                }
            },
            "result_key": "crawled_data"
        },
        {
            "agent": "analyzer",
            "task": {
                "type": "analyze_data",
                "params": {
                    "keywords": ["AI", "人工智能", "芯片"],
                    "enable_trend_detection": True
                }
            },
            "result_key": "analysis_result"
        }
    ]

    # 5. 执行工作流
    results = harness.run_workflow(workflow)

    # 6. 查看结果
    for i, result in enumerate(results):
        logger.info(f"Step {i+1} result: success={result.success}")
        if result.reflection:
            logger.info(f"Reflection: {result.reflection.lessons}")

    return results


def demo_custom_tool():
    """
    演示自定义工具

    展示如何创建和注册自定义工具
    """
    logger = setup_logging()
    logger.info("=== Demo 3: Custom Tool ===")

    # 1. 定义自定义工具
    from trendradar.agent.tools.base import BaseTool

    class EchoTool(BaseTool):
        """示例工具：回显输入"""

        def __init__(self):
            super().__init__()
            self.name = "echo_tool"
            self.description = "Echo the input message"
            self.parameters = {
                "message": {
                    "type": "string",
                    "required": True,
                    "description": "Message to echo"
                }
            }

        def execute(self, message: str, **kwargs):
            self.validate_params(message=message)
            return f"Echo: {message}"

    # 2. 初始化编排器
    harness = AgentHarness(logger=logger)

    # 3. 注册自定义工具
    harness.register_tool(EchoTool(), "utility")

    # 4. 查看注册的工具
    tools = harness.tool_registry.list_tools()
    logger.info(f"Registered tools: {tools}")

    # 5. 获取工具元数据
    metadata = harness.tool_registry.get_metadata("echo_tool")
    logger.info(f"Echo tool metadata: {metadata}")


def demo_context_management():
    """
    演示上下文管理

    展示如何在 Agent 之间传递数据
    """
    logger = setup_logging()
    logger.info("=== Demo 4: Context Management ===")

    from trendradar.agent import Context

    # 1. 创建上下文
    context = Context()

    # 2. 设置数据
    context.set("user_name", "Alice")
    context.set("preferences", {"language": "zh", "theme": "dark"})

    # 3. 获取数据
    name = context.get("user_name")
    prefs = context.get("preferences")
    logger.info(f"User: {name}, Preferences: {prefs}")

    # 4. 更新数据
    context.update({"last_login": "2026-04-20"})

    # 5. 保存快照
    snapshot = context.snapshot()
    logger.info(f"Snapshot saved at {snapshot.timestamp}")

    # 6. 修改数据
    context.set("user_name", "Bob")
    logger.info(f"Modified user: {context.get('user_name')}")

    # 7. 恢复快照
    context.restore(snapshot)
    logger.info(f"Restored user: {context.get('user_name')}")

    # 8. 查看历史
    history = context.get_history()
    logger.info(f"Context history: {len(history)} operations")


def main():
    """主函数"""
    print("TrendRadar Agent System Demo")
    print("=" * 60)

    try:
        # Demo 1: 基本用法
        print("\n1. Basic Usage Demo")
        print("-" * 60)
        # demo_basic_usage()  # 需要实际的爬虫功能，这里注释掉

        # Demo 2: 工作流
        print("\n2. Workflow Demo")
        print("-" * 60)
        # demo_workflow()  # 需要实际的爬虫功能，这里注释掉

        # Demo 3: 自定义工具
        print("\n3. Custom Tool Demo")
        print("-" * 60)
        demo_custom_tool()

        # Demo 4: 上下文管理
        print("\n4. Context Management Demo")
        print("-" * 60)
        demo_context_management()

        print("\n" + "=" * 60)
        print("All demos completed successfully!")

    except Exception as e:
        print(f"\nError: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
