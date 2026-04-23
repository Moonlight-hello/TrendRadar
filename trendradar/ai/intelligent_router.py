"""
智能路由器 - TrendRadar v2.1.0
根据分析场景智能选择原版分析器或方法论分析器
"""

from typing import Dict, Optional, List
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class AnalysisMode(Enum):
    """分析模式枚举"""
    REALTIME = "realtime"        # 实时热点监控（原版引擎）
    METHODOLOGY = "methodology"  # 深度行业分析（方法论引擎）
    MIXED = "mixed"              # 混合模式（两个引擎结合）


class AnalysisScenario(Enum):
    """分析场景枚举"""
    BREAKING_NEWS = "breaking_news"              # 突发热点
    DAILY_MONITORING = "daily_monitoring"        # 日常监控
    INDUSTRY_RESEARCH = "industry_research"      # 行业研究
    PERIODIC_REPORT = "periodic_report"          # 定期报告
    INVESTMENT_DECISION = "investment_decision"  # 投资决策


class IntelligentRouter:
    """
    智能路由器

    职责：
    1. 根据分析场景自动选择分析引擎
    2. 协调原版分析器和方法论分析器
    3. 在混合模式下合并两个引擎的输出
    """

    def __init__(self, original_analyzer=None, methodology_analyzer=None):
        """
        初始化智能路由器

        Args:
            original_analyzer: 原版分析器实例（AIAnalyzer）
            methodology_analyzer: 方法论分析器实例（MethodologyAnalyzer）
        """
        self.original_analyzer = original_analyzer
        self.methodology_analyzer = methodology_analyzer

        # 场景与模式的映射规则
        self.scenario_mode_map = {
            AnalysisScenario.BREAKING_NEWS: AnalysisMode.REALTIME,
            AnalysisScenario.DAILY_MONITORING: AnalysisMode.REALTIME,
            AnalysisScenario.INDUSTRY_RESEARCH: AnalysisMode.METHODOLOGY,
            AnalysisScenario.PERIODIC_REPORT: AnalysisMode.MIXED,
            AnalysisScenario.INVESTMENT_DECISION: AnalysisMode.METHODOLOGY,
        }

    def route(self,
              scenario: AnalysisScenario = None,
              mode: AnalysisMode = None,
              **kwargs) -> Dict:
        """
        路由到合适的分析引擎

        Args:
            scenario: 分析场景（如果提供，会自动推断mode）
            mode: 分析模式（手动指定，优先级高于scenario）
            **kwargs: 传递给分析器的参数

        Returns:
            分析结果字典
        """
        # 确定分析模式
        analysis_mode = self._determine_mode(scenario, mode)

        logger.info(f"路由到分析模式: {analysis_mode.value}")

        # 根据模式调用对应的分析器
        if analysis_mode == AnalysisMode.REALTIME:
            return self._route_to_realtime(**kwargs)

        elif analysis_mode == AnalysisMode.METHODOLOGY:
            return self._route_to_methodology(**kwargs)

        elif analysis_mode == AnalysisMode.MIXED:
            return self._route_to_mixed(**kwargs)

        else:
            raise ValueError(f"未知的分析模式: {analysis_mode}")

    def _determine_mode(self,
                       scenario: Optional[AnalysisScenario],
                       mode: Optional[AnalysisMode]) -> AnalysisMode:
        """
        确定分析模式

        优先级：mode > scenario > 默认(REALTIME)
        """
        if mode:
            return mode

        if scenario:
            return self.scenario_mode_map.get(scenario, AnalysisMode.REALTIME)

        # 默认使用实时模式
        return AnalysisMode.REALTIME

    def _route_to_realtime(self, **kwargs) -> Dict:
        """
        路由到原版实时分析器

        Returns:
            {
                "mode": "realtime",
                "result": AIAnalysisResult,
                "metadata": {...}
            }
        """
        if not self.original_analyzer:
            raise ValueError("原版分析器未初始化")

        logger.info("使用原版实时分析引擎")

        # 调用原版分析器
        result = self.original_analyzer.analyze(**kwargs)

        return {
            "mode": "realtime",
            "result": result,
            "metadata": {
                "engine": "original",
                "analysis_time": "<5分钟",
                "output_length": "~600字",
                "features": ["信号检测", "跨平台对比", "舆情分析"]
            }
        }

    def _route_to_methodology(self, **kwargs) -> Dict:
        """
        路由到方法论深度分析器

        Returns:
            {
                "mode": "methodology",
                "result": MethodologyAnalysisResult,
                "metadata": {...}
            }
        """
        if not self.methodology_analyzer:
            raise ValueError("方法论分析器未初始化")

        logger.info("使用方法论深度分析引擎")

        # 调用方法论分析器
        result = self.methodology_analyzer.analyze(**kwargs)

        return {
            "mode": "methodology",
            "result": result,
            "metadata": {
                "engine": "methodology",
                "analysis_time": "30-60分钟",
                "output_length": "1500-2000字",
                "features": ["产业链分析", "成本拆解", "数据驱动", "系统性认知"]
            }
        }

    def _route_to_mixed(self, **kwargs) -> Dict:
        """
        混合模式：结合两个引擎的优势

        Returns:
            {
                "mode": "mixed",
                "realtime_result": AIAnalysisResult,
                "methodology_result": MethodologyAnalysisResult,
                "merged_report": str,
                "metadata": {...}
            }
        """
        if not self.original_analyzer or not self.methodology_analyzer:
            raise ValueError("混合模式需要两个分析器都初始化")

        logger.info("使用混合分析模式")

        # 并行调用两个分析器
        realtime_result = self.original_analyzer.analyze(**kwargs)
        methodology_result = self.methodology_analyzer.analyze(**kwargs)

        # 合并输出
        merged_report = self._merge_results(realtime_result, methodology_result)

        return {
            "mode": "mixed",
            "realtime_result": realtime_result,
            "methodology_result": methodology_result,
            "merged_report": merged_report,
            "metadata": {
                "engines": ["original", "methodology"],
                "analysis_time": "30-60分钟",
                "output_length": "2000-3000字",
                "features": ["实时热点", "深度分析", "数据驱动", "信号检测"]
            }
        }

    def _merge_results(self, realtime_result, methodology_result) -> str:
        """
        合并两个分析器的结果

        策略：
        1. 热点摘要部分：使用原版的5段式分析
        2. 深度分析部分：使用方法论的6章节报告
        3. 数据速查表：来自方法论分析
        """
        report_parts = []

        # 第一部分：实时热点摘要（原版）
        report_parts.append("# 📊 实时热点摘要\n")
        report_parts.append("## 核心热点态势")
        report_parts.append(realtime_result.core_trends)
        report_parts.append("\n## 舆论风向争议")
        report_parts.append(realtime_result.sentiment_controversy)
        report_parts.append("\n## 异动与弱信号")
        report_parts.append(realtime_result.signals)

        # 第二部分：深度行业分析（方法论）
        report_parts.append("\n\n# 📈 深度行业分析\n")
        report_parts.append(methodology_result.get("full_report", ""))

        # 第三部分：数据速查表（方法论）
        if "data_table" in methodology_result:
            report_parts.append("\n\n# 📋 关键数据速查表\n")
            report_parts.append(methodology_result["data_table"])

        # 第四部分：综合研判（合并两者的展望）
        report_parts.append("\n\n# 🎯 综合研判\n")
        report_parts.append("## 短期展望（实时视角）")
        report_parts.append(realtime_result.outlook_strategy)
        report_parts.append("\n## 中长期展望（深度视角）")
        report_parts.append(methodology_result.get("outlook", ""))

        return "\n".join(report_parts)

    @staticmethod
    def get_recommended_mode(news_count: int,
                            has_industry_data: bool,
                            time_sensitive: bool) -> AnalysisMode:
        """
        根据情况推荐分析模式

        Args:
            news_count: 新闻条数
            has_industry_data: 是否有行业结构化数据
            time_sensitive: 是否时间敏感（突发事件）

        Returns:
            推荐的分析模式
        """
        # 突发事件 → 实时模式
        if time_sensitive:
            return AnalysisMode.REALTIME

        # 有行业数据 → 方法论模式或混合模式
        if has_industry_data:
            if news_count > 20:
                return AnalysisMode.MIXED
            else:
                return AnalysisMode.METHODOLOGY

        # 新闻很多但没行业数据 → 实时模式
        if news_count > 50:
            return AnalysisMode.REALTIME

        # 默认实时模式
        return AnalysisMode.REALTIME


