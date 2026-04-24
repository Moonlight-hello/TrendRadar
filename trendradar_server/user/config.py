# -*- coding: utf-8 -*-
"""
用户模块配置
"""

import os
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# 数据库配置
DB_PATH = os.getenv(
    'TRENDRADAR_DB_PATH',
    str(PROJECT_ROOT / 'data' / 'trendradar.db')
)

# Telegram Bot配置
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')

# Webhook配置（生产环境使用）
WEBHOOK_URL = os.getenv('WEBHOOK_URL', '')  # 例如: https://your-domain.com/webhook
WEBHOOK_PORT = int(os.getenv('WEBHOOK_PORT', '8443'))

# Bot命令前缀
COMMAND_PREFIX = '/'

# 默认平台
DEFAULT_PLATFORMS = ['eastmoney']

# 推送频率选项
PUSH_FREQUENCIES = {
    'realtime': '实时推送',
    'hourly': '每小时',
    'daily': '每日推送',
    'weekly': '每周推送'
}

# 订阅类型
SUBSCRIPTION_TYPES = {
    'stock': '股票',
    'keyword': '关键词',
    'topic': '话题',
    'hashtag': '标签'
}
