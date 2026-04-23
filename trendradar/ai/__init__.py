# coding=utf-8
"""
TrendRadar AI 模块

提供 AI 大模型对热点新闻的深度分析和翻译功能

v2.1.0 新增:
- MethodologyAnalyzer: 方法论驱动深度分析器
- IntelligentRouter: 智能路由器（根据场景选择分析器）
"""

from .analyzer import AIAnalyzer, AIAnalysisResult
from .translator import AITranslator, TranslationResult, BatchTranslationResult
from .formatter import (
    get_ai_analysis_renderer,
    render_ai_analysis_markdown,
    render_ai_analysis_feishu,
    render_ai_analysis_dingtalk,
    render_ai_analysis_html,
    render_ai_analysis_html_rich,
    render_ai_analysis_plain,
)

# v2.1.0: 方法论驱动分析（可选导入，避免依赖问题）
try:
    from .methodology_analyzer import (
        MethodologyAnalyzer,
        MethodologyAnalysisResult,
        analyze_industry,
    )
    from .intelligent_router import (
        IntelligentRouter,
        AnalysisMode,
        AnalysisScenario,
        AnalysisRequest,
    )
    METHODOLOGY_AVAILABLE = True
except ImportError:
    METHODOLOGY_AVAILABLE = False
    MethodologyAnalyzer = None
    MethodologyAnalysisResult = None
    IntelligentRouter = None
    AnalysisMode = None
    AnalysisScenario = None

__all__ = [
    # 分析器
    "AIAnalyzer",
    "AIAnalysisResult",
    # 翻译器
    "AITranslator",
    "TranslationResult",
    "BatchTranslationResult",
    # 格式化
    "get_ai_analysis_renderer",
    "render_ai_analysis_markdown",
    "render_ai_analysis_feishu",
    "render_ai_analysis_dingtalk",
    "render_ai_analysis_html",
    "render_ai_analysis_html_rich",
    "render_ai_analysis_plain",
    # v2.1.0: 方法论驱动分析
    "MethodologyAnalyzer",
    "MethodologyAnalysisResult",
    "analyze_industry",
    "IntelligentRouter",
    "AnalysisMode",
    "AnalysisScenario",
    "AnalysisRequest",
    "METHODOLOGY_AVAILABLE",
]
