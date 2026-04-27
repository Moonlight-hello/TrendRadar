#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票监控服务 - 后端API
支持用户订阅、定时爬取、Webhook推送
"""

import asyncio
import json
import sqlite3
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
import uvicorn
import httpx

# 添加项目路径
import sys
sys.path.insert(0, str(Path(__file__).parent))

from trendradar.crawler.eastmoney import crawl_eastmoney_stock


# ============================================================================
# 配置
# ============================================================================

DB_PATH = "eastmoney_stocks.db"
SUBSCRIPTIONS_DB = "subscriptions.db"
DEFAULT_CRAWL_INTERVAL = 300  # 默认5分钟爬取一次


# ============================================================================
# 数据模型
# ============================================================================

class SubscribeRequest(BaseModel):
    """订阅请求"""
    stock_code: str
    webhook_url: HttpUrl
    webhook_type: str = "feishu"  # feishu/dingtalk/wechat/generic
    user_id: Optional[str] = None
    interval: int = 300  # 爬取间隔（秒）


class UnsubscribeRequest(BaseModel):
    """取消订阅请求"""
    stock_code: str
    user_id: Optional[str] = None


class SubscriptionInfo(BaseModel):
    """订阅信息"""
    id: int
    stock_code: str
    webhook_url: str
    webhook_type: str
    user_id: Optional[str]
    interval: int
    last_crawl_time: Optional[str]
    status: str
    created_at: str


# ============================================================================
# 数据库管理
# ============================================================================

class StockDatabase:
    """股票数据库"""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id TEXT UNIQUE,
                stock_code TEXT,
                title TEXT,
                content TEXT,
                publish_time TIMESTAMP,
                user_id TEXT,
                user_nickname TEXT,
                click_count INTEGER DEFAULT 0,
                comment_count INTEGER DEFAULT 0,
                like_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                comment_id TEXT UNIQUE,
                post_id TEXT,
                content TEXT,
                publish_time TIMESTAMP,
                user_id TEXT,
                user_nickname TEXT,
                like_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_posts_stock_code ON posts(stock_code)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_posts_publish_time ON posts(publish_time)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_comments_post_id ON comments(post_id)")

        conn.commit()
        conn.close()

    def save_data(self, data: Dict) -> Dict:
        """保存数据并返回新增数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        stock_code = data['stock_code']
        posts = data['posts']
        comments = data['comments']

        new_posts = []
        new_comments = []

        for post in posts:
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO posts
                    (post_id, stock_code, title, content, publish_time, user_id, user_nickname,
                     click_count, comment_count, like_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    post.get('post_id'),
                    stock_code,
                    post.get('title'),
                    post.get('content', ''),
                    post.get('publish_time'),
                    post.get('author_id'),
                    post.get('author_name'),
                    post.get('read_count', 0),
                    post.get('comment_count', 0),
                    post.get('like_count', 0)
                ))

                if cursor.rowcount > 0:
                    new_posts.append(post)
            except Exception as e:
                print(f"保存帖子失败: {e}")

        for comment in comments:
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO comments
                    (comment_id, post_id, content, publish_time, user_id, user_nickname, like_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    comment.get('comment_id'),
                    comment.get('post_id'),
                    comment.get('content'),
                    comment.get('create_time'),
                    comment.get('author_id'),
                    comment.get('author_name'),
                    comment.get('like_count', 0)
                ))

                if cursor.rowcount > 0:
                    new_comments.append(comment)
            except Exception as e:
                print(f"保存评论失败: {e}")

        conn.commit()
        conn.close()

        return {
            "new_posts": new_posts,
            "new_comments": new_comments
        }

    def get_latest_posts(self, stock_code: str, limit: int = 10) -> List[Dict]:
        """获取最新帖子"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT post_id, title, user_nickname, publish_time, comment_count, click_count
            FROM posts
            WHERE stock_code=?
            ORDER BY publish_time DESC
            LIMIT ?
        """, (stock_code, limit))

        posts = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return posts

    def get_stats(self, stock_code: str) -> Dict:
        """获取统计信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*) as post_count, MAX(publish_time) as latest
            FROM posts WHERE stock_code=?
        """, (stock_code,))
        row = cursor.fetchone()

        cursor.execute("""
            SELECT COUNT(*) FROM comments
            WHERE post_id IN (SELECT post_id FROM posts WHERE stock_code=?)
        """, (stock_code,))
        comment_count = cursor.fetchone()[0]

        conn.close()

        return {
            "stock_code": stock_code,
            "post_count": row[0],
            "comment_count": comment_count,
            "latest_post_time": row[1]
        }


