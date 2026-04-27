# -*- coding: utf-8 -*-
"""
东方财富股吧爬虫核心模块
简化版本，适配TrendRadar项目
"""

import asyncio
import logging
from typing import List, Dict, Optional

from .client import EastMoneyClient


logger = logging.getLogger(__name__)


class EastMoneyCrawler:
    """东方财富股吧爬虫"""

    def __init__(self, cookies: Optional[Dict] = None):
        """
        初始化爬虫

        Args:
            cookies: 可选的Cookie字典
        """
        self.client = EastMoneyClient(cookies=cookies)
        self.posts_data: List[Dict] = []
        self.comments_data: List[Dict] = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def close(self):
        """关闭爬虫"""
        await self.client.close()

    async def crawl_stock_posts(
        self,
        stock_code: str,
        max_pages: int = 1,
        enable_comments: bool = True,
        max_comments_per_post: int = 100
    ) -> Dict:
        """
        爬取股票帖子和评论

        Args:
            stock_code: 股票代码
            max_pages: 最大爬取页数
            enable_comments: 是否爬取评论
            max_comments_per_post: 每个帖子最大评论数

        Returns:
            爬取结果统计
        """
        logger.info(f"[EastMoneyCrawler] 开始爬取股票 {stock_code}")

        all_posts = []
        all_comments = []

        # 1. 爬取帖子列表
        for page in range(1, max_pages + 1):
            logger.info(f"[EastMoneyCrawler] 爬取第 {page} 页帖子")

            result = await self.client.get_stock_posts(stock_code, page=page)

            if not result.get('success'):
                logger.error(f"[EastMoneyCrawler] 爬取第 {page} 页失败")
                break

            posts = result['data']['list']
            all_posts.extend(posts)

            logger.info(f"[EastMoneyCrawler] 第 {page} 页获取到 {len(posts)} 条帖子")

            # 短暂延迟，避免请求过快
            await asyncio.sleep(1)

        logger.info(f"[EastMoneyCrawler] 共获取 {len(all_posts)} 条帖子")

        # 2. 爬取评论（如果启用）
        if enable_comments and all_posts:
            logger.info(f"[EastMoneyCrawler] 开始爬取评论")

            for i, post in enumerate(all_posts):
                post_id = post['post_id']
                comment_count = post.get('comment_count', 0)

                if comment_count == 0:
                    continue

                logger.info(f"[EastMoneyCrawler] 爬取帖子 {post_id} 的评论 ({i+1}/{len(all_posts)})")

                # 计算需要爬取的页数
                comments_per_page = 30
                total_pages = (min(comment_count, max_comments_per_post) + comments_per_page - 1) // comments_per_page

                post_comments = []
                for page in range(1, total_pages + 1):
                    result = await self.client.get_post_comments(
                        post_id=post_id,
                        stock_code=stock_code,
                        page=page
                    )

                    if result.get('success'):
                        comments = result['data']['list']
                        post_comments.extend(comments)

                        if len(comments) < comments_per_page:
                            break  # 最后一页

                        # 短暂延迟
                        await asyncio.sleep(0.5)
                    else:
                        break

                all_comments.extend(post_comments)
                logger.info(f"[EastMoneyCrawler] 帖子 {post_id} 获取到 {len(post_comments)} 条评论")

                # 避免请求过快
                await asyncio.sleep(1)

        # 保存数据
        self.posts_data = all_posts
        self.comments_data = all_comments

        logger.info(f"[EastMoneyCrawler] 爬取完成: {len(all_posts)} 条帖子, {len(all_comments)} 条评论")

        return {
            "stock_code": stock_code,
            "posts_count": len(all_posts),
            "comments_count": len(all_comments),
            "posts": all_posts,
            "comments": all_comments,
        }

    async def crawl_multiple_stocks(
        self,
        stock_codes: List[str],
        max_pages: int = 1,
        enable_comments: bool = True,
        max_comments_per_post: int = 100
    ) -> Dict:
        """
        爬取多个股票的数据

        Args:
            stock_codes: 股票代码列表
            max_pages: 每个股票最大爬取页数
            enable_comments: 是否爬取评论
            max_comments_per_post: 每个帖子最大评论数

        Returns:
            所有股票的爬取结果
        """
        logger.info(f"[EastMoneyCrawler] 开始爬取 {len(stock_codes)} 个股票")

        results = {}

        for stock_code in stock_codes:
            try:
                result = await self.crawl_stock_posts(
                    stock_code=stock_code,
                    max_pages=max_pages,
                    enable_comments=enable_comments,
                    max_comments_per_post=max_comments_per_post
                )
                results[stock_code] = result

                # 间隔，避免请求过快
                await asyncio.sleep(2)

            except Exception as e:
                logger.error(f"[EastMoneyCrawler] 爬取股票 {stock_code} 失败: {e}")
                results[stock_code] = {
                    "error": str(e),
                    "posts_count": 0,
                    "comments_count": 0,
                }

        total_posts = sum(r.get('posts_count', 0) for r in results.values())
        total_comments = sum(r.get('comments_count', 0) for r in results.values())

        logger.info(
            f"[EastMoneyCrawler] 全部完成: {len(stock_codes)} 个股票, "
            f"{total_posts} 条帖子, {total_comments} 条评论"
        )

        return {
            "total_stocks": len(stock_codes),
            "total_posts": total_posts,
            "total_comments": total_comments,
            "results": results,
        }


async def crawl_eastmoney_stock(
    stock_code: str,
    max_pages: int = 1,
    enable_comments: bool = True,
    max_comments_per_post: int = 100,
    cookies: Optional[Dict] = None
) -> Dict:
    """
    便捷函数：爬取单个股票数据

    Args:
        stock_code: 股票代码
        max_pages: 最大爬取页数
        enable_comments: 是否爬取评论
        max_comments_per_post: 每个帖子最大评论数
        cookies: 可选的Cookie字典

    Returns:
        爬取结果
    """
    async with EastMoneyCrawler(cookies=cookies) as crawler:
        return await crawler.crawl_stock_posts(
            stock_code=stock_code,
            max_pages=max_pages,
            enable_comments=enable_comments,
            max_comments_per_post=max_comments_per_post
        )


async def crawl_eastmoney_stocks(
    stock_codes: List[str],
    max_pages: int = 1,
    enable_comments: bool = True,
    max_comments_per_post: int = 100,
    cookies: Optional[Dict] = None
) -> Dict:
    """
    便捷函数：爬取多个股票数据

    Args:
        stock_codes: 股票代码列表
        max_pages: 每个股票最大爬取页数
        enable_comments: 是否爬取评论
        max_comments_per_post: 每个帖子最大评论数
        cookies: 可选的Cookie字典

    Returns:
        爬取结果
    """
    async with EastMoneyCrawler(cookies=cookies) as crawler:
        return await crawler.crawl_multiple_stocks(
            stock_codes=stock_codes,
            max_pages=max_pages,
            enable_comments=enable_comments,
            max_comments_per_post=max_comments_per_post
        )
