"""
CommunitySpy 工具使用示例

演示如何使用 CommunitySpy 工具爬取股吧数据
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def demo_tool_usage():
    """演示工具用法"""
    print("=" * 60)
    print("Demo 1: 使用 CommunitySpyTool")
    print("=" * 60)

    from trendradar.agent.tools.data_sources.communityspy import CommunitySpyTool

    # 创建工具实例
    tool = CommunitySpyTool()

    # 执行爬取
    result = tool.execute(
        stock_code="301293",
        max_pages=2,
        max_posts=20,
        include_comments=True,
        delay=1.0
    )

    # 查看结果
    print(f"\n成功: {result['success']}")
    if result['success']:
        print(f"股票代码: {result['stock_code']}")
        print(f"帖子数: {result['stats']['posts_count']}")
        print(f"评论数: {result['stats']['comments_count']}")
        print(f"数据库路径: {result['db_path']}")
    else:
        print(f"错误: {result['error']}")


def demo_spider_usage():
    """演示爬虫类用法"""
    print("\n" + "=" * 60)
    print("Demo 2: 使用 EastMoneyCommentSpider")
    print("=" * 60)

    from trendradar.agent.tools.data_sources.communityspy import EastMoneyCommentSpider

    # 创建爬虫实例
    with EastMoneyCommentSpider("301293", db_path="demo_301293.db") as spider:
        print(f"\n正在爬取股票 301293 的数据...")

        # 执行爬取
        stats = spider.crawl(
            max_pages=2,
            max_posts=20,
            include_comments=True,
            delay=1.0
        )

        # 打印统计
        print(f"\n爬取完成!")
        print(f"- 帖子数量: {stats['posts_count']}")
        print(f"- 评论数量: {stats['comments_count']}")
        print(f"- 数据库: {spider.db_path}")


def demo_query_tool():
    """演示查询工具用法"""
    print("\n" + "=" * 60)
    print("Demo 3: 使用 CommunitySpyQueryTool")
    print("=" * 60)

    from trendradar.agent.tools.data_sources.communityspy import CommunitySpyQueryTool

    # 创建查询工具
    query_tool = CommunitySpyQueryTool()

    # 查询统计信息
    stats_result = query_tool.execute(
        db_path="demo_301293.db",
        query_type="stats"
    )

    if stats_result['success']:
        print(f"\n数据库统计:")
        print(f"- 帖子总数: {stats_result['stats']['posts_count']}")
        print(f"- 评论总数: {stats_result['stats']['comments_count']}")
    else:
        print(f"查询失败: {stats_result['error']}")

    # 查询最新帖子
    posts_result = query_tool.execute(
        db_path="demo_301293.db",
        query_type="posts",
        limit=5
    )

    if posts_result['success']:
        print(f"\n最新 {posts_result['count']} 条帖子:")
        for post in posts_result['data']:
            print(f"- [{post['publish_time']}] {post['title']}")
    else:
        print(f"查询失败: {posts_result['error']}")


def demo_agent_integration():
    """演示 Agent 集成用法"""
    print("\n" + "=" * 60)
    print("Demo 4: Agent 系统集成")
    print("=" * 60)

    from trendradar.agent import AgentHarness, Task
    from trendradar.agent.agents import CrawlerAgent
    from trendradar.agent.tools.data_sources.communityspy import CommunitySpyTool

    # 1. 初始化 Harness
    harness = AgentHarness()

    # 2. 注册工具和 Agent
    harness.register_tool(CommunitySpyTool(), "data_source")
    harness.register_agent("crawler", CrawlerAgent)

    # 3. 创建任务
    task = Task(
        type="collect_data",
        params={
            "data_sources": [{
                "type": "communityspy",
                "stock_code": "301293",
                "max_posts": 10
            }]
        }
    )

    # 4. 执行任务
    print("\n正在通过 Agent 系统执行爬取任务...")
    # result = harness.run(task, "crawler")
    # print(f"任务完成: success={result.success}")

    print("注意: 此示例需要完整的 Agent 工具支持")


def main():
    """主函数"""
    print("CommunitySpy 工具使用示例")
    print("=" * 60)

    try:
        # Demo 1: 工具用法
        demo_tool_usage()

        # Demo 2: 爬虫类用法
        demo_spider_usage()

        # Demo 3: 查询工具
        demo_query_tool()

        # Demo 4: Agent 集成
        demo_agent_integration()

        print("\n" + "=" * 60)
        print("所有示例完成!")
        print("=" * 60)

    except Exception as e:
        print(f"\n错误: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
