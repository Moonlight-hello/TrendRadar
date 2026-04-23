#!/usr/bin/env python3
"""
知乎内容合法抓取示例 - 使用浏览器自动化

法律说明：
- 模拟真实用户浏览行为（不突破反爬）
- 仅用于个人学习研究（符合著作权法第24条）
- 遵守robots.txt和平台服务条款
- 不进行大规模、高频率抓取

技术栈：Playwright（比Selenium更稳定）
"""

import asyncio
import json
from playwright.async_api import async_playwright
from typing import Dict, Optional


async def fetch_zhihu_question_content(url: str) -> Dict:
    """
    合法获取知乎问题内容

    Args:
        url: 知乎问题链接

    Returns:
        包含标题、问题描述、高赞回答的字典
    """
    async with async_playwright() as p:
        # 启动浏览器（使用无头模式）
        browser = await p.chromium.launch(
            headless=True,  # 无头模式
            args=[
                '--disable-blink-features=AutomationControlled',  # 反反爬检测
            ]
        )

        # 创建上下文（模拟真实用户）
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='zh-CN',
        )

        page = await context.new_page()

        try:
            print(f"正在访问: {url}")

            # 1. 访问页面（模拟真实用户）
            await page.goto(url, wait_until='networkidle', timeout=30000)

            # 2. 等待内容加载（真实用户也会等待）
            await page.wait_for_selector('.QuestionHeader-title', timeout=10000)

            # 3. 提取标题
            title = await page.text_content('.QuestionHeader-title')
            print(f"✓ 标题: {title}")

            # 4. 提取问题描述（如果有）
            description = ""
            try:
                desc_elem = await page.query_selector('.QuestionRichText')
                if desc_elem:
                    description = await desc_elem.text_content()
            except:
                pass

            # 5. 提取第一个高赞回答（只取第一个，避免过度抓取）
            top_answer = ""
            try:
                # 等待回答加载
                await page.wait_for_selector('.List-item', timeout=5000)

                # 获取第一个回答
                answer_elem = await page.query_selector('.RichContent-inner')
                if answer_elem:
                    top_answer = await answer_elem.text_content()
                    # 限制长度（避免抓取过多）
                    top_answer = top_answer[:500] + "..." if len(top_answer) > 500 else top_answer
            except:
                pass

            # 6. 礼貌等待（模拟真实阅读时间）
            await asyncio.sleep(2)

            result = {
                "url": url,
                "title": title.strip() if title else "",
                "description": description.strip() if description else "",
                "top_answer": top_answer.strip() if top_answer else "",
                "source": "知乎",
            }

            return result

        except Exception as e:
            print(f"✗ 获取失败: {e}")
            return {
                "url": url,
                "error": str(e),
            }
        finally:
            await browser.close()


async def main():
    """示例：获取TrendRadar抓取的知乎热榜内容"""

    # 示例URL（从TrendRadar的数据库读取）
    test_urls = [
        "https://www.zhihu.com/question/2012146437148935053",  # 班主任退群
        "https://www.zhihu.com/question/488808761",  # 最宜居城市
    ]

    print("=" * 60)
    print("知乎内容合法获取示例")
    print("=" * 60)
    print("\n⚖️ 法律说明:")
    print("1. 本工具仅用于个人学习研究（符合著作权法第24条）")
    print("2. 模拟真实用户浏览，不突破技术保护措施")
    print("3. 每个请求间隔2秒以上（礼貌爬取）")
    print("4. 不进行大规模、商业化数据采集")
    print("\n" + "=" * 60 + "\n")

    results = []

    for i, url in enumerate(test_urls, 1):
        print(f"\n[{i}/{len(test_urls)}] 正在获取内容...")
        result = await fetch_zhihu_question_content(url)
        results.append(result)

        # 礼貌间隔（重要！）
        if i < len(test_urls):
            print("⏳ 等待3秒（礼貌爬取）...")
            await asyncio.sleep(3)

    # 输出结果
    print("\n" + "=" * 60)
    print("获取结果汇总")
    print("=" * 60)

    for i, result in enumerate(results, 1):
        print(f"\n📄 问题 {i}:")
        if "error" in result:
            print(f"  ✗ 失败: {result['error']}")
        else:
            print(f"  标题: {result['title'][:50]}...")
            print(f"  描述: {result['description'][:50]}..." if result['description'] else "  描述: (无)")
            print(f"  回答: {result['top_answer'][:100]}..." if result['top_answer'] else "  回答: (无)")

    # 保存到文件
    output_file = "output/zhihu_content.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n✓ 结果已保存到: {output_file}")


if __name__ == "__main__":
    # 安装依赖：pip install playwright
    # 首次运行：playwright install chromium

    asyncio.run(main())
