"""
AnalyzerAgent - 分析 Agent

负责数据分析任务
"""

from typing import List

from ..base import BaseAgent, Task, Result, Action, ActionType


class AnalyzerAgent(BaseAgent):
    """
    分析 Agent

    负责分析新闻数据
    """

    def __init__(self):
        """初始化分析 Agent"""
        super().__init__("AnalyzerAgent")

    def plan(self, task: Task) -> List[Action]:
        """
        规划分析步骤

        Args:
            task: 任务对象，预期参数:
                - data: 待分析数据
                - keywords: 关键词列表
                - enable_ai: 是否启用 AI 分析

        Returns:
            动作列表

        Example:
            task = Task(
                type="analyze_data",
                params={
                    "keywords": ["AI", "芯片"],
                    "enable_ai": True
                }
            )
            →
            [
                Action("use_tool", "keyword_matcher", {"keywords": ["AI", "芯片"]}),
                Action("use_tool", "trend_detector"),
                Action("use_tool", "ai_analyzer")
            ]
        """
        actions = []

        # 1. 关键词过滤
        keywords = task.params.get("keywords", [])
        if keywords:
            actions.append(Action(
                type=ActionType.USE_TOOL.value,
                tool="keyword_matcher",
                params={"keywords": keywords}
            ))

        # 2. 趋势检测
        if task.params.get("enable_trend_detection", True):
            actions.append(Action(
                type=ActionType.USE_TOOL.value,
                tool="trend_detector",
                params={}
            ))

        # 3. AI 分析
        if task.params.get("enable_ai", False):
            actions.append(Action(
                type=ActionType.USE_TOOL.value,
                tool="ai_analyzer",
                params={}
            ))

        return actions

    def execute(self, task: Task) -> Result:
        """
        执行分析任务

        Args:
            task: 任务对象

        Returns:
            执行结果
        """
        self.log("Starting data analysis")

        try:
            # 1. 加载数据
            data = task.params.get("data")
            if not data and self.context:
                # 从上下文获取数据
                data = self.context.get("crawled_data")

            if not data:
                return Result(
                    success=False,
                    error="No data to analyze"
                )

            self.log(f"Loaded data: {len(data) if isinstance(data, list) else 'N/A'} items")

            # 2. Planning: 规划步骤
            actions = self.plan(task)
            self.log(f"Planned {len(actions)} actions")

            # 3. Execution: 执行步骤
            current_data = data
            results = {}

            for i, action in enumerate(actions):
                self.log(f"Executing action {i+1}/{len(actions)}: {action.tool}")
                try:
                    # 将当前数据作为输入
                    action.params["data"] = current_data

                    result = self.execute_action(action)

                    # 保存结果
                    results[action.tool] = result.data

                    # 更新当前数据（用于下一步）
                    if result.success and result.data:
                        current_data = result.data

                except Exception as e:
                    self.handle_error(e)
                    results[action.tool] = {"error": str(e)}

            # 4. 聚合结果
            final_result = Result(
                success=True,
                data={
                    "filtered_data": results.get("keyword_matcher"),
                    "trends": results.get("trend_detector"),
                    "insights": results.get("ai_analyzer")
                }
            )

            # 5. Reflection: 反思
            reflection = self.reflect(final_result)
            final_result.reflection = reflection

            return final_result

        except Exception as e:
            self.log(f"Execution failed: {str(e)}", level="error")
            return Result(
                success=False,
                error=str(e)
            )
