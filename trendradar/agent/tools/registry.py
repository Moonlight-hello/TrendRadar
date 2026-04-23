"""
ToolRegistry 工具注册表
"""

from typing import Dict, List, Optional

from .base import BaseTool


class ToolRegistry:
    """
    工具注册表

    管理所有可用的工具
    支持按类别分组
    """

    def __init__(self):
        """初始化注册表"""
        self.tools: Dict[str, BaseTool] = {}
        self.categories: Dict[str, List[str]] = {}

    def register(self, tool: BaseTool, category: str = "general"):
        """
        注册工具

        Args:
            tool: 工具对象
            category: 工具类别

        Example:
            registry.register(HotNewsScraperTool(), "data_source")
        """
        if tool.name in self.tools:
            raise ValueError(f"Tool {tool.name} already registered")

        self.tools[tool.name] = tool
        tool.category = category

        if category not in self.categories:
            self.categories[category] = []
        self.categories[category].append(tool.name)

    def unregister(self, tool_name: str):
        """
        注销工具

        Args:
            tool_name: 工具名称
        """
        if tool_name not in self.tools:
            return

        tool = self.tools[tool_name]
        category = tool.category

        # 从工具字典移除
        del self.tools[tool_name]

        # 从类别移除
        if category in self.categories:
            self.categories[category].remove(tool_name)
            if not self.categories[category]:
                del self.categories[category]

    def get(self, tool_name: str) -> Optional[BaseTool]:
        """
        获取工具

        Args:
            tool_name: 工具名称

        Returns:
            工具对象，如果不存在返回 None
        """
        return self.tools.get(tool_name)

    def has(self, tool_name: str) -> bool:
        """
        检查工具是否存在

        Args:
            tool_name: 工具名称

        Returns:
            是否存在
        """
        return tool_name in self.tools

    def list_tools(self, category: Optional[str] = None) -> List[str]:
        """
        列出工具名称

        Args:
            category: 类别名称，如果为 None 返回所有工具

        Returns:
            工具名称列表
        """
        if category:
            return self.categories.get(category, [])
        return list(self.tools.keys())

    def list_all(self) -> List[BaseTool]:
        """
        列出所有工具对象

        Returns:
            工具对象列表
        """
        return list(self.tools.values())

    def list_categories(self) -> List[str]:
        """
        列出所有类别

        Returns:
            类别名称列表
        """
        return list(self.categories.keys())

    def get_metadata(self, tool_name: str) -> Optional[Dict]:
        """
        获取工具元数据

        Args:
            tool_name: 工具名称

        Returns:
            元数据字典，如果不存在返回 None
        """
        tool = self.get(tool_name)
        if tool:
            return tool.get_metadata()
        return None

    def get_metadata_all(self) -> List[Dict]:
        """
        获取所有工具的元数据

        Returns:
            元数据列表
        """
        return [tool.get_metadata() for tool in self.tools.values()]

    def clear(self):
        """清空注册表"""
        self.tools.clear()
        self.categories.clear()

    def __repr__(self) -> str:
        """字符串表示"""
        return f"ToolRegistry(tools={len(self.tools)}, categories={len(self.categories)})"
