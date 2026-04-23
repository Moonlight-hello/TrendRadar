"""
AgentHarness 编排器

负责 Agent 的注册、调度和执行
"""

import logging
from typing import Any, Dict, List, Optional, Type

from .base import BaseAgent, Task, Result, AgentExecutionError
from .context import Context, ContextManager
from .tools.registry import ToolRegistry


class AgentHarness:
    """
    Agent 编排器

    核心职责:
    1. 工具注册和发现
    2. Agent 生命周期管理
    3. 上下文传递
    4. 错误处理和重试
    5. 结果聚合
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        初始化编排器

        Args:
            logger: 日志记录器
        """
        self.tool_registry = ToolRegistry()
        self.agents: Dict[str, Type[BaseAgent]] = {}
        self.agent_instances: Dict[str, BaseAgent] = {}
        self.context_manager = ContextManager()
        self.logger = logger or logging.getLogger(__name__)

    def register_tool(self, tool, category: str = "general"):
        """
        注册工具

        Args:
            tool: 工具对象
            category: 工具类别
        """
        self.tool_registry.register(tool, category)
        self.logger.info(f"Registered tool: {tool.name} in category {category}")

    def register_agent(self, agent_name: str, agent_class: Type[BaseAgent]):
        """
        注册 Agent

        Args:
            agent_name: Agent 名称
            agent_class: Agent 类
        """
        self.agents[agent_name] = agent_class
        self.logger.info(f"Registered agent: {agent_name}")

    def get_agent(self, agent_name: str) -> BaseAgent:
        """
        获取 Agent 实例

        如果实例不存在，自动创建

        Args:
            agent_name: Agent 名称

        Returns:
            Agent 实例

        Raises:
            ValueError: Agent 未注册
        """
        if agent_name not in self.agents:
            raise ValueError(f"Agent {agent_name} not registered")

        # 如果实例已存在，直接返回
        if agent_name in self.agent_instances:
            return self.agent_instances[agent_name]

        # 创建新实例
        agent_class = self.agents[agent_name]
        agent = agent_class()

        # 设置工具和日志
        tools = self.tool_registry.list_all()
        agent.register_tools(tools)
        agent.set_logger(self.logger)

        # 缓存实例
        self.agent_instances[agent_name] = agent

        return agent

    def run(self, task: Task, agent_name: Optional[str] = None, context: Optional[Context] = None) -> Result:
        """
        执行任务

        Args:
            task: 任务对象
            agent_name: Agent 名称，如果为 None 自动选择
            context: 执行上下文，如果为 None 使用默认上下文

        Returns:
            执行结果

        Raises:
            AgentExecutionError: 执行失败
        """
        try:
            # 选择 Agent
            if agent_name is None:
                agent = self.select_agent(task)
            else:
                agent = self.get_agent(agent_name)

            # 设置上下文
            if context is None:
                context = self.context_manager.get_context()
            agent.set_context(context)

            # 执行任务
            self.logger.info(f"Executing task {task.type} with agent {agent.name}")
            result = agent.execute(task)

            # 记录结果
            self.logger.info(f"Task {task.type} completed: success={result.success}")

            return result

        except Exception as e:
            self.logger.error(f"Task execution failed: {str(e)}")
            raise AgentExecutionError(f"Failed to execute task: {str(e)}") from e

    def select_agent(self, task: Task) -> BaseAgent:
        """
        自动选择合适的 Agent

        根据任务类型匹配 Agent

        Args:
            task: 任务对象

        Returns:
            Agent 实例

        Raises:
            ValueError: 无法找到合适的 Agent
        """
        # 简单的类型匹配
        agent_mapping = {
            "collect_data": "crawler",
            "analyze_data": "analyzer",
            "generate_report": "reporter",
            "notify": "notifier",
            "monitor": "monitor"
        }

        agent_name = agent_mapping.get(task.type)
        if not agent_name:
            raise ValueError(f"No agent found for task type: {task.type}")

        return self.get_agent(agent_name)

    def run_workflow(self, workflow: List[Dict[str, Any]]) -> List[Result]:
        """
        执行工作流

        Args:
            workflow: 工作流定义，格式:
                [
                    {"agent": "crawler", "task": {...}},
                    {"agent": "analyzer", "task": {...}},
                ]

        Returns:
            结果列表
        """
        results = []
        context = self.context_manager.get_context()

        for step in workflow:
            agent_name = step.get("agent")
            task_params = step.get("task", {})

            # 创建任务
            task = Task(
                type=task_params.get("type", "custom"),
                params=task_params.get("params", {}),
                priority=task_params.get("priority", 0)
            )

            # 执行任务
            result = self.run(task, agent_name, context)
            results.append(result)

            # 如果失败，是否继续
            if not result.success and not step.get("continue_on_failure", False):
                self.logger.warning(f"Workflow stopped at step {step} due to failure")
                break

            # 将结果保存到上下文
            result_key = step.get("result_key", f"step_{len(results)}_result")
            context.set(result_key, result.data)

        return results

    def shutdown(self):
        """关闭编排器，清理资源"""
        self.agent_instances.clear()
        self.context_manager.clear_all()
        self.logger.info("AgentHarness shutdown completed")