class SubscriptionDatabase:
    """订阅数据库"""

    def __init__(self, db_path: str = SUBSCRIPTIONS_DB):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """初始化订阅数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_code TEXT NOT NULL,
                webhook_url TEXT NOT NULL,
                webhook_type TEXT DEFAULT 'generic',
                user_id TEXT,
                interval INTEGER DEFAULT 300,
                last_crawl_time TIMESTAMP,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(stock_code, webhook_url)
            )
        """)

        conn.commit()
        conn.close()

    def add_subscription(self, data: SubscribeRequest) -> int:
        """添加订阅"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO subscriptions (stock_code, webhook_url, webhook_type, user_id, interval)
                VALUES (?, ?, ?, ?, ?)
            """, (data.stock_code, str(data.webhook_url), data.webhook_type, data.user_id, data.interval))

            sub_id = cursor.lastrowid
            conn.commit()
            return sub_id

        except sqlite3.IntegrityError:
            # 已存在，更新
            cursor.execute("""
                UPDATE subscriptions
                SET webhook_type=?, user_id=?, interval=?, status='active'
                WHERE stock_code=? AND webhook_url=?
            """, (data.webhook_type, data.user_id, data.interval, data.stock_code, str(data.webhook_url)))

            conn.commit()
            cursor.execute("""
                SELECT id FROM subscriptions WHERE stock_code=? AND webhook_url=?
            """, (data.stock_code, str(data.webhook_url)))
            sub_id = cursor.fetchone()[0]
            return sub_id

        finally:
            conn.close()

    def remove_subscription(self, stock_code: str, user_id: Optional[str] = None) -> bool:
        """移除订阅"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if user_id:
            cursor.execute("""
                UPDATE subscriptions SET status='inactive'
                WHERE stock_code=? AND user_id=?
            """, (stock_code, user_id))
        else:
            cursor.execute("""
                UPDATE subscriptions SET status='inactive'
                WHERE stock_code=?
            """, (stock_code,))

        affected = cursor.rowcount
        conn.commit()
        conn.close()

        return affected > 0

    def get_all_active_subscriptions(self) -> List[Dict]:
        """获取所有活跃订阅"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM subscriptions WHERE status='active'
        """)

        subs = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return subs

    def get_user_subscriptions(self, user_id: str) -> List[Dict]:
        """获取用户订阅"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM subscriptions WHERE user_id=? AND status='active'
        """, (user_id,))

        subs = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return subs

    def update_crawl_time(self, sub_id: int):
        """更新爬取时间"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE subscriptions SET last_crawl_time=? WHERE id=?
        """, (datetime.now().isoformat(), sub_id))

        conn.commit()
        conn.close()


# ============================================================================
# Webhook 推送
# ============================================================================

async def send_webhook(webhook_url: str, webhook_type: str, content: str, title: str = "股票监控提醒"):
    """发送Webhook"""
    async with httpx.AsyncClient() as client:
        try:
            if webhook_type == "feishu":
                # 飞书格式
                data = {
                    "msg_type": "interactive",
                    "card": {
                        "header": {
                            "title": {"tag": "plain_text", "content": title},
                            "template": "blue"
                        },
                        "elements": [
                            {
                                "tag": "markdown",
                                "content": content
                            }
                        ]
                    }
                }

            elif webhook_type == "dingtalk":
                # 钉钉格式
                data = {
                    "msgtype": "markdown",
                    "markdown": {
                        "title": title,
                        "text": content
                    }
                }

            elif webhook_type == "wechat":
                # 企业微信格式
                data = {
                    "msgtype": "markdown",
                    "markdown": {
                        "content": content
                    }
                }

            else:
                # 通用格式
                data = {
                    "title": title,
                    "content": content
                }

            response = await client.post(webhook_url, json=data, timeout=10)
            response.raise_for_status()
            print(f"✅ Webhook推送成功: {webhook_url[:50]}...")
            return True

        except Exception as e:
            print(f"❌ Webhook推送失败: {e}")
            return False


def generate_report(stock_code: str, new_posts: List, new_comments: List, stats: Dict) -> str:
    """生成推送报告"""
    report = f"# 📊 股票 {stock_code} 监控报告\n\n"
    report += f"**更新时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

    # 统计信息
    report += f"## 📈 统计信息\n"
    report += f"- 总帖子: {stats['post_count']} 条\n"
    report += f"- 总评论: {stats['comment_count']} 条\n"
    report += f"- 最新时间: {stats['latest_post_time']}\n\n"

    # 新增帖子
    if new_posts:
        report += f"## 🆕 新增帖子 ({len(new_posts)}条)\n"
        for i, post in enumerate(new_posts[:5], 1):
            report += f"{i}. **{post['title']}**\n"
            report += f"   - 作者: {post['author_name']}\n"
            report += f"   - 评论: {post['comment_count']} | 阅读: {post['read_count']}\n"
            report += f"   - 时间: {post['publish_time']}\n\n"

    # 新增评论
    if new_comments:
        report += f"## 💬 新增评论 ({len(new_comments)}条)\n"
        for i, comment in enumerate(new_comments[:5], 1):
            content = comment['content'][:50] + "..." if len(comment['content']) > 50 else comment['content']
            report += f"{i}. {comment['author_name']}: {content}\n"

    if not new_posts and not new_comments:
        report += "## ℹ️ 暂无新增内容\n"

    return report


# ============================================================================
# FastAPI 应用
# ============================================================================

app = FastAPI(title="股票监控服务", version="1.0.0", description="支持用户订阅、定时爬取、Webhook推送")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局对象
stock_db = StockDatabase()
sub_db = SubscriptionDatabase()
monitor_tasks = {}


# ============================================================================
# API 路由
# ============================================================================

@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "股票监控服务",
        "version": "1.0.0",
        "endpoints": {
            "订阅": "POST /api/subscribe",
            "取消订阅": "POST /api/unsubscribe",
            "我的订阅": "GET /api/subscriptions/{user_id}",
            "查看统计": "GET /api/stocks/{stock_code}/stats",
            "手动触发": "POST /api/trigger/{stock_code}"
        }
    }


@app.post("/api/subscribe")
async def subscribe(request: SubscribeRequest, background_tasks: BackgroundTasks):
    """
    订阅股票监控
    用户提供webhook_url，后台定时爬取并推送
    """
    try:
        sub_id = sub_db.add_subscription(request)

        # 立即触发一次爬取
        background_tasks.add_task(crawl_and_notify_single, sub_id)

        return {
            "success": True,
            "subscription_id": sub_id,
            "message": f"已订阅股票 {request.stock_code}，每 {request.interval}秒 更新一次"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/unsubscribe")
async def unsubscribe(request: UnsubscribeRequest):
    """取消订阅"""
    success = sub_db.remove_subscription(request.stock_code, request.user_id)

    if success:
        return {"success": True, "message": f"已取消订阅 {request.stock_code}"}
    else:
        raise HTTPException(status_code=404, detail="未找到该订阅")


@app.get("/api/subscriptions/{user_id}")
async def get_user_subscriptions(user_id: str):
    """获取用户的所有订阅"""
    subs = sub_db.get_user_subscriptions(user_id)
    return {"user_id": user_id, "count": len(subs), "subscriptions": subs}


@app.get("/api/stocks/{stock_code}/stats")
async def get_stock_stats(stock_code: str):
    """获取股票统计"""
    stats = stock_db.get_stats(stock_code)
    return stats


@app.post("/api/trigger/{stock_code}")
async def trigger_crawl(stock_code: str, background_tasks: BackgroundTasks):
    """手动触发爬取（所有订阅该股票的用户都会收到推送）"""
    subs = [s for s in sub_db.get_all_active_subscriptions() if s['stock_code'] == stock_code]

    if not subs:
        raise HTTPException(status_code=404, detail="没有人订阅该股票")

    for sub in subs:
        background_tasks.add_task(crawl_and_notify_single, sub['id'])

    return {"message": f"已触发股票 {stock_code} 的爬取，将推送给 {len(subs)} 个订阅者"}


@app.get("/api/subscriptions")
async def get_all_subscriptions():
    """获取所有活跃订阅（管理接口）"""
    subs = sub_db.get_all_active_subscriptions()
    return {"count": len(subs), "subscriptions": subs}


# ============================================================================
# 后台任务
# ============================================================================

async def crawl_and_notify_single(sub_id: int):
    """爬取并推送单个订阅"""
    subs = sub_db.get_all_active_subscriptions()
    sub = next((s for s in subs if s['id'] == sub_id), None)

    if not sub:
        print(f"❌ 订阅 {sub_id} 不存在")
        return

    stock_code = sub['stock_code']
    print(f"🚀 开始爬取股票 {stock_code} (订阅ID: {sub_id})")

    try:
        # 爬取数据
        result = await crawl_eastmoney_stock(
            stock_code=stock_code,
            max_pages=2,
            enable_comments=True,
            max_comments_per_post=30
        )

        # 保存到数据库
        new_data = stock_db.save_data(result)

        # 获取统计
        stats = stock_db.get_stats(stock_code)

        # 生成报告
        report = generate_report(stock_code, new_data['new_posts'], new_data['new_comments'], stats)

        # 推送
        await send_webhook(
            webhook_url=sub['webhook_url'],
            webhook_type=sub['webhook_type'],
            content=report,
            title=f"股票 {stock_code} 监控报告"
        )

        # 更新爬取时间
        sub_db.update_crawl_time(sub_id)

        print(f"✅ 股票 {stock_code} 爬取完成: {len(new_data['new_posts'])}新帖, {len(new_data['new_comments'])}新评")

    except Exception as e:
        print(f"❌ 爬取失败: {e}")


async def monitor_loop():
    """监控循环：定时检查所有订阅并爬取"""
    print("⏰ 监控循环已启动")

    while True:
        try:
            subs = sub_db.get_all_active_subscriptions()
            now = datetime.now()

            for sub in subs:
                # 检查是否到了爬取时间
                last_crawl = sub['last_crawl_time']
                interval = sub['interval']

                should_crawl = False

                if not last_crawl:
                    # 从未爬取过
                    should_crawl = True
                else:
                    last_time = datetime.fromisoformat(last_crawl)
                    elapsed = (now - last_time).total_seconds()
                    if elapsed >= interval:
                        should_crawl = True

                if should_crawl:
                    print(f"⏰ 触发定时爬取: 股票{sub['stock_code']} (订阅ID: {sub['id']})")
                    await crawl_and_notify_single(sub['id'])

        except Exception as e:
            print(f"❌ 监控循环出错: {e}")

        # 每60秒检查一次
        await asyncio.sleep(60)


@app.on_event("startup")
async def startup_event():
    """启动时创建监控任务"""
    asyncio.create_task(monitor_loop())
    print("✅ 监控服务已启动")


# ============================================================================
# 启动服务
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("🚀 股票监控服务")
    print("=" * 80)
    print("服务地址: http://localhost:8000")
    print("API文档: http://localhost:8000/docs")
    print("")
    print("主要功能:")
    print("  - 用户订阅股票（提供Webhook URL）")
    print("  - 后台定时爬取数据")
    print("  - 自动推送到用户的Webhook")
    print("=" * 80)

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
