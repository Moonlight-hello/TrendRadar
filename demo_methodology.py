#!/usr/bin/env python3
# coding=utf-8
"""
方法论驱动分析 - 快速Demo

用法：
    python3 demo_methodology.py --industry aluminum --stage stage1
    python3 demo_methodology.py --industry aluminum --stage cost
"""

import argparse
import yaml
from pathlib import Path


def load_prompt_config():
    """加载Prompt配置"""
    config_path = "prompts_methodology.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def get_mock_data(industry: str):
    """获取模拟数据"""
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
    return {}


def get_mock_news(industry: str):
    """获取模拟新闻"""
    if industry in ["电解铝", "aluminum"]:
        return [
            {"platform": "财联社", "title": "沪铝期货涨1.5%，突破15,500元关口"},
            {"platform": "SMM", "title": "云南、内蒙古等地电解铝企业开工率回升"},
            {"platform": "新华社", "title": "新能源汽车产量同比增长25%，带动铝需求"},
            {"platform": "Mysteel", "title": "氧化铝价格下跌，电解铝利润扩大"},
            {"platform": "路透", "title": "几内亚铝土矿出口增长12%，供应充足"}
        ]
    return []


def format_data_section(data):
    """格式化数据部分"""
    sections = ["## 最近12个月数据\n"]

    if "price" in data:
        sections.append("### 价格数据")
        sections.extend([f"- {item}" for item in data["price"]])
        sections.append("")

    if "production" in data:
        sections.append("### 产量数据")
        sections.extend([f"- {item}" for item in data["production"]])
        sections.append("")

    if "consumption" in data:
        sections.append("### 消费数据")
        sections.extend([f"- {item}" for item in data["consumption"]])
        sections.append("")

    if "inventory" in data:
        sections.append("### 库存数据")
        sections.extend([f"- {item}" for item in data["inventory"]])
        sections.append("")

    if "macro" in data:
        sections.append("### 宏观数据")
        sections.extend([f"- {item}" for item in data["macro"]])
        sections.append("")

    return "\n".join(sections)


def format_news_section(news_items):
    """格式化新闻部分"""
    if not news_items:
        return "暂无相关新闻"

    lines = []
    for i, news in enumerate(news_items, 1):
        platform = news.get("platform", "未知")
        title = news.get("title", "无标题")
        lines.append(f"{i}. 【{platform}】{title}")

    return "\n".join(lines)


def run_analysis(industry: str, stage: str, use_ai: bool = False):
    """运行分析"""

    print(f"\n{'='*60}")
    print(f"🎯 方法论驱动分析 - {stage}")
    print(f"{'='*60}\n")

    # 1. 加载Prompt配置
    print("📋 加载Prompt配置...")
    config = load_prompt_config()
    prompts = config.get("prompts", {})

    # 映射stage名称
    stage_map = {
        "stage1": "stage1_industry_overview",
        "stage2": "stage2_company_analysis",
        "stage3": "stage3_micro_tracking",
        "cost": "special_cost_breakdown"
    }

    prompt_key = stage_map.get(stage, stage)
    prompt_config = prompts.get(prompt_key)

    if not prompt_config:
        print(f"✗ 未找到Prompt: {prompt_key}")
        print(f"可用的有: {list(prompts.keys())}")
        return

    print(f"✓ 加载成功: {prompt_config.get('name')}")

    # 2. 获取数据
    print("\n📊 获取数据...")
    data = get_mock_data(industry)
    news = get_mock_news(industry)
    print(f"✓ 数据类别: {len(data)}个")
    print(f"✓ 新闻条数: {len(news)}条")

    # 3. 格式化
    print("\n📝 格式化数据...")
    data_section = format_data_section(data)
    news_section = format_news_section(news)
    print("✓ 格式化完成")

    # 4. 渲染Prompt
    print("\n🎨 渲染Prompt模板...")
    template = prompt_config.get("template", "")

    try:
        # 根据stage不同，提供不同的参数
        if stage == "cost":
            rendered_prompt = template.format(
                industry=industry,
                product=industry,
                data_section=data_section,
                news_section=news_section
            )
        else:
            rendered_prompt = template.format(
                industry=industry,
                data_section=data_section,
                news_section=news_section
            )

        print(f"✓ Prompt渲染成功（{len(rendered_prompt)}字符）")

    except KeyError as e:
        print(f"✗ Prompt渲染失败，缺少参数: {e}")
        return

    # 5. AI分析（可选）
    if use_ai:
        print("\n🤖 调用AI分析...")
        print("（本Demo跳过实际AI调用，显示Prompt）")

    # 6. 输出结果
    print(f"\n{'='*60}")
    print("📄 完整Prompt预览")
    print(f"{'='*60}\n")
    print(rendered_prompt[:2000])  # 显示前2000字符
    print("\n... (完整内容省略) ...\n")

    # 7. 保存到文件
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / f"{industry}_{stage}_prompt.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(rendered_prompt)

    print(f"✓ 完整Prompt已保存到: {output_file}")

    # 8. 总结
    print(f"\n{'='*60}")
    print("✅ Demo运行成功！")
    print(f"{'='*60}\n")

    print("下一步：")
    print("1. 查看生成的Prompt文件")
    print("2. 复制Prompt到ChatGPT/Claude测试效果")
    print("3. 集成真实的AI API（需要配置API Key）")
    print()


def main():
    parser = argparse.ArgumentParser(description="方法论驱动分析 - 快速Demo")
    parser.add_argument("--industry", default="aluminum", help="行业名称（默认：aluminum）")
    parser.add_argument("--stage", default="stage1", choices=["stage1", "stage2", "stage3", "cost"],
                        help="分析阶段（默认：stage1）")
    parser.add_argument("--use-ai", action="store_true", help="调用AI API（需要配置）")

    args = parser.parse_args()

    run_analysis(args.industry, args.stage, args.use_ai)


if __name__ == "__main__":
    main()