class AnalysisRequest:
    """分析请求封装类"""

    def __init__(self,
                 scenario: AnalysisScenario = None,
                 mode: AnalysisMode = None,
                 industry: str = None,
                 stage: str = None,
                 stats: Dict = None,
                 rss_stats: Dict = None,
                 industry_data: Dict = None,
                 **kwargs):
        """
        初始化分析请求

        Args:
            scenario: 分析场景
            mode: 分析模式（可选，会自动推断）
            industry: 行业名称（方法论分析需要）
            stage: 分析阶段（方法论分析需要，如stage1/stage2/stage3/cost）
            stats: 热榜统计数据（原版分析需要）
            rss_stats: RSS统计数据（原版分析需要）
            industry_data: 行业结构化数据（方法论分析需要）
            **kwargs: 其他参数
        """
        self.scenario = scenario
        self.mode = mode
        self.industry = industry
        self.stage = stage
        self.stats = stats
        self.rss_stats = rss_stats
        self.industry_data = industry_data
        self.kwargs = kwargs

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "scenario": self.scenario.value if self.scenario else None,
            "mode": self.mode.value if self.mode else None,
            "industry": self.industry,
            "stage": self.stage,
            "stats": self.stats,
            "rss_stats": self.rss_stats,
            "industry_data": self.industry_data,
            **self.kwargs
        }


