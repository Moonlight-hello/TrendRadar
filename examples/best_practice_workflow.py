#!/usr/bin/env python3
"""
最佳实践：RSS + 浏览器自动化 混合方案

工作流：
1. RSS获取知乎热榜（100条标题+摘要）- 快速、合法
2. AI判断哪些"有价值"（10-20条）
3. 对"有价值"的用浏览器自动化获取完整内容
4. AI生成深度分析报告

优势：
- RSS批量获取 → 高效
- 浏览器自动化深度获取 → 精准
- AI分析 → 智能
- 完全合法 → 零风险
"""

import asyncio
import sqlite3
from typing import List, Dict
from playwright.async_api import async_playwright


class HybridContentFetcher:
    """混合内容获取器：RSS + 浏览器自动化"""

    def __init__(self):
        self.valuable_keywords = [
            # 行业关键词
            "电解铝", "铝土矿", "氧化铝", "产能", "供应链",
            "茅台", "白酒", "经销商", "批价",
            "新能源", "比亚迪", "特斯拉", "锂电池",
            "AI", "DeepSeek", "大模型", "算力",
            "芯片", "半导体", "华为", "英伟达",

            # 信号词（表示有深度内容）
            "分析", "解读", "深度", "产业链", "成本",
            "研究", "报告", "数据", "趋势",
        ]

    async def step1_get_rss_summaries(self, db_path: str) -> List[Dict]:
        """
        步骤1：从TrendRadar的RSS数据库获取摘要

        Args:
            db_path: RSS数据库路径

        Returns:
            包含标题和摘要的列表
        """
        print("\n" + "=" * 60)
        print("步骤1：从RSS获取内容摘要")
        print("=" * 60)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 查询今日知乎RSS数据
        cursor.execute("""
            SELECT feed_id, title, url, summary, published_at
            FROM rss_items
            WHERE feed_id IN ('zhihu-hot', 'zhihu-daily')
            AND date(created_at) = date('now')
            ORDER BY created_at DESC
            LIMIT 100
        """)

        items = cursor.fetchall()
        conn.close()

        results = []
        for feed_id, title, url, summary, published_at in items:
            results.append({
                "feed_id": feed_id,
                "title": title,
                "url": url,
                "summary": summary or "",
                "published_at": published_at,
            })

        print(f"✓ 从RSS获取 {len(results)} 条摘要")
        return results

    def step2_ai_filter_valuable(self, items: List[Dict]) -> List[Dict]:
        """
        步骤2：AI判断哪些内容"有价值"

        简化版：关键词匹配
        完整版：调用LLM API

        Args:
            items: RSS摘要列表

        Returns:
            有价值的内容列表
        """
        print("\n" + "=" * 60)
        print("步骤2：AI判断有价值内容")
        print("=" * 60)

        valuable_items = []

        for item in items:
            text = item['title'] + " " + item['summary']

            # 简化版：关键词匹配
            if any(keyword in text for keyword in self.valuable_keywords):
                valuable_items.append(item)

        print(f"✓ 发现 {len(valuable_items)} 条有价值内容")

        # 显示前5条
        for i, item in enumerate(valuable_items[:5], 1):
            print(f"  {i}. {item['title'][:40]}...")

        return valuable_items

    async def step3_fetch_full_content(self, items: List[Dict], limit: int = 10) -> List[Dict]:
        """
        步骤3：用浏览器自动化获取完整内容

        Args:
            items: 有价值的内容列表
            limit: 最多获取几条完整内容

        Returns:
            包含完整内容的列表
        """
        print("\n" + "=" * 60)
        print(f"步骤3：获取完整内容（限制{limit}条）")
        print("=" * 60)

        full_contents = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
                viewport={'width': 1920, 'height': 1080},
            )

            for i, item in enumerate(items[:limit], 1):
                print(f"\n[{i}/{limit}] {item['title'][:40]}...")

                try:
                    page = await context.new_page()
                    await page.goto(item['url'], wait_until='networkidle', timeout=30000)
                    await page.wait_for_selector('.QuestionHeader-title', timeout=10000)

                    # 获取完整回答
                    answer = ""
                    try:
                        await page.wait_for_selector('.RichContent-inner', timeout=5000)
                        answer_elem = await page.query_selector('.RichContent-inner')
                        if answer_elem:
                            answer = await answer_elem.text_content()
                            answer = answer[:1000]  # 限制1000字
                    except:
                        pass

                    full_contents.append({
                        **item,
                        "full_content": answer.strip() if answer else item['summary'],
                    })

                    print(f"  ✓ 成功获取 {len(answer)} 字")
                    await page.close()

                    # 礼貌间隔
                    if i < limit:
                        await asyncio.sleep(3)

                except Exception as e:
                    print(f"  ✗ 失败: {e}")
                    # 失败时使用摘要
                    full_contents.append({
                        **item,
                        "full_content": item['summary'],
                    })

            await browser.close()

        return full_contents

    def step4_generate_report(self, contents: List[Dict]) -> str:
        """
        步骤4：生成深度分析报告

        完整版应该调用LLM API生成
        这里演示简化版

        Args:
            contents: 完整内容列表

        Returns:
            分析报告
        """
        print("\n" + "=" * 60)
        print("步骤4：生成深度分析报告")
        print("=" * 60)

        report = []
        report.append("# 知乎热点深度分析报告\n")
        report.append(f"生成时间：2026-03-04\n")
        report.append(f"数据来源：知乎RSS + 浏览器自动化\n")
        report.append(f"分析条数：{len(contents)}\n\n")

        report.append("## 核心发现\n\n")

        for i, item in enumerate(contents, 1):
            report.append(f"### {i}. {item['title']}\n\n")
            report.append(f"**平台**: {item['feed_id']}\n")
            report.append(f"**链接**: {item['url']}\n\n")
            report.append(f"**内容摘要**:\n{item['full_content'][:300]}...\n\n")
            report.append(f"**发布时间**: {item.get('published_at', '未知')}\n\n")
            report.append("---\n\n")

        report_text = "".join(report)

        # 保存报告
        with open("output/zhihu_deep_analysis.md", "w", encoding="utf-8") as f:
            f.write(report_text)

        print("✓ 报告已保存到: output/zhihu_deep_analysis.md")
        return report_text


