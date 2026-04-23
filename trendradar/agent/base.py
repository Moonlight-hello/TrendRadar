"""
BaseAgent 基类和核心数据结构
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum


class TaskType(Enum):
    """任务类型"""
    COLLECT_DATA = "collect_data"
    ANALYZE_DATA = "analyze_data"
    GENERATE_REPORT = "generate_report"
    NOTIFY = "notify"
    MONITOR = "monitor"
    CUSTOM = "custom"


class ActionType(Enum):
    """动作类型"""
    USE_TOOL = "use_tool"
    CALL_AGENT = "call_agent"
    WAIT = "wait"
    CUSTOM = "custom"


@dataclass
class Task:
    """
    任务定义
    """
    type: str
    params: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0
    timeout: Optional[int] = None
    retry: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Action:
    """
    动作定义
    """
    type: str
    tool: Optional[str] = None
    agent: Optional[str] = None
    params: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ActionResult:
    """
    动作执行结果
    """
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Reflection:
    """
    反思结果
    """
    success: bool
    lessons: List[str] = field(default_factory=list)
    improvements: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Result:
    """
    任务执行结果
    """
    success: bool
    data: Any = None
    error: Optional[str] = None
    reflection: Optional[Reflection] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseAgent(ABC):
    """
    Agent 基类

    所有 Agent 必须继承此类并实现 plan() 和 execute() 方法

    三层架构:
    1. Planning: plan() - 规划执行步骤
    2. Execution: execute() - 执行任务
    3. Reflection: reflect() - 反思和优化
    """

    def __init__(self, name: str):
        """
        初始化 Agent

        Args:
            name: Agent 名称
        """
        self.name = name
        self.context = None
        self.tools = []
        self.logger = None

    def set_context(self, context):
        """
        设置执行上下文

        Args:
            context: Context 对象
        """
        self.context = context

    def register_tools(self, tools: List):
        """
        注册工具

        Args:
            tools: 工具列表
        """
        self.tools = tools

    def set_logger(self, logger):
        """
        设置日志记录器

        Args:
            logger: Logger 对象
        """
        self.logger = logger

    @abstractmethod
    def plan(self, task: Task) -> List[Action]:
        """
        规划执行步骤

        这是三层架构的第一层：Planning
        负责将任务拆解为一系列动作

        Args:
            task: 任务对象

        Returns:
            动作列表
        """
        pass

    @abstractmethod
    def execute(self, task: Task) -> Result:
        """
        执行任务

        这是三层架构的第二层：Execution
        负责执行具体的任务逻辑

        典型流程:
        1. 调用 plan() 规划步骤
        2. 执行每个动作
        3. 收集结果
        4. 调用 reflect() 反思

        Args:
            task: 任务对象

        Returns:
            执行结果
        """
        pass

    def reflect(self, result: Result) -> Reflection:
        """
        反思执行结果

        这是三层架构的第三层：Reflection
        负责评估结果、总结经验、优化策略

        Args:
            result: 执行结果

        Returns:
            反思结果
        """
        lessons = []
        improvements = []

        if result.success:
            lessons.append(f"{self.name} 成功完成任务")
        else:
            lessons.append(f"{self.name} 任务失败: {result.error}")
            improvements.append("检查错误原因并优化")

        return Reflection(
            success=result.success,
            lessons=lessons,
            improvements=improvements
        )

    def call_tool(self, tool_name: str, **kwargs) -> Any:
        """
        调用工具

        Args:
            tool_name: 工具名称
            **kwargs: 工具参数

        Returns:
            工具执行结果

        Raises:
            ToolNotFoundError: 工具不存在
        """
        tool = self.find_tool(tool_name)
        if not tool:
            raise ToolNotFoundError(f"Tool {tool_name} not found")

        self.log(f"Calling tool: {tool_name}")
        return tool.execute(**kwargs)

    def find_tool(self, tool_name: str):
        """
        查找工具

        Args:
            tool_name: 工具名称

        Returns:
            工具对象，如果不存在返回 None
        """
        for tool in self.tools:
            if tool.name == tool_name:
                return tool
        return None

    def execute_action(self, action: Action) -> ActionResult:
        """
        执行单个动作

        Args:
            action: 动作对象

        Returns:
            动作执行结果
        """
        try:
            if action.type == ActionType.USE_TOOL.value:
                result = self.call_tool(action.tool, **action.params)
                return ActionResult(success=True, data=result)
            elif action.type == ActionType.CALL_AGENT.value:
                # TODO: 实现 Agent 调用
                return ActionResult(success=False, error="Agent call not implemented")
            else:
                return ActionResult(success=False, error=f"Unknown action type: {action.type}")
        except Exception as e:
            return ActionResult(success=False, error=str(e))

    def handle_error(self, error: Exception):
        """
        处理错误

        Args:
            error: 异常对象
        """
        self.log(f"Error in {self.name}: {str(error)}", level="error")

    def log(self, message: str, level: str = "info"):
        """
        记录日志

        Args:
            message: 日志消息
            level: 日志级别 (info, warning, error)
        """
        if self.logger:
            getattr(self.logger, level)(f"[{self.name}] {message}")
        else:
            print(f"[{level.upper()}] [{self.name}] {message}")


class ToolNotFoundError(Exception):
    """工具未找到异常"""
    pass


class AgentExecutionError(Exception):
    """Agent 执行异常"""
    pass
