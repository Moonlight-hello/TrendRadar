# coding=utf-8
"""
数据格式化工具 - 将TrendRadar数据转换为Prompt需要的Markdown格式
"""

from typing import List, Dict
from datetime import datetime


class DataFormatter:
    """数据格式化器"""

    def format_data_section(
        self,
        industry: str,
        data: Dict = None,
        lookback_months: int = 12
    ) -> str:
        """
        格式化数据部分为Markdown

        Args:
            industry: 行业名称
            data: 数据字典（如果为None，使用模拟数据）
            lookback_months: 回溯月数

        Returns:
            Markdown格式的数据部分
        """
        if data is None:
            # 使用模拟数据（快速Demo）
            data = self._get_mock_data(industry)

        sections = []
        sections.append(f"## 最近{lookback_months}个月数据\n")

        # 价格数据
        if "price" in data:
            sections.append("### 价格数据")
            for item in data["price"]:
                sections.append(f"- {item}")
            sections.append("")

        # 产量数据
        if "production" in data:
            sections.append("### 产量数据")
            for item in data["production"]:
                sections.append(f"- {item}")
            sections.append("")

        # 消费数据
        if "consumption" in data:
            sections.append("### 消费数据")
            for item in data["consumption"]:
                sections.append(f"- {item}")
            sections.append("")

        # 库存数据
        if "inventory" in data:
            sections.append("### 库存数据")
            for item in data["inventory"]:
                sections.append(f"- {item}")
            sections.append("")

        # 宏观数据
        if "macro" in data:
            sections.append("### 宏观数据")
            for item in data["macro"]:
                sections.append(f"- {item}")
            sections.append("")

        return "\n".join(sections)

    def format_news_section(self, news_items: List[Dict]) -> str:
        """
        格式化新闻部分为Markdown

        Args:
            news_items: 新闻列表（字典格式）

        Returns:
            Markdown格式的新闻部分
        """
        if not news_items:
            return "暂无相关新闻"

        lines = []
        for i, news in enumerate(news_items, 1):
            platform = news.get("platform", "未知来源")
            title = news.get("title", "无标题")
            lines.append(f"{i}. 【{platform}】{title}")

        return "\n".join(lines)

    def _get_mock_data(self, industry: str) -> Dict:
        """
        获取模拟数据（用于快速Demo）

        Args:
            industry: 行业名称

        Returns:
            模拟数据字典
        """
        # 电解铝模拟数据
        if industry in ["电解铝", "aluminum"]:
            return {
                "price": [
                    "沪铝期货均价：15,200元/吨（最近1个月）",
                    "氧化铝现货价：2,400元/吨",
                    "预焙阳极价格：1,900元/吨",
                    "现货升水：+150元/吨（扩大）"
                ],
                "production": [
                    "电解铝月产量：340万吨（2025年2月）",
                    "同比增长：+3.2%",
                    "开工率：86.5%（产能利用率）",
                    "产能上限：4,500万吨（政策限制）"
                ],
                "consumption": [
                    "表观消费量：350万吨/月",
                    "同比增长：+5.1%",
                    "下游占比：建筑32%、交通28%、电力15%、包装10%、其他15%",
                    "新能源汽车拉动：单车用铝从80kg增至200kg"
                ],
                "inventory": [
                    "交易所库存（上期所）：85万吨",
                    "环比：-7.6%",
                    "历史分位：35分位（偏低）",
                    "库存天数：24.3天（低于安全水平30天）"
                ],
                "macro": [
                    "制造业PMI：51.2（扩张区间）",
                    "房地产投资：同比-5.2%（拖累需求）",
                    "汽车产量：同比+8.3%（提振需求）",
                    "固定资产投资：累计同比+3.0%"
                ]
            }

        # 钢铁模拟数据
        elif industry in ["钢铁", "steel"]:
            return {
                "price": [
                    "螺纹钢期货：3,850元/吨",
                    "热轧卷板：4,100元/吨",
                    "铁矿石：890元/吨"
                ],
                "production": [
                    "粗钢产量：8,500万吨/月",
                    "同比：-2.1%",
                    "产能利用率：83%"
                ],
                "inventory": [
                    "社会库存：1,200万吨",
                    "环比：+5%"
                ],
                "macro": [
                    "基建投资：+4.5%",
                    "房地产投资：-5.2%"
                ]
            }

        # 默认数据
        else:
            return {
                "price": [f"{industry}价格数据待补充"],
                "production": [f"{industry}产量数据待补充"],
                "inventory": [f"{industry}库存数据待补充"]
            }


class MockNewsProvider:
    """模拟新闻提供者（用于快速Demo）"""

    @staticmethod
    def get_recent_news(industry: str, days: int = 7) -> List[Dict]:
        """
        获取最近新闻（模拟）

        Args:
            industry: 行业名称
            days: 天数

        Returns:
            新闻列表
        """
        if industry in ["电解铝", "aluminum"]:
            return [
                {
                    "platform": "财联社",
                    "title": "沪铝期货涨1.5%，突破15,500元关口",
                    "date": "2025-02-11"
                },
                {
                    "platform": "SMM",
                    "title": "云南、内蒙古等地电解铝企业开工率回升",
                    "date": "2025-02-10"
                },
                {
                    "platform": "新华社",
                    "title": "新能源汽车产量同比增长25%，带动铝需求",
                    "date": "2025-02-10"
                },
                {
                    "platform": "Mysteel",
                    "title": "氧化铝价格下跌，电解铝利润扩大",
                    "date": "2025-02-09"
                },
                {
                    "platform": "路透",
                    "title": "几内亚铝土矿出口增长12%，供应充足",
                    "date": "2025-02-08"
                }
            ]

        elif industry in ["钢铁", "steel"]:
            return [
                {
                    "platform": "财联社",
                    "title": "螺纹钢期货小幅上涨",
                    "date": "2025-02-11"
                },
                {
                    "platform": "Mysteel",
                    "title": "钢材社会库存累积",
                    "date": "2025-02-10"
                }
            ]

        else:
            return [
                {
                    "platform": "模拟来源",
                    "title": f"{industry}行业相关新闻",
                    "date": datetime.now().strftime("%Y-%m-%d")
                }
            ]


# 便捷函数
def format_for_prompt(
    industry: str,
    use_mock_data: bool = True
) -> tuple:
    """
    为Prompt准备数据和新闻

    Args:
        industry: 行业名称
        use_mock_data: 是否使用模拟数据

    Returns:
        (data_section, news_section)
    """
    formatter = DataFormatter()

    # 数据部分
    data_section = formatter.format_data_section(industry)

    # 新闻部分
    if use_mock_data:
        news_provider = MockNewsProvider()
        news_items = news_provider.get_recent_news(industry)
    else:
        # TODO: 集成真实的新闻获取
        news_items = []

    news_section = formatter.format_news_section(news_items)

    return data_section, news_section


if __name__ == "__main__":
    # 测试
    print("测试数据格式化工具\n")
    print("=" * 60)

    data_section, news_section = format_for_prompt("电解铝")

    print("数据部分：")
    print(data_section)

    print("\n新闻部分：")
    print(news_section)
