"""
Context 上下文管理

负责在 Agent 之间传递状态和数据
"""

import time
from typing import Any, Dict, List, Tuple
from dataclasses import dataclass, field


@dataclass
class ContextSnapshot:
    """上下文快照"""
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    timestamp: float


class Context:
    """
    执行上下文

    在 Agent 之间传递状态和数据
    支持数据存取、历史追踪、快照保存
    """

    def __init__(self):
        """初始化上下文"""
        self.data: Dict[str, Any] = {}
        self.metadata: Dict[str, Any] = {}
        self.history: List[Tuple[str, str, Any]] = []
        self._snapshots: List[ContextSnapshot] = []

    def set(self, key: str, value: Any):
        """
        设置上下文数据

        Args:
            key: 键
            value: 值
        """
        self.data[key] = value
        self.history.append(("set", key, value))

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取上下文数据

        Args:
            key: 键
            default: 默认值

        Returns:
            值
        """
        return self.data.get(key, default)

    def update(self, updates: Dict[str, Any]):
        """
        批量更新数据

        Args:
            updates: 更新字典
        """
        self.data.update(updates)
        self.history.append(("update", "", updates))

    def delete(self, key: str):
        """
        删除数据

        Args:
            key: 键
        """
        if key in self.data:
            value = self.data.pop(key)
            self.history.append(("delete", key, value))

    def has(self, key: str) -> bool:
        """
        检查键是否存在

        Args:
            key: 键

        Returns:
            是否存在
        """
        return key in self.data

    def clear(self):
        """清空上下文"""
        self.data.clear()
        self.history.append(("clear", "", None))

    def snapshot(self) -> ContextSnapshot:
        """
        保存快照

        Returns:
            快照对象
        """
        snapshot = ContextSnapshot(
            data=self.data.copy(),
            metadata=self.metadata.copy(),
            timestamp=time.time()
        )
        self._snapshots.append(snapshot)
        return snapshot

    def restore(self, snapshot: ContextSnapshot):
        """
        恢复快照

        Args:
            snapshot: 快照对象
        """
        self.data = snapshot.data.copy()
        self.metadata = snapshot.metadata.copy()
        self.history.append(("restore", "", snapshot.timestamp))

    def get_history(self) -> List[Tuple[str, str, Any]]:
        """
        获取历史记录

        Returns:
            历史记录列表
        """
        return self.history.copy()

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典

        Returns:
            字典表示
        """
        return {
            "data": self.data,
            "metadata": self.metadata,
            "history_count": len(self.history),
            "snapshots_count": len(self._snapshots)
        }

    def __repr__(self) -> str:
        """字符串表示"""
        return f"Context(keys={list(self.data.keys())}, history={len(self.history)})"


class ContextManager:
    """
    上下文管理器

    管理多个上下文实例
    支持命名空间隔离
    """

    def __init__(self):
        """初始化管理器"""
        self.contexts: Dict[str, Context] = {}
        self.default_context = Context()

    def create_context(self, name: str) -> Context:
        """
        创建新上下文

        Args:
            name: 上下文名称

        Returns:
            上下文对象
        """
        if name in self.contexts:
            raise ValueError(f"Context {name} already exists")

        context = Context()
        self.contexts[name] = context
        return context

    def get_context(self, name: str = None) -> Context:
        """
        获取上下文

        Args:
            name: 上下文名称，如果为 None 返回默认上下文

        Returns:
            上下文对象
        """
        if name is None:
            return self.default_context

        if name not in self.contexts:
            raise ValueError(f"Context {name} not found")

        return self.contexts[name]

    def delete_context(self, name: str):
        """
        删除上下文

        Args:
            name: 上下文名称
        """
        if name in self.contexts:
            del self.contexts[name]

    def list_contexts(self) -> List[str]:
        """
        列出所有上下文

        Returns:
            上下文名称列表
        """
        return list(self.contexts.keys())

    def clear_all(self):
        """清空所有上下文"""
        self.contexts.clear()
        self.default_context.clear()