# 使用示例
if __name__ == "__main__":
    # 示例1：突发热点分析
    print("=" * 60)
    print("示例1：突发热点分析（实时模式）")
    print("=" * 60)

    router = IntelligentRouter()
    mode = router._determine_mode(
        scenario=AnalysisScenario.BREAKING_NEWS,
        mode=None
    )
    print(f"推荐模式: {mode.value}")
    print(f"预期输出: ~600字，<5分钟")
    print(f"特点: 信号检测、跨平台对比、舆情分析")

    # 示例2：行业研究
    print("\n" + "=" * 60)
    print("示例2：行业研究（方法论模式）")
    print("=" * 60)

    mode = router._determine_mode(
        scenario=AnalysisScenario.INDUSTRY_RESEARCH,
        mode=None
    )
    print(f"推荐模式: {mode.value}")
    print(f"预期输出: 1500-2000字，30-60分钟")
    print(f"特点: 产业链分析、成本拆解、数据驱动")

    # 示例3：定期报告
    print("\n" + "=" * 60)
    print("示例3：定期报告（混合模式）")
    print("=" * 60)

    mode = router._determine_mode(
        scenario=AnalysisScenario.PERIODIC_REPORT,
        mode=None
    )
    print(f"推荐模式: {mode.value}")
    print(f"预期输出: 2000-3000字，30-60分钟")
    print(f"特点: 实时热点 + 深度分析")

    # 示例4：智能推荐
    print("\n" + "=" * 60)
    print("示例4：智能推荐模式")
    print("=" * 60)

    # 场景A：突发事件（100条新闻，无行业数据，时间敏感）
    mode_a = IntelligentRouter.get_recommended_mode(
        news_count=100,
        has_industry_data=False,
        time_sensitive=True
    )
    print(f"场景A（突发事件）: {mode_a.value}")

    # 场景B：行业跟踪（15条新闻，有行业数据，不紧急）
    mode_b = IntelligentRouter.get_recommended_mode(
        news_count=15,
        has_industry_data=True,
        time_sensitive=False
    )
    print(f"场景B（行业跟踪）: {mode_b.value}")

    # 场景C：周报生成（50条新闻，有行业数据，不紧急）
    mode_c = IntelligentRouter.get_recommended_mode(
        news_count=50,
        has_industry_data=True,
        time_sensitive=False
    )
    print(f"场景C（周报生成）: {mode_c.value}")

    print("\n✅ 智能路由器示例运行完成！")
