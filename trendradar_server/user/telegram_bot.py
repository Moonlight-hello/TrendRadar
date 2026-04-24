# -*- coding: utf-8 -*-
"""
Telegram Bot - 用户交互入口
提供命令处理、订阅管理、消息推送
"""

import os
import sys
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent))

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from user.manager import MinimalUserManager
from typing import List


class TrendRadarBot:
    """TrendRadar Telegram Bot"""

    def __init__(self, token: str, db_path: str):
        """
        初始化Bot

        Args:
            token: Telegram Bot Token
            db_path: 数据库路径
        """
        self.token = token
        self.user_mgr = MinimalUserManager(db_path)
        self.app = None

    def _get_user_id(self, update: Update) -> str:
        """从Update中提取用户ID"""
        telegram_id = update.effective_user.id
        return f"telegram_{telegram_id}"

    # ============================================
    # 命令处理
    # ============================================

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /start - 启动命令

        用户首次使用时自动注册
        """
        user = update.effective_user
        user_id = self._get_user_id(update)

        # 自动注册用户
        result = self.user_mgr.register_user(
            user_id=user_id,
            channel='telegram',
            username=user.first_name,
            telegram_id=str(user.id),
            telegram_username=user.username
        )

        # 更新活跃时间
        self.user_mgr.update_last_active(user_id)

        welcome_text = (
            f"👋 欢迎 {user.first_name}！\n\n"
            f"🎯 **TrendRadar** - 股票讨论智能追踪\n\n"
            f"{'🎉 首次注册成功！' if result['is_new'] else '✅ 欢迎回来！'}\n\n"
            f"📋 **快速开始**:\n"
            f"• /subscribe 订阅股票\n"
            f"• /list 查看订阅列表\n"
            f"• /help 查看帮助\n\n"
            f"💡 例如: /subscribe TSLA"
        )

        await update.message.reply_text(
            welcome_text,
            parse_mode='Markdown'
        )

    async def subscribe(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /subscribe <股票代码> - 订阅股票

        示例:
            /subscribe TSLA
            /subscribe 特斯拉
            /subscribe 301293
        """
        user_id = self._get_user_id(update)

        # 检查参数
        if not context.args:
            await update.message.reply_text(
                "❌ 请提供股票代码\n\n"
                "用法: /subscribe <股票代码>\n"
                "示例: /subscribe TSLA"
            )
            return

        target = context.args[0].upper()

        # 创建订阅
        success, msg, sub_id = self.user_mgr.create_subscription(
            user_id=user_id,
            subscription_type='stock',
            target=target,
            target_display_name=target,
            platforms=['eastmoney'],  # 默认东方财富
            push_channels=['telegram']
        )

        if success:
            await update.message.reply_text(
                f"✅ 订阅成功！\n\n"
                f"📊 股票: {target}\n"
                f"🔔 订阅ID: {sub_id}\n"
                f"📡 数据源: 东方财富股吧\n\n"
                f"系统将自动推送该股票的最新讨论和AI分析。"
            )
        else:
            await update.message.reply_text(f"❌ {msg}")

        # 更新活跃时间
        self.user_mgr.update_last_active(user_id)

    async def list_subscriptions(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /list - 查看订阅列表
        """
        user_id = self._get_user_id(update)

        # 查询订阅
        subs = self.user_mgr.get_user_subscriptions(user_id)

        if not subs:
            await update.message.reply_text(
                "📭 您还没有订阅任何股票\n\n"
                "使用 /subscribe TSLA 开始订阅"
            )
            return

        # 构建订阅列表
        text = f"📋 您的订阅列表 ({len(subs)}个)\n\n"

        for i, sub in enumerate(subs, 1):
            status_icon = "✅" if sub['status'] == 'active' else "⏸️"
            platforms = ", ".join(sub['platforms'])

            text += (
                f"{i}. {status_icon} **{sub['display_name']}** ({sub['target']})\n"
                f"   📡 数据源: {platforms}\n"
                f"   🔔 推送: {'开启' if sub['push_enabled'] else '关闭'}\n"
                f"   🆔 ID: {sub['id']}\n\n"
            )

        text += "💡 使用 /unsubscribe <ID> 取消订阅"

        await update.message.reply_text(text, parse_mode='Markdown')

        # 更新活跃时间
        self.user_mgr.update_last_active(user_id)

    async def unsubscribe(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /unsubscribe <订阅ID> - 取消订阅

        示例:
            /unsubscribe 1
        """
        user_id = self._get_user_id(update)

        # 检查参数
        if not context.args:
            await update.message.reply_text(
                "❌ 请提供订阅ID\n\n"
                "用法: /unsubscribe <订阅ID>\n"
                "使用 /list 查看订阅ID"
            )
            return

        try:
            sub_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ 订阅ID必须是数字")
            return

        # 删除订阅
        success, msg = self.user_mgr.delete_subscription(sub_id)

        if success:
            await update.message.reply_text(f"✅ {msg}")
        else:
            await update.message.reply_text(f"❌ {msg}")

        # 更新活跃时间
        self.user_mgr.update_last_active(user_id)

    async def pause(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /pause <订阅ID> - 暂停订阅推送

        示例:
            /pause 1
        """
        user_id = self._get_user_id(update)

        if not context.args:
            await update.message.reply_text(
                "❌ 请提供订阅ID\n\n"
                "用法: /pause <订阅ID>"
            )
            return

        try:
            sub_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ 订阅ID必须是数字")
            return

        # 暂停订阅
        success, msg = self.user_mgr.update_subscription_status(sub_id, 'paused')

        if success:
            await update.message.reply_text(f"⏸️ 订阅已暂停")
        else:
            await update.message.reply_text(f"❌ {msg}")

        self.user_mgr.update_last_active(user_id)

    async def resume(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /resume <订阅ID> - 恢复订阅推送

        示例:
            /resume 1
        """
        user_id = self._get_user_id(update)

        if not context.args:
            await update.message.reply_text(
                "❌ 请提供订阅ID\n\n"
                "用法: /resume <订阅ID>"
            )
            return

        try:
            sub_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ 订阅ID必须是数字")
            return

        # 恢复订阅
        success, msg = self.user_mgr.update_subscription_status(sub_id, 'active')

        if success:
            await update.message.reply_text(f"▶️ 订阅已恢复")
        else:
            await update.message.reply_text(f"❌ {msg}")

        self.user_mgr.update_last_active(user_id)

    async def stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /stats - 查看统计信息
        """
        user_id = self._get_user_id(update)

        # 获取用户信息和统计
        user_info = self.user_mgr.get_user_info(user_id)
        stats = self.user_mgr.get_user_stats(user_id)

        if not user_info:
            await update.message.reply_text("❌ 用户不存在")
            return

        text = (
            f"📊 **您的统计信息**\n\n"
            f"👤 用户: {user_info['username']}\n"
            f"🆔 ID: {user_id}\n"
            f"📅 注册时间: {user_info['created_at'][:10]}\n"
            f"🕐 最后活跃: {user_info['last_active_at'][:16] if user_info['last_active_at'] else '未知'}\n\n"
            f"📋 活跃订阅数: {stats['subscription_count']}\n"
        )

        await update.message.reply_text(text, parse_mode='Markdown')

        self.user_mgr.update_last_active(user_id)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /help - 帮助信息
        """
        help_text = (
            "📖 **TrendRadar 使用指南**\n\n"
            "**基础命令**:\n"
            "• /start - 开始使用\n"
            "• /subscribe <代码> - 订阅股票\n"
            "• /list - 查看订阅列表\n"
            "• /unsubscribe <ID> - 取消订阅\n\n"
            "**管理命令**:\n"
            "• /pause <ID> - 暂停订阅\n"
            "• /resume <ID> - 恢复订阅\n"
            "• /stats - 查看统计\n"
            "• /help - 显示帮助\n\n"
            "**使用示例**:\n"
            "1️⃣ 订阅特斯拉:\n"
            "   /subscribe TSLA\n\n"
            "2️⃣ 查看订阅:\n"
            "   /list\n\n"
            "3️⃣ 取消订阅:\n"
            "   /unsubscribe 1\n\n"
            "💡 **提示**: 系统会自动推送您关注股票的最新讨论和AI分析。"
        )

        await update.message.reply_text(help_text, parse_mode='Markdown')

    # ============================================
    # 消息推送（供后端调用）
    # ============================================

    async def send_notification(
        self,
        telegram_id: str,
        title: str,
        content: str,
        parse_mode: str = 'Markdown'
    ):
        """
        发送推送消息（供后端调用）

        Args:
            telegram_id: Telegram用户ID
            title: 标题
            content: 内容
            parse_mode: 解析模式
        """
        message = f"**{title}**\n\n{content}"

        try:
            await self.app.bot.send_message(
                chat_id=int(telegram_id),
                text=message,
                parse_mode=parse_mode
            )
            return True, "发送成功"
        except Exception as e:
            return False, f"发送失败: {str(e)}"

    # ============================================
    # 启动和运行
    # ============================================

    def setup(self):
        """设置Bot命令处理器"""
        self.app = Application.builder().token(self.token).build()

        # 注册命令处理器
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("subscribe", self.subscribe))
        self.app.add_handler(CommandHandler("list", self.list_subscriptions))
        self.app.add_handler(CommandHandler("unsubscribe", self.unsubscribe))
        self.app.add_handler(CommandHandler("pause", self.pause))
        self.app.add_handler(CommandHandler("resume", self.resume))
        self.app.add_handler(CommandHandler("stats", self.stats))
        self.app.add_handler(CommandHandler("help", self.help_command))

        print("✅ Bot命令处理器已设置")

    def run(self):
        """运行Bot（阻塞模式）"""
        if not self.app:
            self.setup()

        print(f"🚀 TrendRadar Bot 启动中...")
        print(f"📂 数据库: {self.user_mgr.db_path}")
        print(f"✅ Bot已启动，按Ctrl+C停止")

        self.app.run_polling(allowed_updates=Update.ALL_TYPES)

    async def start_webhook(self, webhook_url: str, port: int = 8443):
        """运行Bot（Webhook模式，用于生产环境）"""
        if not self.app:
            self.setup()

        await self.app.bot.set_webhook(url=webhook_url)
        await self.app.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path=self.token
        )


# ============================================
# 主程序入口
# ============================================

if __name__ == "__main__":
    # 从环境变量读取配置
    BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN")
    DB_PATH = os.getenv("DB_PATH", "/tmp/trendradar_bot.db")

    if BOT_TOKEN == "YOUR_BOT_TOKEN":
        print("❌ 请设置环境变量 TELEGRAM_BOT_TOKEN")
        print("   export TELEGRAM_BOT_TOKEN='your_bot_token'")
        sys.exit(1)

    # 创建并运行Bot
    bot = TrendRadarBot(token=BOT_TOKEN, db_path=DB_PATH)
    bot.run()
