#!/usr/bin/env python3
"""
TrendRadar v2.1.0 双引擎集成测试脚本

测试双引擎架构的完整集成
"""

import sys
from pathlib import Path


def print_section(title):
    """打印章节标题"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def test_imports():
    """测试1: 模块导入"""
    print_section("测试1: 模块导入")

    try:
        # 测试原版模块
        from trendradar.ai import AIAnalyzer, AIAnalysisResult
        print("✓ 原版模块导入成功: AIAnalyzer, AIAnalysisResult")

        # 测试新增模块
        from trendradar.ai import METHODOLOGY_AVAILABLE

        if METHODOLOGY_AVAILABLE:
            from trendradar.ai import (
                MethodologyAnalyzer,
                IntelligentRouter,
                AnalysisMode,
                AnalysisScenario,
            )
            print("✓ 方法论模块导入成功: MethodologyAnalyzer")
            print("✓ 智能路由器导入成功: IntelligentRouter")
            print("✓ 所有新增模块可用")
            return True
        else:
            print("⚠️  方法论模块不可用（缺少依赖或配置）")
            print("   这是正常的，可以继续使用原版功能")
            return False

    except ImportError as e:
        print(f"✗ 模块导入失败: {e}")
        return False


def test_prompt_manager():
    """测试2: Prompt管理器"""
    print_section("测试2: Prompt管理器")

    try:
        from trendradar.ai.prompt_manager import PromptManager

        # 检查配置文件
        config_file = Path("prompts_methodology.yaml")
        if not config_file.exists():
            print(f"✗ 配置文件不存在: {config_file}")
            return False

        # 加载Prompt管理器
        manager = PromptManager(str(config_file))
        print(f"✓ Prompt配置加载成功: {config_file}")

        # 测试获取Prompt
        prompt_config = manager.get_prompt("stage1")
        print(f"✓ Stage1 Prompt获取成功: {prompt_config.get('name')}")

        return True

    except Exception as e:
        print(f"✗ Prompt管理器测试失败: {e}")
        return False


def test_data_formatter():
    """测试3: 数据格式化"""
    print_section("测试3: 数据格式化")

    try:
        from trendradar.ai.data_formatter import DataFormatter

        formatter = DataFormatter()
        print("✓ 数据格式化工具初始化成功")

        # 测试数据格式化
        mock_data = {
            "price": ["沪铝期货：15,200元/吨"],
            "production": ["月产量：340万吨"],
        }

        formatted = formatter.format_data_section("aluminum", mock_data)
        print(f"✓ 数据格式化成功，长度: {len(formatted)} 字符")

        return True

    except Exception as e:
        print(f"✗ 数据格式化测试失败: {e}")
        return False


def test_intelligent_router():
    """测试4: 智能路由器"""
    print_section("测试4: 智能路由器")

    try:
        from trendradar.ai.intelligent_router import (
            IntelligentRouter,
            AnalysisMode,
            AnalysisScenario,
        )

        # 创建路由器（不传入实际分析器）
        router = IntelligentRouter()
        print("✓ 智能路由器初始化成功")

        # 测试场景推荐
        mode = router._determine_mode(
            scenario=AnalysisScenario.BREAKING_NEWS,
            mode=None
        )
        print(f"✓ 场景推荐测试: 突发热点 → {mode.value}")

        mode = router._determine_mode(
            scenario=AnalysisScenario.INDUSTRY_RESEARCH,
            mode=None
        )
        print(f"✓ 场景推荐测试: 行业研究 → {mode.value}")

        # 测试智能推荐
        recommended = IntelligentRouter.get_recommended_mode(
            news_count=100,
            has_industry_data=False,
            time_sensitive=True
        )
        print(f"✓ 智能推荐测试: 突发事件 → {recommended.value}")

        return True

    except Exception as e:
        print(f"✗ 智能路由器测试失败: {e}")
        return False


def test_methodology_analyzer():
    """测试5: 方法论分析器"""
    print_section("测试5: 方法论分析器")

    try:
        from trendradar.ai.methodology_analyzer import MethodologyAnalyzer

        # 创建分析器（使用模拟配置）
        mock_config = {
            "PROVIDER": "openai",
            "MODEL": "gpt-4",
            "API_KEY": "test-key",
        }

        analyzer = MethodologyAnalyzer(mock_config, debug=False)
        print("✓ 方法论分析器初始化成功")

        # 测试Prompt生成（不调用AI）
        mock_data = {
            "price": ["沪铝期货：15,200元/吨"],
            "production": ["月产量：340万吨"],
        }

        mock_news = [
            {"title": "沪铝期货上涨", "source": "财联社"}
        ]

        prompt = analyzer.generate_prompt_only(
            industry="aluminum",
            stage="stage1",
            data=mock_data,
            news=mock_news,
            output_path="output/test_dual_engine_prompt.txt"
        )

        print(f"✓ Prompt生成成功，长度: {len(prompt)} 字符")
        print(f"✓ 已保存到: output/test_dual_engine_prompt.txt")

        return True

    except Exception as e:
        print(f"✗ 方法论分析器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_demo_script():
    """测试6: Demo脚本"""
    print_section("测试6: Demo脚本")

    try:
        # 检查demo脚本
        demo_file = Path("demo_methodology.py")
        if not demo_file.exists():
            print(f"✗ Demo脚本不存在: {demo_file}")
            return False

        print(f"✓ Demo脚本存在: {demo_file}")

        # 检查输出目录
        output_dir = Path("output")
        if output_dir.exists():
            prompt_files = list(output_dir.glob("*_prompt.txt"))
            print(f"✓ 输出目录存在，包含 {len(prompt_files)} 个Prompt文件")
        else:
            print("⚠️  输出目录不存在，首次运行会自动创建")

        return True

    except Exception as e:
        print(f"✗ Demo脚本测试失败: {e}")
        return False


def test_config_files():
    """测试7: 配置文件"""
    print_section("测试7: 配置文件")

    required_files = [
        "config/config.yaml",
        "config/ai_analysis_prompt.txt",
        "config/ai_analysis_prompt_enhanced.txt",
        "prompts_methodology.yaml",
    ]

    all_exist = True
    for file_path in required_files:
        path = Path(file_path)
        if path.exists():
            size = path.stat().st_size / 1024
            print(f"✓ {file_path} ({size:.1f} KB)")
        else:
            print(f"✗ {file_path} (不存在)")
            all_exist = False

    return all_exist


def run_all_tests():
    """运行所有测试"""
    print("\n" + "🚀" * 30)
    print("   TrendRadar v2.1.0 双引擎集成测试")
    print("🚀" * 30)

    results = {}

    # 运行测试
    results["imports"] = test_imports()
    results["config_files"] = test_config_files()
    results["prompt_manager"] = test_prompt_manager()
    results["data_formatter"] = test_data_formatter()
    results["intelligent_router"] = test_intelligent_router()
    results["methodology_analyzer"] = test_methodology_analyzer()
    results["demo_script"] = test_demo_script()

    # 总结
    print_section("测试总结")

    total = len(results)
    passed = sum(1 for v in results.values() if v)

    print(f"\n总计: {passed}/{total} 项测试通过")
    print("\n详细结果:")

    status_symbols = {True: "✓", False: "✗"}
    test_names = {
        "imports": "模块导入",
        "config_files": "配置文件",
        "prompt_manager": "Prompt管理器",
        "data_formatter": "数据格式化",
        "intelligent_router": "智能路由器",
        "methodology_analyzer": "方法论分析器",
        "demo_script": "Demo脚本",
    }

    for key, passed in results.items():
        symbol = status_symbols[passed]
        name = test_names.get(key, key)
        print(f"  {symbol} {name}")

    # 给出建议
    print("\n" + "=" * 60)
    if passed == total:
        print("✅ 所有测试通过！系统已完全集成。")
        print("\n下一步:")
        print("  1. 安装依赖: pip3 install -r requirements.txt --break-system-packages")
        print("  2. 运行Demo: python3 demo_methodology.py --industry aluminum --stage stage1")
        print("  3. 启动TrendRadar: python3 -m trendradar")
    else:
        print("⚠️  部分测试未通过")
        print("\n建议:")
        if not results.get("config_files"):
            print("  • 检查配置文件是否完整")
        if not results.get("imports"):
            print("  • 检查模块导入，可能缺少依赖")
        if not results.get("methodology_analyzer"):
            print("  • 检查方法论分析器配置")

    print("=" * 60)

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
