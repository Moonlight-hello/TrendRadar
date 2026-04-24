# -*- coding: utf-8 -*-
"""
推送服务 - 负责向用户发送通知
支持Telegram、微信等多渠道
"""

import asyncio
from typing import List, Dict, Tuple
from user.manager import MinimalUserManager
from user.telegram_bot import TrendRadarBot


class PushService:
    """推送服务"""

    def __init__(self, user_manager: MinimalUserManager, telegram_bot: TrendRadarBot = None):
        """
        初始化推送服务

        Args:
            user_manager: 用户管理器
            telegram_bot: Telegram Bot实例（可选）
        """
        self.user_mgr = user_manager
        self.telegram_bot = telegram_bot

    async def push_to_user(
        self,
        user_id: str,
        subscription_id: int,
        title: str,
        content: str
    ) -> Tuple[bool, str]:
        """
        推送消息给指定用户

        Args:
            user_id: 用户ID
            subscription_id: 订阅ID
            title: 标题
            content: 内容

        Returns:
            (成功?, 消息)
        """
        # 获取用户信息
        user_info = self.user_mgr.get_user_info(user_id)
        if not user_info:
            return False, "用户不存在"

        channel = user_info['channel']

        # 根据渠道推送
        if channel == 'telegram':
            return await self._push_telegram(user_info, title, content)
        elif channel == 'wechat':
            return await self._push_wechat(user_info, title, content)
        else:
            return False, f"不支持的推送渠道: {channel}"

    async def _push_telegram(
        self,
        user_info: Dict,
        title: str,
        content: str
    ) -> Tuple[bool, str]:
        """推送到Telegram"""
        if not self.telegram_bot:
            return False, "Telegram Bot未初始化"

        telegram_id = user_info['telegram_id']
        if not telegram_id:
            return False, "Telegram ID不存在"

        return await self.telegram_bot.send_notification(
            telegram_id=telegram_id,
            title=title,
            content=content
        )

    async def _push_wechat(
        self,
        user_info: Dict,
        title: str,
        content: str
    ) -> Tuple[bool, str]:
        """推送到微信（待实现）"""
        # TODO: 实现微信推送
        return False, "微信推送暂未实现"

    async def push_batch(
        self,
        notifications: List[Dict]
    ) -> Dict[str, Tuple[bool, str]]:
        """
        批量推送

        Args:
            notifications: 推送列表
                [{
                    'user_id': 'telegram_123',
                    'subscription_id': 1,
                    'title': '特斯拉更新',
                    'content': '...'
                }]

        Returns:
            {user_id: (成功?, 消息)}
        """
        results = {}

        for notif in notifications:
            success, msg = await self.push_to_user(
                user_id=notif['user_id'],
                subscription_id=notif['subscription_id'],
                title=notif['title'],
                content=notif['content']
            )
            results[notif['user_id']] = (success, msg)

        return results

    def format_notification(
        self,
        subscription: Dict,
        analysis: Dict
    ) -> Tuple[str, str]:
        """
        格式化推送内容

        Args:
            subscription: 订阅信息
            analysis: AI分析结果

        Returns:
            (标题, 内容)
        """
        target = subscription['display_name'] or subscription['target']

        title = f"📊 {target} 最新分析"

        content = (
            f"**{target}** 更新\n"
            f"─────────────────\n\n"
            f"📝 **AI摘要**:\n{analysis.get('summary', '暂无摘要')}\n\n"
            f"😊 **市场情绪**: {self._format_sentiment(analysis.get('sentiment', 'neutral'))}\n\n"
        )

        if 'keywords' in analysis and analysis['keywords']:
            keywords = ", ".join(analysis['keywords'][:5])
            content += f"🔥 **热词**: {keywords}\n\n"

        content += f"🕐 更新时间: {analysis.get('created_at', '')[:16]}"

        return title, content

    def _format_sentiment(self, sentiment: str) -> str:
        """格式化情感"""
        sentiment_map = {
            'positive': '积极 😊',
            'negative': '消极 😟',
            'neutral': '中性 😐'
        }
        return sentiment_map.get(sentiment, sentiment)


# ============================================
# 使用示例
# ============================================

if __name__ == "__main__":
    import os
    from user.manager import MinimalUserManager
    from user.telegram_bot import TrendRadarBot

    # 初始化
    user_mgr = MinimalUserManager("/tmp/test_push.db")
    bot = TrendRadarBot(
        token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
        db_path="/tmp/test_push.db"
    )
    bot.setup()

    push_service = PushService(user_mgr, bot)

    # 示例：推送消息
    async def test_push():
        # 注册测试用户
        user_mgr.register_user(
            user_id="telegram_123456",
            channel="telegram",
            telegram_id="123456"
        )

        # 推送消息
        success, msg = await push_service.push_to_user(
            user_id="telegram_123456",
            subscription_id=1,
            title="测试推送",
            content="这是一条测试消息"
        )

        print(f"推送结果: {success}, {msg}")

    # 运行测试
    # asyncio.run(test_push())
