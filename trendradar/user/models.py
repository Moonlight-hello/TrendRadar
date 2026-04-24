# coding=utf-8
"""
用户数据模型
"""

from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime


@dataclass
class User:
    """用户模型"""
    user_id: str
    username: Optional[str] = None
    channel: str = "telegram"
    telegram_id: Optional[str] = None
    telegram_username: Optional[str] = None
    wechat_openid: Optional[str] = None
    status: str = "active"
    created_at: Optional[datetime] = None
    last_active_at: Optional[datetime] = None


@dataclass
class Membership:
    """会员模型"""
    user_id: str
    membership_type: str = "free"  # free/basic/pro/enterprise
    status: str = "active"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    auto_renew: bool = False


@dataclass
class Subscription:
    """订阅模型"""
    id: Optional[int] = None
    user_id: str = ""
    subscription_type: str = "stock"  # stock/topic/keyword
    target: str = ""
    target_display_name: Optional[str] = None
    platforms: List[str] = None
    push_enabled: bool = True
    push_channels: List[str] = None
    push_frequency: str = "realtime"  # realtime/hourly/daily
    status: str = "active"  # active/paused/cancelled
    created_at: Optional[datetime] = None
    last_push_at: Optional[datetime] = None

    def __post_init__(self):
        if self.platforms is None:
            self.platforms = ["eastmoney"]
        if self.push_channels is None:
            self.push_channels = ["telegram"]
