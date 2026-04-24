# -*- coding: utf-8 -*-
"""
极简版用户管理器
专注于：用户身份识别 + 个性化订阅
不包含：付费、会员等级、Token管理
"""

import sqlite3
import json
from datetime import datetime
from typing import Optional, Dict, List, Tuple
from pathlib import Path


class MinimalUserManager:
    """极简版用户管理器 - 仅保留核心功能"""

    def __init__(self, db_path: str):
        """
        初始化

        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """初始化数据库"""
        schema_path = Path(__file__).parent.parent / "db" / "schema_minimal.sql"

        if schema_path.exists():
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema_sql = f.read()

            conn = sqlite3.connect(self.db_path)
            conn.executescript(schema_sql)
            conn.close()

    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # ============================================
    # 用户管理
    # ============================================

    def register_user(
        self,
        user_id: str,
        channel: str,
        username: Optional[str] = None,
        telegram_id: Optional[str] = None,
        telegram_username: Optional[str] = None,
        wechat_openid: Optional[str] = None
    ) -> Dict:
        """
        注册用户（自动创建）

        Args:
            user_id: 用户唯一标识
            channel: 注册渠道(telegram/wechat/web/anonymous)
            username: 昵称（可选）
            telegram_id: Telegram ID（可选）
            telegram_username: Telegram用户名（可选）
            wechat_openid: 微信OpenID（可选）

        Returns:
            注册结果
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # 检查是否已存在
        cursor.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,))
        if cursor.fetchone():
            conn.close()
            return {
                'success': True,
                'message': '用户已存在',
                'user_id': user_id,
                'is_new': False
            }

        # 创建新用户
        now = datetime.now().isoformat()
        cursor.execute("""
            INSERT INTO users (
                user_id, username, channel,
                telegram_id, telegram_username, wechat_openid,
                status, created_at, last_active_at
            ) VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?)
        """, (
            user_id, username, channel,
            telegram_id, telegram_username, wechat_openid,
            now, now
        ))

        conn.commit()
        conn.close()

        return {
            'success': True,
            'message': '注册成功',
            'user_id': user_id,
            'is_new': True,
            'channel': channel
        }

    def get_user_info(self, user_id: str) -> Optional[Dict]:
        """
        查询用户信息

        Args:
            user_id: 用户ID

        Returns:
            用户信息字典
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT user_id, username, channel,
                   telegram_id, telegram_username, wechat_openid,
                   status, created_at, last_active_at
            FROM users WHERE user_id = ?
        """, (user_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return {
            'user_id': row['user_id'],
            'username': row['username'],
            'channel': row['channel'],
            'telegram_id': row['telegram_id'],
            'telegram_username': row['telegram_username'],
            'wechat_openid': row['wechat_openid'],
            'status': row['status'],
            'created_at': row['created_at'],
            'last_active_at': row['last_active_at']
        }

    def user_exists(self, user_id: str) -> bool:
        """检查用户是否存在"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM users WHERE user_id = ? LIMIT 1", (user_id,))
        exists = cursor.fetchone() is not None
        conn.close()
        return exists

    def update_last_active(self, user_id: str):
        """更新用户最后活跃时间"""
        conn = self._get_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute(
            "UPDATE users SET last_active_at = ? WHERE user_id = ?",
            (now, user_id)
        )
        conn.commit()
        conn.close()

    # ============================================
    # 订阅管理
    # ============================================

    def create_subscription(
        self,
        user_id: str,
        subscription_type: str,
        target: str,
        platforms: List[str],
        push_channels: List[str],
        target_display_name: Optional[str] = None,
        push_frequency: str = 'realtime'
    ) -> Tuple[bool, str, Optional[int]]:
        """
        创建订阅

        Args:
            user_id: 用户ID
            subscription_type: 订阅类型(stock/topic/keyword)
            target: 目标内容
            platforms: 数据源平台列表
            push_channels: 推送渠道列表
            target_display_name: 显示名称
            push_frequency: 推送频率

        Returns:
            (成功?, 消息, 订阅ID)
        """
        # 检查用户是否存在
        if not self.user_exists(user_id):
            return False, "用户不存在", None

        conn = self._get_connection()
        cursor = conn.cursor()

        # 检查是否已订阅
        cursor.execute("""
            SELECT id FROM subscriptions
            WHERE user_id = ? AND target = ? AND status = 'active'
        """, (user_id, target))

        if cursor.fetchone():
            conn.close()
            return False, "已订阅该内容", None

        # 创建订阅
        now = datetime.now().isoformat()
        cursor.execute("""
            INSERT INTO subscriptions (
                user_id, subscription_type, target, target_display_name,
                platforms, push_enabled, push_channels, push_frequency,
                status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, 1, ?, ?, 'active', ?, ?)
        """, (
            user_id, subscription_type, target, target_display_name,
            json.dumps(platforms), json.dumps(push_channels), push_frequency,
            now, now
        ))

        subscription_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return True, "订阅创建成功", subscription_id

    def get_user_subscriptions(
        self,
        user_id: str,
        status: str = 'active'
    ) -> List[Dict]:
        """
        查询用户订阅列表

        Args:
            user_id: 用户ID
            status: 订阅状态(active/paused/all)

        Returns:
            订阅列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        if status == 'all':
            cursor.execute("""
                SELECT * FROM subscriptions WHERE user_id = ?
                ORDER BY created_at DESC
            """, (user_id,))
        else:
            cursor.execute("""
                SELECT * FROM subscriptions WHERE user_id = ? AND status = ?
                ORDER BY created_at DESC
            """, (user_id, status))

        rows = cursor.fetchall()
        conn.close()

        return [
            {
                'id': row['id'],
                'type': row['subscription_type'],
                'target': row['target'],
                'display_name': row['target_display_name'],
                'platforms': json.loads(row['platforms']),
                'push_enabled': bool(row['push_enabled']),
                'push_channels': json.loads(row['push_channels']),
                'push_frequency': row['push_frequency'],
                'status': row['status'],
                'last_push_at': row['last_push_at'],
                'created_at': row['created_at']
            }
            for row in rows
        ]

    def get_all_active_subscriptions(self) -> List[Dict]:
        """
        获取所有活跃订阅（用于定时任务爬取）

        Returns:
            所有活跃订阅列表（含用户信息）
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT s.*, u.channel, u.telegram_id, u.wechat_openid
            FROM subscriptions s
            JOIN users u ON s.user_id = u.user_id
            WHERE s.status = 'active' AND u.status = 'active'
            ORDER BY s.created_at
        """)

        rows = cursor.fetchall()
        conn.close()

        return [
            {
                'id': row['id'],
                'user_id': row['user_id'],
                'type': row['subscription_type'],
                'target': row['target'],
                'display_name': row['target_display_name'],
                'platforms': json.loads(row['platforms']),
                'push_channels': json.loads(row['push_channels']),
                'push_frequency': row['push_frequency'],
                'last_push_at': row['last_push_at'],
                'user_channel': row['channel'],
                'telegram_id': row['telegram_id'],
                'wechat_openid': row['wechat_openid']
            }
            for row in rows
        ]

    def update_subscription_status(
        self,
        subscription_id: int,
        status: str
    ) -> Tuple[bool, str]:
        """
        更新订阅状态

        Args:
            subscription_id: 订阅ID
            status: 新状态(active/paused)

        Returns:
            (成功?, 消息)
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        now = datetime.now().isoformat()
        cursor.execute("""
            UPDATE subscriptions
            SET status = ?, updated_at = ?
            WHERE id = ?
        """, (status, now, subscription_id))

        if cursor.rowcount == 0:
            conn.close()
            return False, "订阅不存在"

        conn.commit()
        conn.close()

        return True, f"订阅状态已更新为{status}"

    def delete_subscription(self, subscription_id: int) -> Tuple[bool, str]:
        """删除订阅"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM subscriptions WHERE id = ?", (subscription_id,))

        if cursor.rowcount == 0:
            conn.close()
            return False, "订阅不存在"

        conn.commit()
        conn.close()

        return True, "订阅已删除"

    def update_last_push(self, subscription_id: int):
        """更新最后推送时间"""
        conn = self._get_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute(
            "UPDATE subscriptions SET last_push_at = ? WHERE id = ?",
            (now, subscription_id)
        )
        conn.commit()
        conn.close()

    # ============================================
    # 统计查询
    # ============================================

    def get_user_stats(self, user_id: str) -> Dict:
        """获取用户统计信息"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # 订阅数
        cursor.execute(
            "SELECT COUNT(*) as count FROM subscriptions WHERE user_id = ? AND status = 'active'",
            (user_id,)
        )
        subscription_count = cursor.fetchone()['count']

        conn.close()

        return {
            'subscription_count': subscription_count
        }


# ============================================
# 使用示例
# ============================================

if __name__ == "__main__":
    # 示例：如何使用极简版UserManager

    user_mgr = MinimalUserManager("/tmp/test_minimal.db")

    # 1. Telegram用户注册
    telegram_user_id = "telegram_123456789"
    result = user_mgr.register_user(
        user_id=telegram_user_id,
        channel='telegram',
        username='张三',
        telegram_id='123456789',
        telegram_username='zhangsan'
    )
    print(f"注册结果: {result}")

    # 2. 创建订阅
    success, msg, sub_id = user_mgr.create_subscription(
        user_id=telegram_user_id,
        subscription_type='stock',
        target='TSLA',
        target_display_name='特斯拉',
        platforms=['eastmoney'],
        push_channels=['telegram']
    )
    print(f"订阅结果: {msg}, ID: {sub_id}")

    # 3. 查询订阅列表
    subs = user_mgr.get_user_subscriptions(telegram_user_id)
    print(f"订阅列表: {subs}")

    # 4. 获取所有活跃订阅（用于定时任务）
    all_subs = user_mgr.get_all_active_subscriptions()
    print(f"所有活跃订阅: {len(all_subs)}个")
