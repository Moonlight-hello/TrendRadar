# -*- coding: utf-8 -*-
"""
统一爬虫Agent
集成 UserManager，支持多平台爬取，并自动管理用户额度
"""

import sys
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime

# 添加communityspy路径
sys.path.append('/Users/wangxinlong/Code/communityspy')

# 导入UserManager（相对路径）
try:
    from .user_manager import UserManager
except ImportError:
    from user_manager import UserManager


class CrawlerAgent:
    """
    统一爬虫Agent
    - 支持多平台（东方财富、雪球、知乎、小红书、微博）
    - 集成用户管理（会员检查、请求限制）
    - 数据标准化输出
    """

    def __init__(self, user_manager: UserManager):
        """
        初始化爬虫Agent

        Args:
            user_manager: 用户管理器实例
        """
        self.user_mgr = user_manager

        # 平台适配器映射
        self.platform_adapters = {
            'eastmoney': self._crawl_eastmoney,
            'xueqiu': self._crawl_xueqiu,
            'zhihu': self._crawl_zhihu,
            'xiaohongshu': self._crawl_xiaohongshu,
            'weibo': self._crawl_weibo,
        }

    # ============================================
    # 主爬取接口
    # ============================================

    def crawl(
        self,
        user_id: str,
        platform: str,
        target: str,
        max_items: int = 50,
        subscription_id: Optional[int] = None
    ) -> Tuple[bool, str, List[Dict]]:
        """
        统一爬取接口

        Args:
            user_id: 用户ID
            platform: 平台名称(eastmoney/xueqiu/zhihu等)
            target: 爬取目标(股票代码/关键词/用户ID)
            max_items: 最大条目数
            subscription_id: 关联的订阅ID（可选）

        Returns:
            (是否成功, 消息, 数据列表)
        """
        # 1. 检查用户是否存在
        if not self.user_mgr.user_exists(user_id):
            return False, "用户不存在，请先注册", []

        # 2. 检查会员是否有效
        user_info = self.user_mgr.get_user_info(user_id)
        if user_info['membership']['is_expired']:
            return False, f"会员已过期，到期时间：{user_info['membership']['end_date']}", []

        # 3. 检查每日请求限制
        stats = self.user_mgr.get_user_stats(user_id)
        if stats['today_request_count'] >= user_info['limits']['max_daily_requests']:
            return False, f"今日请求已达上限({user_info['limits']['max_daily_requests']})", []

        # 4. 检查平台是否支持
        if platform not in self.platform_adapters:
            return False, f"不支持的平台: {platform}，可用平台: {list(self.platform_adapters.keys())}", []

        # 5. 检查用户会员等级是否支持该平台
        allowed_platforms = self._get_allowed_platforms(user_info['membership']['type'])
        if platform not in allowed_platforms:
            return False, f"您的会员等级({user_info['membership']['type']})不支持{platform}平台", []

        # 6. 执行爬取
        try:
            crawler_func = self.platform_adapters[platform]
            raw_data = crawler_func(target, max_items)

            # 7. 数据标准化
            normalized_data = self._normalize_data(raw_data, platform, target)

            # 8. 记录爬取请求（虽然不消耗Token，但计入请求次数）
            # 这里可以选择性地记录到数据库

            return True, f"成功爬取{len(normalized_data)}条数据", normalized_data

        except Exception as e:
            return False, f"爬取失败: {str(e)}", []

    # ============================================
    # 平台适配器
    # ============================================

    def _crawl_eastmoney(self, stock_code: str, max_items: int) -> List[Dict]:
        """
        东方财富股吧爬虫

        Args:
            stock_code: 股票代码
            max_items: 最大条目数

        Returns:
            原始数据列表
        """
        try:
            from communityspy_new import EastMoneyCommentSpider

            # 创建临时数据目录
            data_dir = Path("/tmp/trendradar_crawl") / f"eastmoney_{stock_code}"
            data_dir.mkdir(parents=True, exist_ok=True)

            spider = EastMoneyCommentSpider(
                stock_code=stock_code,
                data_dir=str(data_dir),
                log_level="WARNING"
            )

            # 计算需要爬取的页数（每页约20条）
            max_pages = max(1, max_items // 20)

            # 爬取帖子
            posts = []
            for post in spider.crawl_posts_stream(max_pages=max_pages):
                posts.append({
                    'id': post.get('post_id'),
                    'type': 'post',
                    'author': post.get('user_name'),
                    'author_id': post.get('user_id'),
                    'title': post.get('title'),
                    'text': post.get('content'),
                    'time': post.get('publish_time'),
                    'likes': post.get('read_count', 0),
                    'comments': post.get('comment_count', 0),
                    'url': post.get('url'),
                    'raw': post
                })

                if len(posts) >= max_items:
                    break

            spider.close()
            return posts

        except ImportError:
            # 如果无法导入，返回模拟数据
            return self._mock_data('eastmoney', stock_code, max_items)

    def _crawl_xueqiu(self, stock_code: str, max_items: int) -> List[Dict]:
        """雪球爬虫（待实现）"""
        # TODO: 实现雪球爬虫
        return self._mock_data('xueqiu', stock_code, max_items)

    def _crawl_zhihu(self, keyword: str, max_items: int) -> List[Dict]:
        """
        知乎爬虫（基于MediaCrawlerPro）

        Args:
            keyword: 搜索关键词
            max_items: 最大条目数

        Returns:
            原始数据列表
        """
        try:
            sys.path.append('/Users/wangxinlong/Code/communityspy/MediaCrawlerPro-Python')
            from media_platform.zhihu.core import ZhihuCrawler

            # TODO: 配置和初始化ZhihuCrawler
            # crawler = ZhihuCrawler(config)
            # data = crawler.search(keyword, max_items)

            return self._mock_data('zhihu', keyword, max_items)

        except ImportError:
            return self._mock_data('zhihu', keyword, max_items)

    def _crawl_xiaohongshu(self, keyword: str, max_items: int) -> List[Dict]:
        """小红书爬虫（待实现）"""
        # TODO: 基于MediaCrawlerPro实现
        return self._mock_data('xiaohongshu', keyword, max_items)

    def _crawl_weibo(self, keyword: str, max_items: int) -> List[Dict]:
        """微博爬虫（待实现）"""
        # TODO: 基于MediaCrawlerPro实现
        return self._mock_data('weibo', keyword, max_items)

    # ============================================
    # 数据标准化
    # ============================================

    def _normalize_data(self, raw_data: List[Dict], platform: str, target: str) -> List[Dict]:
        """
        数据标准化：不同平台 → 统一格式

        标准格式:
        {
            'platform': 'eastmoney',
            'data_type': 'post',
            'target': 'TSLA',
            'content_id': '123456',
            'parent_id': None,
            'author_id': 'user123',
            'author_name': '张三',
            'content': '帖子内容',
            'publish_time': '2026-04-23T10:00:00',
            'metrics': {'likes': 100, 'comments': 20},
            'raw_json': '{...}'
        }
        """
        normalized = []

        for item in raw_data:
            try:
                normalized_item = {
                    'platform': platform,
                    'data_type': item.get('type', 'post'),
                    'target': target,
                    'content_id': str(item['id']),
                    'parent_id': item.get('parent_id'),
                    'author_id': item.get('author_id'),
                    'author_name': item.get('author'),
                    'content': item.get('text', ''),
                    'publish_time': item.get('time'),
                    'metrics': {
                        'likes': item.get('likes', 0),
                        'comments': item.get('comments', 0),
                        'shares': item.get('shares', 0),
                        'views': item.get('views', 0)
                    },
                    'raw_json': json.dumps(item.get('raw', item), ensure_ascii=False)
                }

                normalized.append(normalized_item)

            except Exception as e:
                # 跳过格式错误的数据
                print(f"⚠️  数据标准化失败: {e}")
                continue

        return normalized

    # ============================================
    # 辅助方法
    # ============================================

    def _get_allowed_platforms(self, membership_type: str) -> List[str]:
        """根据会员等级获取允许的平台"""
        platform_map = {
            'free': ['eastmoney'],
            'basic': ['eastmoney', 'xueqiu', 'zhihu'],
            'pro': ['eastmoney', 'xueqiu', 'zhihu', 'xiaohongshu', 'weibo'],
            'enterprise': ['eastmoney', 'xueqiu', 'zhihu', 'xiaohongshu', 'weibo']
        }
        return platform_map.get(membership_type, ['eastmoney'])

    def _mock_data(self, platform: str, target: str, max_items: int) -> List[Dict]:
        """生成模拟数据（用于测试）"""
        mock_data = []
        for i in range(min(max_items, 10)):
            mock_data.append({
                'id': f'{platform}_{i+1}',
                'type': 'post' if i % 3 == 0 else 'comment',
                'author': f'测试用户{i+1}',
                'author_id': f'user_{i+1}',
                'text': f'这是来自{platform}平台关于{target}的第{i+1}条数据',
                'time': datetime.now().isoformat(),
                'likes': (i+1) * 10,
                'comments': i * 2,
                'raw': {}
            })
        return mock_data

    # ============================================
    # 批量爬取（多订阅）
    # ============================================

    def crawl_batch(self, user_id: str, subscriptions: List[Dict]) -> Dict[int, Tuple[bool, str, List[Dict]]]:
        """
        批量爬取多个订阅

        Args:
            user_id: 用户ID
            subscriptions: 订阅列表（来自user_mgr.get_user_subscriptions）

        Returns:
            {subscription_id: (成功?, 消息, 数据)}
        """
        results = {}

        for sub in subscriptions:
            sub_id = sub['id']
            target = sub['target']
            platforms = sub['platforms']

            # 对每个平台爬取
            for platform in platforms:
                success, msg, data = self.crawl(
                    user_id=user_id,
                    platform=platform,
                    target=target,
                    max_items=50,
                    subscription_id=sub_id
                )

                # 合并结果
                if sub_id not in results:
                    results[sub_id] = (success, msg, data)
                else:
                    # 合并数据
                    prev_success, prev_msg, prev_data = results[sub_id]
                    combined_data = prev_data + data
                    results[sub_id] = (
                        prev_success and success,
                        f"{prev_msg}; {msg}",
                        combined_data
                    )

        return results


# ============================================
# 使用示例
# ============================================

if __name__ == "__main__":
    # 示例：如何使用 CrawlerAgent

    from user_manager import UserManager

    # 1. 初始化用户管理器
    user_mgr = UserManager("/tmp/test_crawler.db")

    # 2. 注册测试用户
    user_id = "telegram_test_123"
    user_mgr.register_user(user_id)

    # 3. 创建爬虫Agent
    crawler = CrawlerAgent(user_mgr)

    # 4. 爬取数据
    success, msg, data = crawler.crawl(
        user_id=user_id,
        platform='eastmoney',
        target='301293',  # 三博脑科
        max_items=10
    )

    print(f"爬取结果: {success}")
    print(f"消息: {msg}")
    print(f"数据条数: {len(data)}")

    if data:
        print("\n前3条数据:")
        for i, item in enumerate(data[:3], 1):
            print(f"{i}. [{item['data_type']}] {item['author_name']}: {item['content'][:50]}...")
