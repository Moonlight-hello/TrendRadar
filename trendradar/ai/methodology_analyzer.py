"""
方法论驱动分析器 - TrendRadar v2.1.0

提供基于知识沉淀方法论的深度行业分析能力
"""

import logging
from typing import Dict, List, Optional
from pathlib import Path

from trendradar.ai.client import AIClient
from trendradar.ai.prompt_manager import PromptManager
from trendradar.ai.data_formatter import DataFormatter

logger = logging.getLogger(__name__)


class MethodologyAnalysisResult:
    """方法论分析结果"""

    def __init__(
        self,
        success: bool,
        full_report: str = "",
        stage: str = "",
        industry: str = "",
        data_table: str = "",
        outlook: str = "",
        error: Optional[str] = None,
    ):
        self.success = success
        self.full_report = full_report
        self.stage = stage
        self.industry = industry
        self.data_table = data_table
        self.outlook = outlook
        self.error = error

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "success": self.success,
            "full_report": self.full_report,
            "stage": self.stage,
            "industry": self.industry,
            "data_table": self.data_table,
            "outlook": self.outlook,
            "error": self.error,
        }


class MethodologyAnalyzer:
    """
    方法论驱动分析器

    职责：
    1. 加载Prompt模板
    2. 格式化行业数据和新闻
    3. 调用AI进行深度分析
    4. 返回结构化分析结果

    支持的分析阶段：
    - stage1: 行业宏观认知（5天掌握全貌）
    - stage2: 公司研究（财报+成本）
    - stage3: 微观跟踪（异常识别）
    - cost: 成本结构深度拆解
    """

    def __init__(
        self,
        ai_config: Dict,
        prompt_file: str = "prompts_methodology.yaml",
        debug: bool = False,
    ):
        """
        初始化方法论分析器

        Args:
            ai_config: AI配置（与AIClient兼容）
            prompt_file: Prompt模板文件路径
            debug: 是否开启调试模式
        """
        self.ai_config = ai_config
        self.debug = debug

        # 初始化AI客户端（复用TrendRadar的LiteLLM客户端）
        self.client = AIClient(ai_config)

        # 初始化Prompt管理器
        try:
            self.prompt_manager = PromptManager(prompt_file)
            if debug:
                logger.info(f"Prompt模板加载成功: {prompt_file}")
        except Exception as e:
            logger.error(f"加载Prompt模板失败: {e}")
            raise

        # 初始化数据格式化工具
        self.data_formatter = DataFormatter()

    def analyze(
        self,
        industry: str,
        stage: str,
        data: Optional[Dict] = None,
        news: Optional[List[Dict]] = None,
        lookback_months: int = 12,
        **kwargs,
    ) -> MethodologyAnalysisResult:
        """
        执行方法论驱动的行业分析

        Args:
            industry: 行业名称（如"aluminum", "steel", "copper"）
            stage: 分析阶段（stage1/stage2/stage3/cost）
            data: 行业结构化数据（包含price, production, inventory等）
            news: 新闻列表
            lookback_months: 数据回溯月数（默认12个月）
            **kwargs: 其他参数

        Returns:
            MethodologyAnalysisResult: 分析结果对象
        """
        try:
            # 1. 格式化数据
            if self.debug:
                logger.info(f"开始分析: 行业={industry}, 阶段={stage}")

            data_section = self._format_data(industry, data, lookback_months)
            news_section = self._format_news(news)

            # 2. 渲染Prompt
            prompt = self._render_prompt(stage, industry, data_section, news_section, **kwargs)

            if self.debug:
                logger.info(f"Prompt渲染完成，长度: {len(prompt)} 字符")

            # 3. 调用AI
            response = self._call_ai(prompt)

            if self.debug:
                logger.info(f"AI响应完成，长度: {len(response)} 字符")

            # 4. 解析结果
            result = self._parse_response(response, stage, industry)

            return result

        except Exception as e:
            logger.error(f"方法论分析失败: {e}")
            if self.debug:
                import traceback
                traceback.print_exc()
            return MethodologyAnalysisResult(
                success=False, error=f"分析失败: {str(e)}"
            )

    def _format_data(
        self, industry: str, data: Optional[Dict], lookback_months: int
    ) -> str:
        """格式化行业数据"""
        if not data:
            return "（暂无结构化数据）"

        return self.data_formatter.format_data_section(
            industry=industry, data=data, lookback_months=lookback_months
        )

    def _format_news(self, news: Optional[List[Dict]]) -> str:
        """格式化新闻列表"""
        if not news:
            return "（暂无相关新闻）"

        return self.data_formatter.format_news_section(news)

    def _render_prompt(
        self,
        stage: str,
        industry: str,
        data_section: str,
        news_section: str,
        **kwargs,
    ) -> str:
        """渲染Prompt模板"""
        try:
            return self.prompt_manager.render_prompt(
                stage=stage,
                industry=industry,
                data_section=data_section,
                news_section=news_section,
                **kwargs,
            )
        except Exception as e:
            logger.error(f"Prompt渲染失败: {e}")
            raise

    def _call_ai(self, prompt: str) -> str:
        """调用AI模型"""
        try:
            # 使用与TrendRadar原版相同的AIClient
            messages = [{"role": "user", "content": prompt}]

            response = self.client.chat(messages)

            return response

        except Exception as e:
            logger.error(f"AI调用失败: {e}")
            raise

    def _parse_response(
        self, response: str, stage: str, industry: str
    ) -> MethodologyAnalysisResult:
        """解析AI响应"""
        # 简单解析，将完整响应作为报告
        # 后续可以增强解析逻辑，提取数据表、展望等部分

        # 尝试提取关键部分
        data_table = ""
        outlook = ""

        # 简单的关键词匹配提取
        if "关键数据速查表" in response or "数据速查表" in response:
            # 尝试提取数据表部分
            lines = response.split("\n")
            in_table = False
            table_lines = []
            for line in lines:
                if "数据速查表" in line or "关键数据" in line:
                    in_table = True
                if in_table:
                    table_lines.append(line)
                    if line.strip().startswith("##") and "数据速查表" not in line:
                        break
            if table_lines:
                data_table = "\n".join(table_lines)

        if "展望" in response or "未来" in response or "趋势" in response:
            # 尝试提取展望部分
            lines = response.split("\n")
            outlook_lines = []
            in_outlook = False
            for line in lines:
                if any(
                    keyword in line
                    for keyword in ["展望", "未来", "趋势", "预测", "后续"]
                ):
                    in_outlook = True
                if in_outlook:
                    outlook_lines.append(line)
                    # 简单的结束判断
                    if (
                        line.strip().startswith("##")
                        and not any(
                            keyword in line
                            for keyword in ["展望", "未来", "趋势", "预测"]
                        )
                    ):
                        break
            if outlook_lines:
                outlook = "\n".join(outlook_lines)

        return MethodologyAnalysisResult(
            success=True,
            full_report=response,
            stage=stage,
            industry=industry,
            data_table=data_table,
            outlook=outlook,
        )

    def generate_prompt_only(
        self,
        industry: str,
        stage: str,
        data: Optional[Dict] = None,
        news: Optional[List[Dict]] = None,
        lookback_months: int = 12,
        output_path: Optional[str] = None,
        **kwargs,
    ) -> str:
        """
        仅生成Prompt，不调用AI（用于导出或手动测试）

        Args:
            industry: 行业名称
            stage: 分析阶段
            data: 行业数据
            news: 新闻列表
            lookback_months: 数据回溯月数
            output_path: 输出文件路径（可选）
            **kwargs: 其他参数

        Returns:
            str: 完整的Prompt文本
        """
        # 格式化数据和新闻
        data_section = self._format_data(industry, data, lookback_months)
        news_section = self._format_news(news)

        # 渲染Prompt
        prompt = self._render_prompt(
            stage, industry, data_section, news_section, **kwargs
        )

        # 如果指定了输出路径，保存到文件
        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(prompt)
            if self.debug:
                logger.info(f"Prompt已保存到: {output_path}")

        return prompt


