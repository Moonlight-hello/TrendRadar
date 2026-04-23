"""
BaseTool 工具基类
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseTool(ABC):
    """
    工具基类

    所有工具必须继承此类并实现 execute() 方法
    """

    def __init__(self):
        """初始化工具"""
        self.name: str = ""
        self.description: str = ""
        self.parameters: Dict[str, Any] = {}
        self.category: str = "general"

    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """
        执行工具

        Args:
            **kwargs: 工具参数

        Returns:
            执行结果
        """
        pass

    def validate_params(self, **kwargs) -> bool:
        """
        验证参数

        Args:
            **kwargs: 参数字典

        Returns:
            是否有效

        Raises:
            ValueError: 参数无效
        """
        for param_name, param_spec in self.parameters.items():
            # 检查必需参数
            if param_spec.get("required", False):
                if param_name not in kwargs:
                    raise ValueError(f"Missing required parameter: {param_name}")

            # 检查类型
            if param_name in kwargs:
                expected_type = param_spec.get("type")
                actual_value = kwargs[param_name]

                # 简单的类型检查
                if expected_type == "string" and not isinstance(actual_value, str):
                    raise ValueError(f"Parameter {param_name} must be string")
                elif expected_type == "integer" and not isinstance(actual_value, int):
                    raise ValueError(f"Parameter {param_name} must be integer")
                elif expected_type == "array" and not isinstance(actual_value, list):
                    raise ValueError(f"Parameter {param_name} must be array")
                elif expected_type == "object" and not isinstance(actual_value, dict):
                    raise ValueError(f"Parameter {param_name} must be object")

        return True

    def get_metadata(self) -> Dict[str, Any]:
        """
        获取工具元数据

        Returns:
            元数据字典
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "category": self.category
        }

    def __repr__(self) -> str:
        """字符串表示"""
        return f"Tool(name={self.name}, category={self.category})"


class ComposedTool(BaseTool):
    """
    组合工具

    将多个工具组合成一个新工具
    按顺序执行所有子工具
    """

    def __init__(self, name: str, tools: list):
        """
        初始化组合工具

        Args:
            name: 工具名称
            tools: 子工具列表
        """
        super().__init__()
        self.name = name
        self.description = f"Composed tool: {name}"
        self.tools = tools

    def execute(self, **kwargs) -> Any:
        """
        顺序执行所有子工具

        Args:
            **kwargs: 初始参数

        Returns:
            最后一个工具的结果
        """
        result = kwargs

        for tool in self.tools:
            # 如果上一个工具返回字典，作为下一个工具的参数
            if isinstance(result, dict):
                result = tool.execute(**result)
            else:
                result = tool.execute(data=result)

        return result


class ToolError(Exception):
    """工具执行异常"""
    pass
