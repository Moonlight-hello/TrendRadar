"""
CrawlerAgent - 爬虫 Agent

负责数据采集任务
"""

from typing import List

from ..base import BaseAgent, Task, Result, Action, ActionType


class CrawlerAgent(BaseAgent):
    """
    爬虫 Agent

    负责采集新闻数据
    """

    def __init__(self):
        """初始化爬虫 Agent"""
        super().__init__("CrawlerAgent")

    def plan(self, task: Task) -> List[Action]:
        """
        规划爬取步骤

        Args:
            task: 任务对象，预期参数:
                - data_sources: 数据源列表
                - storage: 存储方式

        Returns:
            动作列表

        Example:
            task = Task(
                type="collect_data",
                params={
                    "data_sources": ["zhihu", "weibo"],
                    "storage": "sqlite"
                }
            )
            →
            [
                Action("use_tool", "hot_news_scraper", {"platform": "zhihu"}),
                Action("use_tool", "hot_news_scraper", {"platform": "weibo"}),
                Action("use_tool", "sqlite_storage", {"operation": "save"})
            ]
        """
        actions = []

        # 获取数据源列表
        data_sources = task.params.get("data_sources", [])

        # 为每个数据源创建采集动作
        for source in data_sources:
            if source.get("type") == "hot_news":
                actions.append(Action(
                    type=ActionType.USE_TOOL.value,
                    tool="hot_news_scraper",
                    params={"platform": source.get("platform")}
                ))
            elif source.get("type") == "rss":
                actions.append(Action(
                    type=ActionType.USE_TOOL.value,
                    tool="rss_fetcher",
                    params={"feed_url": source.get("url")}
                ))

        # 保存数据
        storage = task.params.get("storage", "sqlite")
        actions.append(Action(
            type=ActionType.USE_TOOL.value,
            tool=f"{storage}_storage",
            params={"operation": "save"}
        ))

        return actions

    def execute(self, task: Task) -> Result:
        """
        执行爬取任务

        Args:
            task: 任务对象

        Returns:
            执行结果
        """
        self.log("Starting data collection")

        try:
            # Planning: 规划步骤
            actions = self.plan(task)
            self.log(f"Planned {len(actions)} actions")

            # Execution: 执行步骤
            results = []
            for i, action in enumerate(actions):
                self.log(f"Executing action {i+1}/{len(actions)}: {action.tool}")
                try:
                    result = self.execute_action(action)
                    results.append(result)

                    # 如果是采集动作，保存结果到上下文
                    if action.tool in ["hot_news_scraper", "rss_fetcher"]:
                        key = f"{action.tool}_{action.params.get('platform', 'data')}"
                        if self.context:
                            self.context.set(key, result.data)

                except Exception as e:
                    self.handle_error(e)
                    results.append({
                        "success": False,
                        "error": str(e),
                        "action": action.tool
                    })

            # 判断是否所有动作都成功
            success = all(r.success if hasattr(r, 'success') else r.get("success", False) for r in results)

            # Reflection: 反思
            result = Result(
                success=success,
                data={"crawled_data": results, "action_count": len(actions)}
            )
            reflection = self.reflect(result)

            result.reflection = reflection
            return result

        except Exception as e:
            self.log(f"Execution failed: {str(e)}", level="error")
            return Result(
                success=False,
                error=str(e)
            )
