"""
用户管理工具类
供其他Agent调用的核心类，不依赖FastAPI
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
from pathlib import Path
import sys

# 添加config路径
sys.path.append(str(Path(__file__).parent.parent))
from config.membership_rules import (
    get_membership_config,
    calculate_token_cost,
    check_membership_limit
)


class UserManager:
    """用户管理器 - 封装所有用户相关操作"""

    def __init__(self, db_path: str):
        """
        初始化用户管理器

        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """初始化数据库（如果表不存在则创建）"""
        schema_path = Path(__file__).parent.parent / "db" / "schema_simple.sql"

        if schema_path.exists():
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema_sql = f.read()

            conn = sqlite3.connect(self.db_path)
            conn.executescript(schema_sql)
            conn.close()

    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 返回字典格式
        return conn

    # ============================================
    # 用户注册和查询
    # ============================================

    def register_user(self, user_id: str, channel: str = 'telegram') -> Dict:
        """
        注册新用户（如果已存在则返回现有用户）

        Args:
            user_id: 用户唯一标识
            channel: 注册渠道

        Returns:
            用户信息字典
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # 检查用户是否存在
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        existing = cursor.fetchone()

        if existing:
            conn.close()
            return {
                'success': True,
                'message': '用户已存在',
                'user_id': user_id,
                'is_new': False
            }

        # 创建新用户（免费版，10000 tokens）
        free_config = get_membership_config('free')

        cursor.execute("""
            INSERT INTO users (
                user_id, membership_type, membership_status,
                token_balance, max_subscriptions, max_daily_requests
            ) VALUES (?, 'free', 'active', ?, ?, ?)
        """, (
            user_id,
            free_config['initial_tokens'],
            free_config['max_subscriptions'],
            free_config['max_daily_requests']
        ))

        conn.commit()
        conn.close()

        return {
            'success': True,
            'message': '注册成功',
            'user_id': user_id,
            'is_new': True,
            'membership': 'free',
            'token_balance': free_config['initial_tokens'],
            'welcome_message': f"欢迎使用TrendRadar！您已获得{free_config['initial_tokens']}个免费Token。"
        }

    def get_user_info(self, user_id: str) -> Optional[Dict]:
        """
        查询用户详细信息

        Args:
            user_id: 用户ID

        Returns:
            用户信息字典，如果不存在返回None
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                user_id, username, email, phone,
                membership_type, membership_status,
                membership_start_date, membership_end_date,
                token_balance, token_total_purchased, token_total_consumed,
                max_subscriptions, max_daily_requests, status,
                created_at, updated_at, last_login_at
            FROM users WHERE user_id = ?
        """, (user_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        # 检查会员是否过期
        membership_expired = False
        if row['membership_end_date']:
            end_date = datetime.fromisoformat(row['membership_end_date'])
            membership_expired = end_date < datetime.now()

        return {
            'user_id': row['user_id'],
            'username': row['username'],
            'email': row['email'],
            'phone': row['phone'],
            'membership': {
                'type': row['membership_type'],
                'status': 'expired' if membership_expired else row['membership_status'],
                'start_date': row['membership_start_date'],
                'end_date': row['membership_end_date'],
                'is_expired': membership_expired
            },
            'token': {
                'balance': row['token_balance'],
                'total_purchased': row['token_total_purchased'],
                'total_consumed': row['token_total_consumed']
            },
            'limits': {
                'max_subscriptions': row['max_subscriptions'],
                'max_daily_requests': row['max_daily_requests']
            },
            'status': row['status'],
            'created_at': row['created_at'],
            'last_login': row['last_login_at']
        }

    def user_exists(self, user_id: str) -> bool:
        """检查用户是否存在"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM users WHERE user_id = ? LIMIT 1", (user_id,))
        exists = cursor.fetchone() is not None
        conn.close()
        return exists

    def update_last_login(self, user_id: str):
        """更新用户最后登录时间"""
        conn = self._get_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute(
            "UPDATE users SET last_login_at = ?, updated_at = ? WHERE user_id = ?",
            (now, now, user_id)
        )
        conn.commit()
        conn.close()

    # ============================================
    # Token管理
    # ============================================

    def get_token_balance(self, user_id: str) -> int:
        """
        查询用户Token余额

        Returns:
            Token余额，用户不存在返回0
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT token_balance FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        return row['token_balance'] if row else 0

    def deduct_token(
        self,
        user_id: str,
        amount: int,
        operation: str,
        model: str,
        subscription_id: Optional[int] = None,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        request_summary: Optional[str] = None
    ) -> Tuple[bool, str, Dict]:
        """
        扣除用户Token

        Args:
            user_id: 用户ID
            amount: 扣除数量
            operation: 操作类型(analyze/summarize/verify/chat)
            model: 使用的模型名称
            subscription_id: 关联订阅ID（可选）
            prompt_tokens: 输入token数
            completion_tokens: 输出token数
            request_summary: 请求摘要（可选）

        Returns:
            (是否成功, 错误信息, 结果信息)
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # 查询当前余额
        cursor.execute("SELECT token_balance FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            return False, "用户不存在", {}

        current_balance = row['token_balance']

        if current_balance < amount:
            conn.close()
            return False, f"Token余额不足，当前余额：{current_balance}，需要：{amount}", {
                'current_balance': current_balance,
                'required': amount,
                'shortage': amount - current_balance
            }

        # 扣除Token
        new_balance = current_balance - amount
        cursor.execute("""
            UPDATE users
            SET token_balance = ?,
                token_total_consumed = token_total_consumed + ?,
                updated_at = ?
            WHERE user_id = ?
        """, (new_balance, amount, datetime.now().isoformat(), user_id))

        # 计算成本
        cost = calculate_token_cost(model, amount)

        # 记录消耗
        cursor.execute("""
            INSERT INTO token_usage (
                user_id, subscription_id, operation_type, model,
                prompt_tokens, completion_tokens, total_tokens,
                cost_amount, request_content
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id, subscription_id, operation, model,
            prompt_tokens, completion_tokens, amount,
            cost, request_summary
        ))

        conn.commit()
        conn.close()

        return True, "扣除成功", {
            'deducted': amount,
            'remaining_balance': new_balance,
            'cost': cost,
            'model': model
        }

    def add_token(
        self,
        user_id: str,
        amount: int,
        source: str = 'purchase',
        transaction_id: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        增加用户Token（充值或赠送）

        Args:
            user_id: 用户ID
            amount: 增加数量
            source: 来源(purchase/gift/refund)
            transaction_id: 交易ID

        Returns:
            (是否成功, 消息)
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE users
            SET token_balance = token_balance + ?,
                token_total_purchased = token_total_purchased + ?,
                updated_at = ?
            WHERE user_id = ?
        """, (amount, amount, datetime.now().isoformat(), user_id))

        if cursor.rowcount == 0:
            conn.close()
            return False, "用户不存在"

        conn.commit()
        conn.close()

        return True, f"成功添加{amount}个Token"

    def get_token_history(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict]:
        """
        查询Token消耗历史

        Args:
            user_id: 用户ID
            limit: 返回条数
            offset: 偏移量

        Returns:
            消耗记录列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                id, subscription_id, operation_type, model,
                prompt_tokens, completion_tokens, total_tokens,
                cost_amount, created_at
            FROM token_usage
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """, (user_id, limit, offset))

        rows = cursor.fetchall()
        conn.close()

        return [
            {
                'id': row['id'],
                'subscription_id': row['subscription_id'],
                'operation': row['operation_type'],
                'model': row['model'],
                'tokens': {
                    'prompt': row['prompt_tokens'],
                    'completion': row['completion_tokens'],
                    'total': row['total_tokens']
                },
                'cost': row['cost_amount'],
                'time': row['created_at']
            }
            for row in rows
        ]

    # ============================================
    # 会员管理
    # ============================================

    def upgrade_membership(
        self,
        user_id: str,
        membership_type: str,
        duration_months: int = 1
    ) -> Tuple[bool, str]:
        """
        升级用户会员

        Args:
            user_id: 用户ID
            membership_type: 会员类型(basic/pro/enterprise)
            duration_months: 时长(月)

        Returns:
            (是否成功, 消息)
        """
        if membership_type not in ['basic', 'pro', 'enterprise']:
            return False, "无效的会员类型"

        conn = self._get_connection()
        cursor = conn.cursor()

        # 获取会员配置
        config = get_membership_config(membership_type)

        # 计算开始和结束日期
        now = datetime.now()
        start_date = now.isoformat()
        end_date = (now + timedelta(days=30 * duration_months)).isoformat()

        # 更新用户会员信息
        cursor.execute("""
            UPDATE users
            SET membership_type = ?,
                membership_status = 'active',
                membership_start_date = ?,
                membership_end_date = ?,
                max_subscriptions = ?,
                max_daily_requests = ?,
                token_balance = token_balance + ?,
                updated_at = ?
            WHERE user_id = ?
        """, (
            membership_type,
            start_date,
            end_date,
            config['max_subscriptions'],
            config['max_daily_requests'],
            config['monthly_tokens'],
            now.isoformat(),
            user_id
        ))

        if cursor.rowcount == 0:
            conn.close()
            return False, "用户不存在"

        conn.commit()
        conn.close()

        return True, f"成功升级为{config['name']}，有效期至{end_date[:10]}"

    def check_membership_valid(self, user_id: str) -> bool:
        """检查用户会员是否有效（未过期）"""
        user_info = self.get_user_info(user_id)
        if not user_info:
            return False

        return not user_info['membership']['is_expired']

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
        push_frequency: str = 'realtime',
        target_display_name: Optional[str] = None,
        filters: Optional[Dict] = None
    ) -> Tuple[bool, str, Optional[int]]:
        """
        创建订阅

        Args:
            user_id: 用户ID
            subscription_type: 订阅类型(stock/topic/keyword)
            target: 目标内容
            platforms: 数据源平台列表
            push_channels: 推送渠道列表
            push_frequency: 推送频率
            target_display_name: 显示名称
            filters: 过滤规则

        Returns:
            (是否成功, 消息, 订阅ID)
        """
        # 检查用户是否存在
        user_info = self.get_user_info(user_id)
        if not user_info:
            return False, "用户不存在", None

        # 检查订阅数限制
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) as count FROM subscriptions WHERE user_id = ? AND status = 'active'",
            (user_id,)
        )
        current_count = cursor.fetchone()['count']

        if current_count >= user_info['limits']['max_subscriptions']:
            conn.close()
            return False, f"已达到最大订阅数限制({user_info['limits']['max_subscriptions']})", None

        # 创建订阅
        cursor.execute("""
            INSERT INTO subscriptions (
                user_id, subscription_type, target, target_display_name,
                platforms, push_channels, push_frequency, filters, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active')
        """, (
            user_id, subscription_type, target, target_display_name,
            json.dumps(platforms), json.dumps(push_channels),
            push_frequency, json.dumps(filters) if filters else None
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
        查询用户的订阅列表

        Args:
            user_id: 用户ID
            status: 订阅状态过滤(active/paused/cancelled/all)

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
                'push_channels': json.loads(row['push_channels']),
                'push_frequency': row['push_frequency'],
                'status': row['status'],
                'last_crawl_at': row['last_crawl_at'],
                'last_push_at': row['last_push_at'],
                'created_at': row['created_at']
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
            status: 新状态(active/paused/cancelled)

        Returns:
            (是否成功, 消息)
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE subscriptions
            SET status = ?, updated_at = ?
            WHERE id = ?
        """, (status, datetime.now().isoformat(), subscription_id))

        if cursor.rowcount == 0:
            conn.close()
            return False, "订阅不存在"

        conn.commit()
        conn.close()

        return True, f"订阅状态已更新为{status}"

    # ============================================
    # 统计查询
    # ============================================

    def get_user_stats(self, user_id: str) -> Dict:
        """
        获取用户统计信息

        Returns:
            统计信息字典
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # 订阅数
        cursor.execute(
            "SELECT COUNT(*) as count FROM subscriptions WHERE user_id = ? AND status = 'active'",
            (user_id,)
        )
        subscription_count = cursor.fetchone()['count']

        # 今日Token消耗
        today_start = datetime.now().replace(hour=0, minute=0, second=0).isoformat()
        cursor.execute("""
            SELECT COALESCE(SUM(total_tokens), 0) as total
            FROM token_usage
            WHERE user_id = ? AND created_at >= ?
        """, (user_id, today_start))
        today_tokens = cursor.fetchone()['total']

        # 今日请求次数
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM token_usage
            WHERE user_id = ? AND created_at >= ?
        """, (user_id, today_start))
        today_requests = cursor.fetchone()['count']

        conn.close()

        return {
            'subscription_count': subscription_count,
            'today_tokens_consumed': today_tokens,
            'today_request_count': today_requests
        }
