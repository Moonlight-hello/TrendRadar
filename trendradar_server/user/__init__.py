# -*- coding: utf-8 -*-
"""
User Module - 用户管理模块

提供用户身份识别、订阅管理、消息推送等功能
"""

from .manager import MinimalUserManager

# 可选导入（需要安装 python-telegram-bot）
try:
    from .telegram_bot import TrendRadarBot
    from .push_service import PushService
    __all__ = ['MinimalUserManager', 'TrendRadarBot', 'PushService']
except ImportError:
    __all__ = ['MinimalUserManager']

__version__ = "1.0.0"
