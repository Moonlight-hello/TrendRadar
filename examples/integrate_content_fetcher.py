#!/usr/bin/env python3
"""
将内容抓取集成到TrendRadar工作流

流程：
1. TrendRadar抓取热榜标题（现有功能）
2. AI判断哪些标题"有价值"
3. 对"有价值"的标题，用浏览器自动化获取完整内容
4. AI分析完整内容，生成深度报告
"""

import asyncio
import sqlite3
from typing import List, Dict
from playwright.async_api import async_playwright


class ContentFetcher:
    """内容获取器 - 合法获取完整内容"""

    def __init__(self, max_daily_requests: int = 50):
        """
        初始化

        Args:
            max_daily_requests: 每天最大请求数（防止过度抓取）
        """
        self.max_daily_requests = max_daily_requests
        self.request_count = 0

    async def fetch_content(self, url: str, platform: str) -> Dict:
        """
        根据平台获取内容

        Args:
            url: 文章链接
            platform: 平台名称（zhihu/weibo/douyin等）

        Returns:
            内容字典
        """
        if self.request_count >= self.max_daily_requests:
            return {"error": "已达每日请求上限"}

        self.request_count += 1

        if "zhihu.com" in url:
            return await self._fetch_zhihu(url)
        elif "weibo.com" in url:
            return await self._fetch_weibo(url)
        else:
            return {"error": f"暂不支持平台: {platform}"}

    async def _fetch_zhihu(self, url: str) -> Dict:
        """获取知乎内容"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
                viewport={'width': 1920, 'height': 1080},
            )
            page = await context.new_page()

            try:
                await page.goto(url, wait_until='networkidle', timeout=30000)
                await page.wait_for_selector('.QuestionHeader-title', timeout=10000)

                title = await page.text_content('.QuestionHeader-title')

                # 提取问题描述
                description = ""
                try:
                    desc_elem = await page.query_selector('.QuestionRichText')
                    if desc_elem:
                        description = await desc_elem.text_content()
                except:
                    pass

                # 提取第一个回答（限制500字）
                top_answer = ""
                try:
                    await page.wait_for_selector('.RichContent-inner', timeout=5000)
                    answer_elem = await page.query_selector('.RichContent-inner')
                    if answer_elem:
                        top_answer = await answer_elem.text_content()
                        top_answer = top_answer[:500] + "..." if len(top_answer) > 500 else top_answer
                except:
                    pass

                # 礼貌等待
                await asyncio.sleep(2)

                return {
                    "url": url,
                    "title": title.strip() if title else "",
                    "description": description.strip() if description else "",
                    "content": top_answer.strip() if top_answer else "",
                    "platform": "知乎",
                }

            except Exception as e:
                return {"url": url, "error": str(e)}
            finally:
                await browser.close()

    async def _fetch_weibo(self, url: str) -> Dict:
        """获取微博内容（待实现）"""
        return {"url": url, "error": "微博内容获取功能开发中"}


class IntelligentContentAnalyzer:
    """智能内容分析器"""

    def __init__(self):
        self.fetcher = ContentFetcher(max_daily_requests=50)

    async def analyze_hot_topics(self, db_path: str):
        """
        分析TrendRadar抓取的热榜

        Args:
            db_path: TrendRadar数据库路径
        """
        # 1. 从TrendRadar数据库读取今日热榜
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT platform_id, title, url
            FROM news_items
            WHERE created_at >= date('now')
            LIMIT 100
        """)

        items = cursor.fetchall()
        conn.close()

        print(f"✓ 读取到 {len(items)} 条热榜新闻")

        # 2. AI判断哪些"有价值"（这里简化为关键词匹配）
        valuable_keywords = [
            "电解铝", "茅台", "新能源", "AI", "比亚迪",
            "华为", "特斯拉", "DeepSeek", "产能", "供应链"
        ]

        valuable_items = []
        for platform, title, url in items:
            if any(keyword in title for keyword in valuable_keywords):
                valuable_items.append((platform, title, url))

        print(f"✓ 发现 {len(valuable_items)} 条有价值的新闻")

        # 3. 对"有价值"的新闻获取完整内容
        print("\n开始获取完整内容...")
        detailed_contents = []

        for i, (platform, title, url) in enumerate(valuable_items[:10], 1):  # 限制前10条
            print(f"\n[{i}/10] {title[:30]}...")

            content = await self.fetcher.fetch_content(url, platform)

            if "error" not in content:
                detailed_contents.append({
                    "title": title,
                    "platform": platform,
                    "url": url,
                    "content": content.get("content", ""),
                    "description": content.get("description", ""),
                })
                print(f"  ✓ 获取成功")
            else:
                print(f"  ✗ 失败: {content['error']}")

            # 礼貌间隔
            if i < len(valuable_items):
                await asyncio.sleep(3)

        # 4. 生成分析报告
        print("\n" + "=" * 60)
        print("深度内容分析报告")
        print("=" * 60)

        for item in detailed_contents:
            print(f"\n📄 {item['title']}")
            print(f"   平台: {item['platform']}")
            print(f"   内容摘要: {item['content'][:100]}...")

        return detailed_contents


async def main():
    """主流程示例"""

    print("=" * 60)
    print("TrendRadar + 内容获取 集成示例")
    print("=" * 60)
    print("\n工作流程:")
    print("1. 读取TrendRadar今日热榜")
    print("2. AI判断哪些标题\"有价值\"")
    print("3. 获取\"有价值\"新闻的完整内容")
    print("4. 生成深度分析报告")
    print("\n" + "=" * 60 + "\n")

    # 指定TrendRadar数据库路径
    db_path = "output/news/2026-03-04.db"

    analyzer = IntelligentContentAnalyzer()
    await analyzer.analyze_hot_topics(db_path)


if __name__ == "__main__":
    asyncio.run(main())
