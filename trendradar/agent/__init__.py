"""
TrendRadar Agent System

基于 Claude Code 架构思想的模块化 Agent 系统
"""

from .base import BaseAgent, Task, Result, Action, ActionResult
from .context import Context, ContextManager
from .harness import AgentHarness

__all__ = [
    "BaseAgent",
    "Task",
    "Result",
    "Action",
    "ActionResult",
    "Context",
    "ContextManager",
    "AgentHarness",
]
