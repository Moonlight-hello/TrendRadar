#!/usr/bin/env python3
"""
本地快速测试脚本

测试 TrendRadar 和 CommunitySpy 的基本功能
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_imports():
    """测试导入"""
    print("=" * 60)
    print("测试 1: 模块导入")
    print("=" * 60)

    try:
        from trendradar.agent import AgentHarness, Task
        print("✅ AgentHarness 导入成功")

        from trendradar.agent.agents import CrawlerAgent, AnalyzerAgent
        print("✅ Agents 导入成功")

        from trendradar.agent.tools.base import BaseTool
        print("✅ BaseTool 导入成功")

        from trendradar.agent.tools.data_sources.communityspy import (
            CommunitySpyTool,
            EastMoneyCommentSpider
        )
        print("✅ CommunitySpy 导入成功")

        print("\n✅ 所有模块导入成功！\n")
        return True

    except Exception as e:
        print(f"\n❌ 导入失败: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return False


def test_tool_registry():
    """测试工具注册"""
    print("=" * 60)
    print("测试 2: 工具注册系统")
    print("=" * 60)

    try:
        from trendradar.agent import AgentHarness
        from trendradar.agent.tools.data_sources.communityspy import CommunitySpyTool

        # 创建编排器
        harness = AgentHarness()
        print("✅ AgentHarness 创建成功")

        # 注册工具
        tool = CommunitySpyTool()
        harness.register_tool(tool, "data_source")
        print("✅ CommunitySpy 工具注册成功")

        # 查看已注册的工具
        tools = harness.tool_registry.list_tools()
        print(f"✅ 已注册的工具: {tools}")

        # 获取工具元数据
        metadata = harness.tool_registry.get_metadata("communityspy")
        print(f"✅ 工具元数据: {metadata['name']}")

        print("\n✅ 工具注册系统正常！\n")
        return True

    except Exception as e:
        print(f"\n❌ 工具注册失败: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return False


def test_context():
    """测试上下文管理"""
    print("=" * 60)
    print("测试 3: 上下文管理")
    print("=" * 60)

    try:
        from trendradar.agent import Context

        # 创建上下文
        context = Context()
        print("✅ Context 创建成功")

        # 设置数据
        context.set("test_key", "test_value")
        print("✅ 数据设置成功")

        # 获取数据
        value = context.get("test_key")
        assert value == "test_value"
        print(f"✅ 数据获取成功: {value}")

        # 保存快照
        snapshot = context.snapshot()
        print(f"✅ 快照保存成功: {snapshot.timestamp}")

        print("\n✅ 上下文管理正常！\n")
        return True

    except Exception as e:
        print(f"\n❌ 上下文管理失败: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return False


def test_communityspy_basic():
    """测试 CommunitySpy 基本功能（不实际爬取）"""
    print("=" * 60)
    print("测试 4: CommunitySpy 基本功能")
    print("=" * 60)

    try:
        from trendradar.agent.tools.data_sources.communityspy import (
            CommunitySpyTool,
            EastMoneyCommentSpider
        )

        # 测试工具创建
        tool = CommunitySpyTool()
        print(f"✅ 工具名称: {tool.name}")
        print(f"✅ 工具描述: {tool.description}")
        print(f"✅ 工具类别: {tool.category}")

        # 测试参数定义
        params = tool.parameters
        print(f"✅ 参数数量: {len(params)}")
        print(f"✅ 必需参数: {[k for k, v in params.items() if v.get('required')]}")

        # 测试爬虫类创建（不实际连接）
        spider = EastMoneyCommentSpider("301293", db_path=":memory:")
        print(f"✅ 爬虫实例创建成功: {spider.stock_code}")
        spider.close()

        print("\n✅ CommunitySpy 基本功能正常！\n")
        return True

    except Exception as e:
        print(f"\n❌ CommunitySpy 测试失败: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("TrendRadar 本地测试")
    print("=" * 60 + "\n")

    results = []

    # 运行测试
    results.append(("模块导入", test_imports()))
    results.append(("工具注册", test_tool_registry()))
    results.append(("上下文管理", test_context()))
    results.append(("CommunitySpy", test_communityspy_basic()))

    # 打印总结
    print("=" * 60)
    print("测试总结")
    print("=" * 60)

    for name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{name}: {status}")

    all_passed = all(r[1] for r in results)

    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 所有测试通过！系统运行正常！")
        print("\n下一步:")
        print("1. 运行 examples/communityspy_demo.py 查看完整示例")
        print("2. 使用 CLI 工具测试实际爬取")
        print("3. 查看 QUICKSTART_LOCAL.md 了解更多")
    else:
        print("⚠️  部分测试失败，请检查错误信息")
        print("\n建议:")
        print("1. 检查依赖是否完整安装: pip install -r requirements.txt")
        print("2. 确认在项目根目录运行")
        print("3. 查看详细错误信息")

    print("=" * 60 + "\n")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
