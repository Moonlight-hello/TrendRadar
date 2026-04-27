#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票监控 API 服务
提供 REST API 和 WebSocket 实时推送
"""

import asyncio
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# 添加项目路径
import sys
sys.path.insert(0, str(Path(__file__).parent))

from trendradar.crawler.eastmoney import crawl_eastmoney_stock


# ============================================================================
# 数据模型
# ============================================================================

class StockPost(BaseModel):
    """帖子模型"""
    post_id: str
    title: str
    user_nickname: str
    publish_time: str
    comment_count: int
    click_count: int


class StockComment(BaseModel):
    """评论模型"""
    comment_id: str
    post_id: str
    content: str
    user_nickname: str
    publish_time: str
    like_count: int


class StockStats(BaseModel):
    """股票统计"""
    stock_code: str
    post_count: int
    comment_count: int
    latest_post_time: Optional[str]


class MonitorRequest(BaseModel):
    """监控请求"""
    stock_code: str
    max_pages: int = 3
    max_comments_per_post: int = 50


# ============================================================================
# WebSocket 连接管理
# ============================================================================

class ConnectionManager:
    """WebSocket 连接管理器"""

    def __init__(self):
        # 按股票代码分组的连接
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, stock_code: str):
        """接受连接"""
        await websocket.accept()
        if stock_code not in self.active_connections:
            self.active_connections[stock_code] = []
        self.active_connections[stock_code].append(websocket)
        print(f"✅ 新连接: {stock_code}, 当前连接数: {len(self.active_connections[stock_code])}")

    def disconnect(self, websocket: WebSocket, stock_code: str):
        """断开连接"""
        if stock_code in self.active_connections:
            self.active_connections[stock_code].remove(websocket)
            print(f"❌ 断开连接: {stock_code}, 剩余连接数: {len(self.active_connections[stock_code])}")

    async def broadcast(self, stock_code: str, message: dict):
        """向指定股票的所有订阅者广播消息"""
        if stock_code not in self.active_connections:
            return

        disconnected = []
        for connection in self.active_connections[stock_code]:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"发送失败: {e}")
                disconnected.append(connection)

        # 清理断开的连接
        for conn in disconnected:
            self.active_connections[stock_code].remove(conn)


# ============================================================================
# 数据库操作
# ============================================================================

class StockDatabase:
    """数据库操作类"""

    def __init__(self, db_path: str = "eastmoney_stocks.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 创建表
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

        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_posts_stock_code ON posts(stock_code)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_posts_publish_time ON posts(publish_time)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_comments_post_id ON comments(post_id)")

        conn.commit()
        conn.close()

    def get_stock_stats(self, stock_code: str) -> Optional[StockStats]:
        """获取股票统计"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*) as post_count, MAX(publish_time) as latest
            FROM posts WHERE stock_code=?
        """, (stock_code,))
        row = cursor.fetchone()

        if not row or row['post_count'] == 0:
            conn.close()
            return None

        cursor.execute("""
            SELECT COUNT(*) FROM comments
            WHERE post_id IN (SELECT post_id FROM posts WHERE stock_code=?)
        """, (stock_code,))
        comment_count = cursor.fetchone()[0]

        conn.close()

        return StockStats(
            stock_code=stock_code,
            post_count=row['post_count'],
            comment_count=comment_count,
            latest_post_time=row['latest']
        )

    def get_posts(self, stock_code: str, limit: int = 20, offset: int = 0) -> List[StockPost]:
        """获取帖子列表"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT post_id, title, user_nickname, publish_time, comment_count, click_count
            FROM posts
            WHERE stock_code=?
            ORDER BY publish_time DESC
            LIMIT ? OFFSET ?
        """, (stock_code, limit, offset))

        posts = [StockPost(**dict(row)) for row in cursor.fetchall()]
        conn.close()
        return posts

    def get_comments(self, post_id: str, limit: int = 50) -> List[StockComment]:
        """获取评论列表"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT comment_id, post_id, content, user_nickname, publish_time, like_count
            FROM comments
            WHERE post_id=?
            ORDER BY publish_time DESC
            LIMIT ?
        """, (post_id, limit))

        comments = [StockComment(**dict(row)) for row in cursor.fetchall()]
        conn.close()
        return comments

    def save_data(self, data: Dict) -> Dict:
        """保存数据到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        stock_code = data['stock_code']
        posts = data['posts']
        comments = data['comments']

        new_posts = []
        new_comments = []

        # 保存帖子
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

        # 保存评论
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


# ============================================================================
# FastAPI 应用
# ============================================================================

app = FastAPI(title="股票监控API", version="1.0.0")

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局对象
manager = ConnectionManager()
db = StockDatabase()

# 后台监控任务
monitoring_tasks = {}


# ============================================================================
# REST API 路由
# ============================================================================

@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "股票监控API",
        "version": "1.0.0",
        "endpoints": {
            "websocket": "/ws/{stock_code}",
            "stats": "/api/stocks/{stock_code}/stats",
            "posts": "/api/stocks/{stock_code}/posts",
            "comments": "/api/posts/{post_id}/comments",
            "monitor": "/api/monitor"
        }
    }