# 便捷函数
def analyze_industry(
    industry: str,
    stage: str,
    ai_config: Dict,
    data: Optional[Dict] = None,
    news: Optional[List[Dict]] = None,
    prompt_file: str = "prompts_methodology.yaml",
    debug: bool = False,
) -> MethodologyAnalysisResult:
    """
    便捷函数：执行行业分析

    Args:
        industry: 行业名称
        stage: 分析阶段
        ai_config: AI配置
        data: 行业数据
        news: 新闻列表
        prompt_file: Prompt模板文件
        debug: 调试模式

    Returns:
        MethodologyAnalysisResult: 分析结果
    """
    analyzer = MethodologyAnalyzer(ai_config, prompt_file, debug)
    return analyzer.analyze(industry, stage, data, news)


# 测试示例
if __name__ == "__main__":
    print("MethodologyAnalyzer 测试")
    print("=" * 60)

    # 模拟配置
    mock_ai_config = {
        "PROVIDER": "openai",
        "MODEL": "gpt-4",
        "API_KEY": "test-key",
        "BASE_URL": None,
        "TIMEOUT": 120,
    }

    # 模拟数据
    mock_data = {
        "price": ["沪铝期货均价：15,200元/吨", "氧化铝现货价：2,400元/吨"],
        "production": ["电解铝月产量：340万吨", "同比增长：+3.2%"],
        "inventory": ["交易所库存：85万吨", "环比：-7.6%"],
    }

    mock_news = [
        {"title": "沪铝期货涨1.5%，突破15,500元关口", "source": "财联社"},
        {"title": "新能源汽车产量同比增长25%", "source": "新华社"},
    ]

    try:
        # 测试1: 仅生成Prompt
        print("\n测试1: 生成Prompt（不调用AI）")
        analyzer = MethodologyAnalyzer(mock_ai_config, debug=True)
        prompt = analyzer.generate_prompt_only(
            industry="aluminum",
            stage="stage1",
            data=mock_data,
            news=mock_news,
            output_path="output/test_prompt.txt",
        )
        print(f"✓ Prompt生成成功，长度: {len(prompt)} 字符")
        print(f"✓ 已保存到: output/test_prompt.txt")

        print("\n" + "=" * 60)
        print("✅ MethodologyAnalyzer 测试通过")
        print("=" * 60)
        print("\n提示：")
        print("1. 实际使用时需要配置真实的AI API密钥")
        print("2. 调用 analyzer.analyze() 会自动调用AI并返回结果")
        print("3. 使用 generate_prompt_only() 可以导出Prompt进行手动测试")

    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback

        traceback.print_exc()