async def main():
    """主流程"""

    print("=" * 60)
    print("混合内容获取方案 - 演示")
    print("=" * 60)
    print("\n工作流:")
    print("1. RSS获取摘要（快速、合法）")
    print("2. AI判断价值（智能筛选）")
    print("3. 浏览器自动化获取完整内容（深度）")
    print("4. AI生成报告（分析）")
    print("\n" + "=" * 60)

    fetcher = HybridContentFetcher()

    # 步骤1：从RSS获取摘要
    rss_db = "output/rss/2026-03-04.db"
    summaries = await fetcher.step1_get_rss_summaries(rss_db)

    if not summaries:
        print("\n⚠️ 没有RSS数据，请先运行TrendRadar抓取RSS")
        print("   python3 -m trendradar")
        return

    # 步骤2：AI判断价值
    valuable = fetcher.step2_ai_filter_valuable(summaries)

    if not valuable:
        print("\n⚠️ 没有发现有价值的内容")
        return

    # 步骤3：获取完整内容
    full_contents = await fetcher.step3_fetch_full_content(valuable, limit=5)

    # 步骤4：生成报告
    report = fetcher.step4_generate_report(full_contents)

    print("\n" + "=" * 60)
    print("✅ 分析完成！")
    print("=" * 60)
    print(f"\n共分析 {len(full_contents)} 条深度内容")
    print("报告已保存到: output/zhihu_deep_analysis.md")


if __name__ == "__main__":
    # 先确保TrendRadar已经抓取了RSS数据
    # python3 -m trendradar

    # 然后运行本脚本
    asyncio.run(main())