@app.get("/api/stocks/{stock_code}/stats")
async def get_stock_stats(stock_code: str):
    """获取股票统计信息"""
    stats = db.get_stock_stats(stock_code)
    if not stats:
        raise HTTPException(status_code=404, detail="股票数据不存在")
    return stats


@app.get("/api/stocks/{stock_code}/posts")
async def get_posts(stock_code: str, limit: int = 20, offset: int = 0):
    """获取帖子列表"""
    posts = db.get_posts(stock_code, limit, offset)
    return {"stock_code": stock_code, "count": len(posts), "posts": posts}


@app.get("/api/posts/{post_id}/comments")
async def get_comments(post_id: str, limit: int = 50):
    """获取评论列表"""
    comments = db.get_comments(post_id, limit)
    return {"post_id": post_id, "count": len(comments), "comments": comments}


@app.post("/api/monitor")
async def start_monitor(request: MonitorRequest, background_tasks: BackgroundTasks):
    """开始监控股票（手动触发）"""
    background_tasks.add_task(crawl_and_notify, request.stock_code, request.max_pages, request.max_comments_per_post)
    return {"message": f"已开始爬取股票 {request.stock_code}"}


# ============================================================================
# WebSocket 路由
# ============================================================================

@app.websocket("/ws/{stock_code}")
async def websocket_endpoint(websocket: WebSocket, stock_code: str):
    """
    WebSocket 实时推送
    客户端连接后会收到新增的帖子和评论
    """
    await manager.connect(websocket, stock_code)

    try:
        # 发送欢迎消息
        await websocket.send_json({
            "type": "connected",
            "stock_code": stock_code,
            "message": f"已连接到股票 {stock_code} 的实时推送"
        })

        # 发送当前统计
        stats = db.get_stock_stats(stock_code)
        if stats:
            await websocket.send_json({
                "type": "stats",
                "data": stats.dict()
            })

        # 保持连接
        while True:
            # 接收心跳消息
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        manager.disconnect(websocket, stock_code)


# ============================================================================
# 后台任务
# ============================================================================

async def crawl_and_notify(stock_code: str, max_pages: int = 3, max_comments_per_post: int = 50):
    """爬取数据并通过WebSocket推送"""
    print(f"🚀 开始爬取股票 {stock_code}")

    try:
        # 爬取数据
        result = await crawl_eastmoney_stock(
            stock_code=stock_code,
            max_pages=max_pages,
            enable_comments=True,
            max_comments_per_post=max_comments_per_post
        )

        # 保存到数据库并获取新数据
        new_data = db.save_data(result)

        # 通过WebSocket推送新数据
        if new_data['new_posts']:
            await manager.broadcast(stock_code, {
                "type": "new_posts",
                "stock_code": stock_code,
                "count": len(new_data['new_posts']),
                "data": new_data['new_posts'][:5]  # 只推送前5条
            })

        if new_data['new_comments']:
            await manager.broadcast(stock_code, {
                "type": "new_comments",
                "stock_code": stock_code,
                "count": len(new_data['new_comments']),
                "data": new_data['new_comments'][:10]  # 只推送前10条
            })

        # 推送统计更新
        stats = db.get_stock_stats(stock_code)
        if stats:
            await manager.broadcast(stock_code, {
                "type": "stats_update",
                "data": stats.dict()
            })

        print(f"✅ 股票 {stock_code} 爬取完成: {len(new_data['new_posts'])}新帖, {len(new_data['new_comments'])}新评")

    except Exception as e:
        print(f"❌ 爬取失败: {e}")
        await manager.broadcast(stock_code, {
            "type": "error",
            "message": str(e)
        })


async def auto_monitor_loop(stock_code: str, interval: int = 300):
    """自动监控循环（每隔interval秒爬取一次）"""
    print(f"⏰ 启动自动监控: {stock_code}, 间隔 {interval}秒")

    while True:
        try:
            await crawl_and_notify(stock_code, max_pages=2, max_comments_per_post=30)
        except Exception as e:
            print(f"❌ 自动监控出错: {e}")

        await asyncio.sleep(interval)


@app.post("/api/monitor/auto/{stock_code}")
async def start_auto_monitor(stock_code: str, interval: int = 300):
    """启动自动监控（每隔interval秒爬取一次）"""
    if stock_code in monitoring_tasks:
        return {"message": f"股票 {stock_code} 已在监控中"}

    # 创建后台任务
    task = asyncio.create_task(auto_monitor_loop(stock_code, interval))
    monitoring_tasks[stock_code] = task

    return {
        "message": f"已启动股票 {stock_code} 的自动监控",
        "interval": interval
    }


@app.delete("/api/monitor/auto/{stock_code}")
async def stop_auto_monitor(stock_code: str):
    """停止自动监控"""
    if stock_code not in monitoring_tasks:
        raise HTTPException(status_code=404, detail="该股票未在监控中")

    task = monitoring_tasks[stock_code]
    task.cancel()
    del monitoring_tasks[stock_code]

    return {"message": f"已停止股票 {stock_code} 的监控"}


# ============================================================================
# 启动服务
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("🚀 股票监控API服务")
    print("=" * 80)
    print("REST API: http://localhost:8000")
    print("WebSocket: ws://localhost:8000/ws/{stock_code}")
    print("API文档: http://localhost:8000/docs")
    print("=" * 80)

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
