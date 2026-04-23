"""
东方财富股吧评论爬虫

从原 communityspy.py 提取的核心爬虫功能
"""

import requests
import json
import time
import sqlite3
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from urllib.parse import urlencode, quote
import random


class EastMoneyCommentSpider:
    """东方财富股吧评论爬虫"""

    def __init__(self, stock_code: str, db_path: Optional[str] = None):
        """
        初始化爬虫

        Args:
            stock_code: 股票代码
            db_path: 数据库路径，如果为 None 则使用默认路径
        """
        self.stock_code = stock_code
        self.db_path = db_path or f'eastmoney_{stock_code}.db'

        # API URLs
        self.base_url = "https://guba.eastmoney.com"
        self.gbapi_url = "https://gbapi.eastmoney.com"

        # 初始化 Session
        self.session = requests.Session()
        self.session.verify = False

        # 设置请求头（完整的浏览器请求头）
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Connection': 'keep-alive',
            'Referer': 'https://guba.eastmoney.com/',
            'Sec-Fetch-Dest': 'script',
            'Sec-Fetch-Mode': 'no-cors',
            'Sec-Fetch-Site': 'same-site',
        }

        self.session.headers.update(self.headers)

        # 存储已爬取的ID
        self.crawled_posts = set()
        self.crawled_comments = set()

        # 初始化数据库
        if self.db_path:
            self.init_database()

    def init_database(self):
        """初始化SQLite数据库（完整版本）"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()

        # 创建帖子表（完整字段）
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id TEXT UNIQUE NOT NULL,
            stock_code TEXT NOT NULL,
            title TEXT,
            abstract TEXT,
            content TEXT,
            publish_time TEXT,
            update_time TEXT,
            user_id TEXT,
            user_nickname TEXT,
            user_level INTEGER DEFAULT 0,
            click_count INTEGER DEFAULT 0,
            comment_count INTEGER DEFAULT 0,
            forward_count INTEGER DEFAULT 0,
            like_count INTEGER DEFAULT 0,
            is_top INTEGER DEFAULT 0,
            is_hot INTEGER DEFAULT 0,
            is_essence INTEGER DEFAULT 0,
            source_type INTEGER DEFAULT 0,
            tags TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # 创建评论表（完整字段）
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            comment_id TEXT UNIQUE NOT NULL,
            post_id TEXT NOT NULL,
            parent_comment_id TEXT,
            user_id TEXT,
            user_nickname TEXT,
            user_level INTEGER DEFAULT 0,
            content TEXT,
            publish_time TEXT,
            like_count INTEGER DEFAULT 0,
            reply_count INTEGER DEFAULT 0,
            floor_number INTEGER,
            is_author INTEGER DEFAULT 0,
            is_recommend INTEGER DEFAULT 0,
            ip_address TEXT,
            device_type TEXT,
            status INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (post_id) REFERENCES posts(post_id)
        )
        ''')

        # 创建回复表
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS replies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reply_id TEXT UNIQUE NOT NULL,
            comment_id TEXT NOT NULL,
            post_id TEXT NOT NULL,
            parent_reply_id TEXT,
            user_id TEXT,
            user_nickname TEXT,
            target_user_id TEXT,
            target_user_nickname TEXT,
            content TEXT,
            publish_time TEXT,
            like_count INTEGER DEFAULT 0,
            floor_number INTEGER,
            ip_address TEXT,
            device_type TEXT,
            status INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (comment_id) REFERENCES comments(comment_id),
            FOREIGN KEY (post_id) REFERENCES posts(post_id)
        )
        ''')

        # 创建索引
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_posts_stock_code ON posts(stock_code)')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_posts_publish_time ON posts(publish_time)')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_comments_post_id ON comments(post_id)')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_replies_comment_id ON replies(comment_id)')

        self.conn.commit()

    # ==================== 接口1：获取帖子列表 ====================

    def get_post_list(self, page: int = 1, page_size: int = 80) -> Optional[List[Dict]]:
        """
        获取帖子列表（使用正确的API）
        对应接口：https://gbapi.eastmoney.com/webarticlelist/api/Article/Articlelist
        """
        url = f"{self.gbapi_url}/webarticlelist/api/Article/Articlelist"

        # 动态生成callback
        callback = f"jsonp_{int(time.time() * 1000)}_{random.randint(100, 999)}"

        params = {
            'code': self.stock_code,
            'type': 0,
            'ps': page_size,
            'p': page,
            'sort': 1,
            'callback': callback
        }

        try:
            print(f"请求帖子列表 - 页码: {page}, 大小: {page_size}")
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()

            text = response.text
            print(f"原始响应长度: {len(text)} 字符")

            data = self.parse_jsonp_response(text)

            if not data:
                print("解析JSONP响应失败")
                return None

            # 从're'字段获取帖子列表
            posts = data.get('re', [])

            print(f"获取到 {len(posts)} 个帖子")
            return posts

        except Exception as e:
            print(f"获取帖子列表异常: {e}")
            return None

    def parse_jsonp_response(self, response_text: str) -> Optional[Dict]:
        """
        解析JSONP响应，返回JSON对象
        处理格式: jsonp_123456_abc(...)
        返回: 解析后的字典或None
        """
        try:
            text = response_text.strip()

            # 1. 如果是标准JSONP格式
            if text.startswith('jsonp_'):
                # 找到第一个括号和最后一个括号
                start_idx = text.find('(')
                end_idx = text.rfind(')')

                if start_idx != -1 and end_idx != -1:
                    json_str = text[start_idx + 1:end_idx]
                    return json.loads(json_str)

            # 2. 尝试正则匹配（更通用）
            match = re.search(r'jsonp_\d+_\w+\((.+)\)', text, re.DOTALL)
            if match:
                json_str = match.group(1).strip()
                return json.loads(json_str)

            # 3. 可能已经是纯JSON了
            return json.loads(text)

        except json.JSONDecodeError as e:
            print(f"JSONP解析失败: {e}")
            print(f"原始文本前200字符: {response_text[:200]}")
            return None
        except Exception as e:
            print(f"解析异常: {e}")
            return None

    def parse_post_data(self, post_item: Dict) -> Optional[Dict]:
        """解析单个帖子数据"""
        try:
            post_id = str(post_item.get('post_id') or post_item.get('id') or '')
            if not post_id:
                return None

            # 提取帖子信息
            post = {
                'post_id': post_id,
                'stock_code': self.stock_code,
                'title': post_item.get('post_title', ''),
                'abstract': post_item.get('abstract', ''),
                'content': post_item.get('content', ''),
                'publish_time': post_item.get('post_publish_time') or post_item.get('publish_time') or '',
                'update_time': post_item.get('post_last_time') or '',
                'user_id': str(post_item.get('user_id') or post_item.get('author_id') or ''),
                'user_nickname': post_item.get('user_nickname') or post_item.get('author') or '',
                'user_level': post_item.get('user_level') or post_item.get('level') or 0,
                'click_count': post_item.get('click_count') or post_item.get('view_count') or 0,
                'comment_count': post_item.get('comment_count') or post_item.get('reply_count') or 0,
                'forward_count': post_item.get('forward_count') or 0,
                'like_count': post_item.get('like_count') or post_item.get('praise_count') or 0,
                'is_top': 1 if post_item.get('is_top') else 0,
                'is_hot': 1 if post_item.get('is_hot') else 0,
                'is_essence': 1 if post_item.get('is_essence') or post_item.get('is_good') else 0,
                'source_type': post_item.get('source_type', 0),
                'tags': json.dumps(post_item.get('tags', []), ensure_ascii=False) if post_item.get('tags') else '',
            }

            return post

        except Exception as e:
            print(f"解析帖子数据失败: {e}")
            return None

    def save_post(self, post: Dict):
        """保存帖子到数据库"""
        try:
            self.cursor.execute('''
            INSERT OR REPLACE INTO posts
            (post_id, stock_code, title, abstract, content, publish_time, update_time,
             user_id, user_nickname, user_level, click_count, comment_count, forward_count,
             like_count, is_top, is_hot, is_essence, source_type, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                post['post_id'],
                post['stock_code'],
                post['title'],
                post['abstract'],
                post['content'],
                post['publish_time'],
                post['update_time'],
                post['user_id'],
                post['user_nickname'],
                post['user_level'],
                post['click_count'],
                post['comment_count'],
                post['forward_count'],
                post['like_count'],
                post['is_top'],
                post['is_hot'],
                post['is_essence'],
                post['source_type'],
                post['tags']
            ))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"保存帖子失败 {post['post_id']}: {e}")
            return False

    # ==================== 接口2：获取帖子评论 ====================

    def get_post_comments(self, post_id: str, page: int = 1, page_size: int = 30) -> Optional[Dict]:
        """
        获取帖子评论（使用正确的API）
        对应接口：https://guba.eastmoney.com/api/getData?code=301293&path=reply/api/Reply/ArticleNewReplyList
        """
        url = f"{self.base_url}/api/getData"

        # URL参数
        query_params = {
            'code': self.stock_code,
            'path': 'reply/api/Reply/ArticleNewReplyList'
        }

        # POST body参数（严格按照抓包格式）
        param_str = f"postid={post_id}&sort=1&sorttype=1&p={page}&ps={page_size}"
        encoded_param = quote(param_str, safe='=&')

        post_data = {
            'param': encoded_param,
            'plat': 'Web',
            'path': 'reply/api/Reply/ArticleNewReplyList',
            'env': '2',
            'origin': '',
            'version': '2022',
            'product': 'Guba'
        }

        # 设置特定的请求头
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': self.base_url,
            'Referer': f'{self.base_url}/news,{self.stock_code},{post_id}.html',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty',
        }

        full_url = f"{url}?{urlencode(query_params)}"

        try:
            print(f"获取帖子 {post_id} 第 {page} 页评论")
            response = self.session.post(full_url, data=post_data, headers=headers, timeout=30)
            response.raise_for_status()

            data = response.json()

            if isinstance(data, dict) and data.get('success') is not None and not data.get('success'):
                print(f"API调用失败: {data.get('message', '未知错误')}")
                return None

            print(f"成功获取评论数据，响应大小: {len(str(data))} 字节")
            return data

        except requests.exceptions.RequestException as e:
            print(f"获取评论失败: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"JSON解析失败: {e}")
            print(f"响应内容前500字符: {response.text[:500]}")
            return None

    def parse_comments_data(self, data: Dict, post_id: str) -> Tuple[List[Dict], List[Dict]]:
        """
        解析评论数据（根据实际API结构）
        """
        comments = []
        replies = []

        try:
            print(f"开始解析评论数据，数据键: {list(data.keys())}")

            # 根据抓包数据，评论数据可能在不同的键中
            comment_list = None

            # 尝试不同的键名
            possible_keys = ['re', 'data', 'list', 'comments', 'replys']
            for key in possible_keys:
                if key in data and isinstance(data[key], list):
                    comment_list = data[key]
                    print(f"在 '{key}' 键中找到 {len(comment_list)} 条数据")
                    break

            if comment_list is None:
                # 如果找不到列表，尝试直接使用数据（如果是列表）
                if isinstance(data, list):
                    comment_list = data
                else:
                    print(f"未找到评论数据列表")
                    return comments, replies

            print(f"开始解析 {len(comment_list)} 条评论...")

            for idx, item in enumerate(comment_list):
                # 解析主评论
                comment = self.parse_single_comment(item, post_id, idx + 1)
                if comment:
                    comments.append(comment)

                # 解析子回复
                child_keys = ['child_replys', 'replies', 'sub_replys', 'children']
                child_list = None

                for key in child_keys:
                    if key in item and isinstance(item[key], list):
                        child_list = item[key]
                        break

                if child_list:
                    for reply_idx, reply_item in enumerate(child_list):
                        reply = self.parse_single_reply(
                            reply_item,
                            comment['comment_id'] if comment else str(item.get('id', '')),
                            post_id,
                            reply_idx + 1
                        )
                        if reply:
                            replies.append(reply)

            print(f"解析完成: {len(comments)} 条评论, {len(replies)} 条回复")
            return comments, replies

        except Exception as e:
            print(f"解析评论数据失败: {e}")
            import traceback
            traceback.print_exc()
            return comments, replies

    def parse_single_comment(self, item: Dict, post_id: str, floor: int) -> Optional[Dict]:
        """解析单条评论"""
        try:
            # 使用实际API字段名
            comment_id = str(item.get('reply_id', ''))
            content = item.get('reply_text', '')
            publish_time = item.get('reply_time') or item.get('reply_publish_time', '')

            # 用户信息可能在 reply_user 对象内
            user_info = item.get('reply_user', {})
            user_id = user_info.get('user_id', item.get('user_id', ''))
            user_nickname = user_info.get('user_nickname', item.get('user_nickname', ''))

            # 评论状态信息
            like_count = item.get('reply_like_count', 0)
            is_author = 1 if item.get('reply_is_author') else 0

            # IP和设备信息
            ip_address = item.get('reply_ip_address', '')
            device_type = self._get_device_type(item.get('reply_from', 0))

            comment = {
                'comment_id': f"{post_id}_{comment_id}" if comment_id else f"{post_id}_cmt_{floor}",
                'post_id': post_id,
                'parent_comment_id': item.get('parent_id', ''),
                'user_id': user_id,
                'user_nickname': user_nickname,
                'user_level': item.get('user_level', 0),
                'content': content,
                'publish_time': publish_time,
                'like_count': like_count,
                'reply_count': len(item.get('child_replys', [])),
                'floor_number': floor,
                'is_author': is_author,
                'is_recommend': 1 if item.get('reply_is_amazing') else 0,
                'ip_address': ip_address,
                'device_type': device_type,
                'status': 1
            }

            return comment

        except Exception as e:
            print(f"解析单条评论失败: {e}")
            return None

    def parse_single_reply(self, item: Dict, comment_id: str, post_id: str, floor: int) -> Optional[Dict]:
        """解析单条回复"""
        try:
            reply_id = str(item.get('reply_id', f"{comment_id}_rep_{floor}"))
            content = item.get('reply_text', '')

            # 用户信息
            user_info = item.get('reply_user', {})
            user_id = user_info.get('user_id', item.get('user_id', ''))
            user_nickname = user_info.get('user_nickname', item.get('user_nickname', ''))

            # 目标用户
            target_user_id = item.get('target_user_id', '')
            target_user_nickname = item.get('target_user_nickname', '')

            # 清理内容：移除@用户的部分
            if target_user_nickname and content.startswith(f"@{target_user_nickname}"):
                content = content.replace(f"@{target_user_nickname}", "", 1).strip()

            reply = {
                'reply_id': reply_id,
                'comment_id': comment_id,
                'post_id': post_id,
                'parent_reply_id': item.get('parent_id', ''),
                'user_id': user_id,
                'user_nickname': user_nickname,
                'target_user_id': target_user_id,
                'target_user_nickname': target_user_nickname,
                'content': content,
                'publish_time': item.get('reply_time') or item.get('reply_publish_time', ''),
                'like_count': item.get('reply_like_count', 0),
                'floor_number': floor,
                'ip_address': item.get('reply_ip_address', ''),
                'device_type': self._get_device_type(item.get('reply_from', 0)),
                'status': 1
            }

            return reply

        except Exception as e:
            print(f"解析单条回复失败: {e}")
            return None

    def _get_device_type(self, from_code: int) -> str:
        """根据reply_from代码获取设备类型"""
        device_map = {
            31: "Android",
            32: "iPhone",
            46: "网页端",
            42: "iPad",
            112: "PC客户端"
        }
        return device_map.get(from_code, f"未知({from_code})")

    def save_comments(self, comments: List[Dict]):
        """保存评论到数据库"""
        saved_count = 0
        for comment in comments:
            try:
                self.cursor.execute('''
                INSERT OR REPLACE INTO comments
                (comment_id, post_id, parent_comment_id, user_id, user_nickname,
                 user_level, content, publish_time, like_count, reply_count,
                 floor_number, is_author, is_recommend, ip_address, device_type, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    comment['comment_id'],
                    comment['post_id'],
                    comment['parent_comment_id'],
                    comment['user_id'],
                    comment['user_nickname'],
                    comment['user_level'],
                    comment['content'],
                    comment['publish_time'],
                    comment['like_count'],
                    comment['reply_count'],
                    comment['floor_number'],
                    comment['is_author'],
                    comment['is_recommend'],
                    comment['ip_address'],
                    comment['device_type'],
                    comment['status']
                ))
                saved_count += 1
            except Exception as e:
                print(f"保存评论失败 {comment.get('comment_id', 'unknown')}: {e}")

        self.conn.commit()
        print(f"成功保存 {saved_count}/{len(comments)} 条评论")

    def save_replies(self, replies: List[Dict]):
        """保存回复到数据库"""
        saved_count = 0
        for reply in replies:
            try:
                self.cursor.execute('''
                INSERT OR REPLACE INTO replies
                (reply_id, comment_id, post_id, parent_reply_id, user_id, user_nickname,
                 target_user_id, target_user_nickname, content, publish_time, like_count,
                 floor_number, ip_address, device_type, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    reply['reply_id'],
                    reply['comment_id'],
                    reply['post_id'],
                    reply['parent_reply_id'],
                    reply['user_id'],
                    reply['user_nickname'],
                    reply['target_user_id'],
                    reply['target_user_nickname'],
                    reply['content'],
                    reply['publish_time'],
                    reply['like_count'],
                    reply['floor_number'],
                    reply['ip_address'],
                    reply['device_type'],
                    reply['status']
                ))
                saved_count += 1
            except Exception as e:
                print(f"保存回复失败 {reply.get('reply_id', 'unknown')}: {e}")

        self.conn.commit()
        print(f"成功保存 {saved_count}/{len(replies)} 条回复")

    # ==================== 主爬取逻辑 ====================

    def crawl(self, max_pages: int = 10, max_posts: int = 100,
              include_comments: bool = True, delay: float = 1.0):
        """
        执行爬取任务

        Args:
            max_pages: 最大页数
            max_posts: 最大帖子数
            include_comments: 是否爬取评论
            delay: 请求延迟（秒）

        Returns:
            爬取统计信息
        """
        stats = {
            'posts_count': 0,
            'comments_count': 0,
            'replies_count': 0,
            'errors': []
        }

        post_count = 0

        for page in range(1, max_pages + 1):
            if post_count >= max_posts:
                break

            print(f"\n{'='*60}")
            print(f"正在爬取第 {page} 页...")
            print(f"{'='*60}")

            posts = self.get_post_list(page)
            if not posts:
                print("未获取到帖子，停止爬取")
                break

            for post_item in posts:
                if post_count >= max_posts:
                    break

                # 解析并保存帖子
                post = self.parse_post_data(post_item)
                if post and post['post_id'] not in self.crawled_posts:
                    if self.save_post(post):
                        self.crawled_posts.add(post['post_id'])
                        stats['posts_count'] += 1
                        post_count += 1
                        print(f"✅ 保存帖子: {post['title'][:30]}...")

                        # 爬取评论
                        if include_comments:
                            time.sleep(delay)
                            comment_data = self.get_post_comments(post['post_id'])
                            if comment_data:
                                comments, replies = self.parse_comments_data(comment_data, post['post_id'])

                                if comments:
                                    self.save_comments(comments)
                                    stats['comments_count'] += len(comments)

                                if replies:
                                    self.save_replies(replies)
                                    stats['replies_count'] += len(replies)

                time.sleep(delay)

        print(f"\n{'='*60}")
        print("爬取完成！")
        print(f"帖子: {stats['posts_count']}")
        print(f"评论: {stats['comments_count']}")
        print(f"回复: {stats['replies_count']}")
        print(f"{'='*60}\n")

        return stats

    def close(self):
        """关闭数据库连接"""
        if hasattr(self, 'conn'):
            self.conn.close()

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()
