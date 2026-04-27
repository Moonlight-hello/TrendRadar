# -*- coding: utf-8 -*-
"""
东方财富股吧客户端
从HTML中提取嵌入的JSON数据（而不是解析HTML标签）
"""

import asyncio
import json
import logging
import re
from typing import Dict, List, Optional
from urllib.parse import urlencode

import httpx


logger = logging.getLogger(__name__)


class EastMoneyClient:
    """东方财富股吧客户端（从HTML提取JSON数据）"""

    def __init__(self, cookies: Optional[Dict] = None):
        self.base_url = "https://guba.eastmoney.com"

        # 用户提供的Cookie（可选）
        self.cookies = cookies or {
            "qgqp_b_id": "158d23a8e8f260623c1a489368661090",
            "nid18": "04f8c86cbf08ab9d8acbc47965b1b765",
            "gviem": "oFKe4LfaBztRSWlpuxIPZ6de1",
            "st_si": "48337060892598",
            "st_pvi": "22164803623127",
            "st_sn": "102",
            "st_psi": "20260424164413379-117001356556-4497026896",
        }

        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": "https://guba.eastmoney.com/",
        }

        self._client: Optional[httpx.AsyncClient] = None

    def _get_cookies_string(self) -> str:
        """将cookies字典转换为字符串"""
        return "; ".join([f"{k}={v}" for k, v in self.cookies.items()])

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def close(self):
        """关闭客户端"""
        if self._client:
            await self._client.aclose()

    def get_client(self) -> httpx.AsyncClient:
        """获取HTTP客户端"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                headers=self.headers,
                cookies=self.cookies,
                timeout=30.0,
                follow_redirects=True
            )
        return self._client

    async def _fetch_html(self, url: str) -> str:
        """获取HTML页面"""
        client = self.get_client()
        try:
            response = await client.get(url)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.error(f"[EastMoney] Request error: {e}")
            raise

    def _parse_post_list(self, html: str, stock_code: str) -> List[Dict]:
        """
        从HTML中提取嵌入的JSON数据

        Args:
            html: HTML内容
            stock_code: 股票代码

        Returns:
            帖子列表
        """
        posts = []

        try:
            # 查找包含帖子数据的JSON对象
            # 数据格式: {"re":[{"post_id":...}, ...]}
            # 查找所有script标签
            scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)

            for script in scripts:
                # 查找包含帖子数据的script
                if '"post_id"' not in script or '"post_title"' not in script:
                    continue

                # 查找JSON对象的起始位置
                start_idx = script.find('{"re":[')
                if start_idx == -1:
                    continue

                # 从起始位置开始提取，找到完整的JSON对象
                # 使用括号计数法找到JSON结束位置
                json_text = self._extract_json_object(script[start_idx:])

                if json_text:
                    try:
                        data = json.loads(json_text)
                        raw_posts = data.get('re', [])

                        logger.info(f"[EastMoney] 从JSON中提取到 {len(raw_posts)} 条原始帖子")

                        # 转换为标准格式
                        for raw_post in raw_posts:
                            # 只处理当前股票的帖子
                            if raw_post.get('stockbar_code') != stock_code:
                                continue

                            post_data = {
                                "post_id": str(raw_post.get('post_id', '')),
                                "title": raw_post.get('post_title', ''),
                                "content": "",  # 列表页不包含正文
                                "stock_code": stock_code,
                                "stock_name": raw_post.get('stockbar_name', '').replace('吧', ''),
                                "author_id": raw_post.get('user_id', ''),
                                "author_name": raw_post.get('user_nickname', ''),
                                "publish_time": raw_post.get('post_publish_time', ''),
                                "read_count": raw_post.get('post_click_count', 0),
                                "comment_count": raw_post.get('post_comment_count', 0),
                                "like_count": 0,  # API中没有点赞数
                                "post_type": raw_post.get('post_type', 0) + 1,  # 转换为1开始
                                "post_url": f"{self.base_url}/news,{stock_code},{raw_post.get('post_id')}.html",
                            }
                            posts.append(post_data)

                        break  # 找到数据后退出循环

                    except json.JSONDecodeError as e:
                        logger.error(f"[EastMoney] JSON解析失败: {e}")
                        continue

            logger.info(f"[EastMoney] 成功解析 {len(posts)} 条当前股票的帖子")

        except Exception as e:
            logger.error(f"[EastMoney] 解析帖子列表失败: {e}")

        return posts

    def _parse_comment_data(self, raw_comments: List, post_id: str) -> List[Dict]:
        """
        解析评论数据

        Args:
            raw_comments: 原始评论列表
            post_id: 帖子ID

        Returns:
            标准格式评论列表
        """
        comments = []
        for raw in raw_comments:
            # 提取用户信息
            reply_user = raw.get('reply_user', {})

            comment = {
                "comment_id": str(raw.get('reply_id', '')),
                "post_id": str(raw.get('source_post_id', post_id)),
                "content": raw.get('reply_text', ''),
                "author_id": str(raw.get('user_id', '')),
                "author_name": reply_user.get('user_nickname', ''),
                "create_time": raw.get('reply_time', ''),
                "like_count": raw.get('reply_like_count', 0),
                "reply_count": raw.get('child_reply_count', 0),
                "parent_id": "",  # 一级评论没有parent_id
            }
            comments.append(comment)
        return comments

    def _extract_json_object(self, text: str) -> Optional[str]:
        """
        从文本中提取完整的JSON对象
        使用括号计数法

        Args:
            text: 包含JSON的文本，起始位置是'{'

        Returns:
            完整的JSON字符串，如果失败返回None
        """
        if not text or text[0] != '{':
            return None

        brace_count = 0
        in_string = False
        escape_next = False

        for i, char in enumerate(text):
            if escape_next:
                escape_next = False
                continue

            if char == '\\' and in_string:
                escape_next = True
                continue

            if char == '"' and not in_string:
                in_string = True
            elif char == '"' and in_string:
                in_string = False
            elif char == '{' and not in_string:
                brace_count += 1
            elif char == '}' and not in_string:
                brace_count -= 1
                if brace_count == 0:
                    # 找到完整的JSON对象
                    return text[:i+1]

        return None

    async def get_stock_posts(
        self,
        stock_code: str,
        page: int = 1,
        page_size: int = 20
    ) -> Dict:
        """
        获取股票吧帖子列表（通过HTML解析）

        Args:
            stock_code: 股票代码
            page: 页码（第一页为1）
            page_size: 每页数量（实际由网页决定，约80条）

        Returns:
            帖子列表数据
        """
        # 构造URL
        # 第一页: https://guba.eastmoney.com/list,{stock_code}.html
        # 其他页: https://guba.eastmoney.com/list,{stock_code}_{page}.html
        if page == 1:
            url = f"{self.base_url}/list,{stock_code}.html"
        else:
            url = f"{self.base_url}/list,{stock_code}_{page}.html"

        logger.info(f"[EastMoney] 访问: {url}")

        try:
            # 获取HTML
            html = await self._fetch_html(url)

            # 解析帖子列表
            posts = self._parse_post_list(html, stock_code)

            logger.info(f"[EastMoney] 成功解析 {len(posts)} 条帖子")

            return {
                "success": True,
                "data": {
                    "list": posts,
                    "total": len(posts),
                },
                "page": page,
                "stock_code": stock_code,
            }

        except Exception as e:
            logger.error(f"[EastMoney] 获取帖子列表失败: {e}")
            return {
                "success": False,
                "data": {"list": []},
                "error": str(e),
            }

    async def get_post_comments(
        self,
        post_id: str,
        stock_code: str = "",
        page: int = 1,
        page_size: int = 30
    ) -> Dict:
        """
        获取帖子评论列表
        使用真实的评论API

        Args:
            post_id: 帖子ID
            stock_code: 股票代码
            page: 页码
            page_size: 每页数量（默认30）

        Returns:
            评论列表
        """
        if not stock_code:
            logger.warning(f"[EastMoney] 获取评论需要stock_code参数")
            return {"data": {"list": []}}

        try:
            logger.info(f"[EastMoney] 获取评论: post_id={post_id}, page={page}")

            # 真实的评论API
            api_url = "https://guba.eastmoney.com/api/getData"

            # Query参数
            query_params = {
                "code": stock_code,
                "path": "reply/api/Reply/ArticleNewReplyList"
            }

            # Body参数（URL编码格式）
            # param参数包含：postid, sort, sorttype, p(page), ps(pagesize)
            param_data = f"postid={post_id}&sort=1&sorttype=1&p={page}&ps={page_size}"
            body_data = {
                "param": param_data,
                "plat": "Web",
                "path": "reply/api/Reply/ArticleNewReplyList",
                "env": "2",
                "origin": "",
                "version": "2022",
                "product": "Guba"
            }

            # Headers
            headers = {
                "Accept": "*/*",
                "Accept-Language": "zh-CN,zh;q=0.9",
                "Content-Type": "application/x-www-form-urlencoded",
                "Origin": "https://guba.eastmoney.com",
                "Referer": f"https://guba.eastmoney.com/news,{stock_code},{post_id}.html",
                "User-Agent": self.headers["User-Agent"],
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin",
            }

            client = self.get_client()
            response = await client.post(
                api_url,
                params=query_params,
                data=body_data,
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()

                # 解析评论数据
                if data.get('re') and isinstance(data['re'], list):
                    comments = self._parse_comment_data(data['re'], post_id)
                    total_count = data.get('reply_total_count', len(comments))

                    logger.info(f"[EastMoney] 获取到 {len(comments)} 条评论（共{total_count}条）")
                    return {
                        "success": True,
                        "data": {
                            "list": comments,
                            "total": total_count,
                            "page": page
                        }
                    }
                else:
                    logger.debug(f"[EastMoney] 帖子 {post_id} 暂无评论")
            else:
                logger.warning(
                    f"[EastMoney] 获取评论失败: status={response.status_code}, response={response.text[:200]}"
                )

        except Exception as e:
            logger.error(f"[EastMoney] 获取评论失败: {e}")
            import traceback
            traceback.print_exc()

        return {"data": {"list": []}}

    async def get_stock_info(self, stock_code: str) -> Dict:
        """
        获取股票信息

        Args:
            stock_code: 股票代码

        Returns:
            股票信息
        """
        # TODO: 实现股票基本信息获取
        return {
            "stock_code": stock_code,
            "stock_name": "",
        }
