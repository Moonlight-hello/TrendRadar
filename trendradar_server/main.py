# -*- coding: utf-8 -*-
"""
TrendRadar FastAPI 服务主入口

整合所有模块：
- UserManager: 用户管理
- CrawlerAgent: 数据爬取
- AnalyzerAgent: AI分析
- TelegramBot: 用户交互
- PushService: 消息推送
- Scheduler: 定时任务调度
"""

import os
import sys
import threading
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# 添加项目路径
sys.path.append(str(Path(__file__).parent))

# 导入核心模块
from core.user_manager import UserManager
from core.crawler_agent import CrawlerAgent
from core.analyzer_agent import AnalyzerAgent
from core.scheduler import TrendRadarScheduler
from user import MinimalUserManager, TrendRadarBot, PushService


# ============================================
# FastAPI应用初始化
# ============================================

app = FastAPI(
    title="TrendRadar API",
    description="AI驱动的股票讨论智能追踪系统",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================
# 全局变量和配置
# ============================================

# 数据库路径
DB_PATH = os.getenv("TRENDRADAR_DB_PATH", "/tmp/trendradar.db")

# API配置
API_BASE = os.getenv("NEW_API_BASE", "http://45.197.145.24:3000/v1")
API_KEY = os.getenv("NEW_API_KEY", "sk-QlwwecImBL1Yx0p2ji8Awsr0ROuD6HPeimWQIRBtgqYSPnXj")

# Telegram Bot配置
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Mock模式（开发环境使用）
MOCK_MODE = os.getenv("MOCK_MODE", "true").lower() == "true"

# 全局实例
user_mgr: Optional[UserManager] = None
crawler: Optional[CrawlerAgent] = None
analyzer: Optional[AnalyzerAgent] = None
scheduler: Optional[TrendRadarScheduler] = None
telegram_bot: Optional[TrendRadarBot] = None
push_service: Optional[PushService] = None


# ============================================
# Pydantic模型
# ============================================

class AnalyzeRequest(BaseModel):
    """分析请求"""
    symbol: str  # 股票代码
    source: str = "eastmoney"  # 数据源
    max_posts: int = 50  # 最大帖子数
    analysis_type: str = "comprehensive"  # 分析类型


class SubscriptionRequest(BaseModel):
    """订阅请求"""
    user_id: str
    target: str
    target_display_name: Optional[str] = None
    subscription_type: str = "stock"
    platforms: List[str] = ["eastmoney"]
    push_channels: List[str] = ["telegram"]
    push_frequency: str = "realtime"


class TaskResponse(BaseModel):
    """任务响应"""
    task_id: str
    status: str
    message: Optional[str] = None


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    timestamp: str
    services: dict


# ============================================
# 应用生命周期事件
# ============================================

@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    global user_mgr, crawler, analyzer, scheduler, telegram_bot, push_service

    print("=" * 60)
    print("TrendRadar Server 启动中...")
    print("=" * 60)

    # 1. 初始化用户管理器
    print(f"📂 数据库路径: {DB_PATH}")
    user_mgr = UserManager(DB_PATH)
    print("✅ 用户管理器初始化完成")

    # 2. 初始化爬虫Agent
    crawler = CrawlerAgent(user_mgr)
    print("✅ 爬虫Agent初始化完成")

    # 3. 初始化分析Agent
    analyzer = AnalyzerAgent(
        user_manager=user_mgr,
        api_base=API_BASE,
        api_key=API_KEY,
        mock_mode=MOCK_MODE
    )
    print(f"✅ 分析Agent初始化完成 (Mock模式: {MOCK_MODE})")

    # 4. 初始化Telegram Bot（如果配置了Token）
    if TELEGRAM_BOT_TOKEN:
        try:
            telegram_bot = TrendRadarBot(
                token=TELEGRAM_BOT_TOKEN,
                db_path=DB_PATH
            )
            telegram_bot.setup()

            # 在后台线程运行Bot
            bot_thread = threading.Thread(
                target=telegram_bot.run,
                daemon=True
            )
            bot_thread.start()
            print("✅ Telegram Bot启动成功")

            # 初始化推送服务
            minimal_user_mgr = MinimalUserManager(DB_PATH)
            push_service = PushService(minimal_user_mgr, telegram_bot)
            print("✅ 推送服务初始化完成")

        except Exception as e:
            print(f"⚠️  Telegram Bot启动失败: {e}")
    else:
        print("⚠️  未配置TELEGRAM_BOT_TOKEN，跳过Bot启动")

    # 5. 初始化调度器
    scheduler = TrendRadarScheduler(
        user_manager=user_mgr,
        crawler_agent=crawler,
        analyzer_agent=analyzer,
        push_service=push_service,
        crawl_interval_minutes=30
    )
    scheduler.start()
    print("✅ 定时任务调度器启动完成")

    print("=" * 60)
    print("🚀 TrendRadar Server 启动完成！")
    print("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时执行"""
    print("\n停止TrendRadar Server...")

    # 停止调度器
    if scheduler:
        scheduler.stop()
        print("✅ 调度器已停止")

    # 停止Telegram Bot
    if telegram_bot:
        print("✅ Telegram Bot已停止")

    print("👋 TrendRadar Server 已关闭")


# ============================================
# API路由
# ============================================

@app.get("/", response_model=dict)
async def root():
    """根路径"""
    return {
        "name": "TrendRadar API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查"""
    services = {
        "database": user_mgr is not None,
        "crawler": crawler is not None,
        "analyzer": analyzer is not None,
        "scheduler": scheduler is not None and scheduler.is_running,
        "telegram_bot": telegram_bot is not None,
        "push_service": push_service is not None
    }

    return HealthResponse(
        status="healthy" if all(services.values()) else "degraded",
        timestamp=datetime.now().isoformat(),
        services=services
    )


@app.post("/api/analyze", response_model=dict)
async def analyze_stock(
    request: AnalyzeRequest,
    background_tasks: BackgroundTasks
):
    """
    提交股票分析任务

    Args:
        request: 分析请求

    Returns:
        任务ID和状态
    """
    # 生成任务ID
    task_id = f"task_{datetime.now().strftime('%Y%m%d%H%M%S')}"

    # 这里简化实现：直接同步执行
    # 生产环境应该使用Celery等任务队列

    try:
        # 创建临时用户（或使用实际用户ID）
        user_id = "api_user"

        # 爬取数据
        success, msg, data = crawler.crawl(
            user_id=user_id,
            platform=request.source,
            target=request.symbol,
            max_items=request.max_posts
        )

        if not success:
            raise HTTPException(status_code=400, detail=msg)

        # AI分析
        success, msg, analysis = analyzer.analyze(
            user_id=user_id,
            data=data,
            analysis_type=request.analysis_type
        )

        if not success:
            raise HTTPException(status_code=400, detail=msg)

        return {
            "task_id": task_id,
            "status": "completed",
            "result": analysis
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tasks/{task_id}", response_model=dict)
async def get_task_status(task_id: str):
    """
    查询任务状态

    Args:
        task_id: 任务ID

    Returns:
        任务状态和结果
    """
    # 简化实现：返回示例响应
    # 生产环境应该从数据库或缓存查询
    return {
        "task_id": task_id,
        "status": "completed",
        "progress": 100,
        "message": "任务已完成"
    }


@app.post("/api/subscriptions", response_model=dict)
async def create_subscription(request: SubscriptionRequest):
    """
    创建订阅

    Args:
        request: 订阅请求

    Returns:
        订阅ID和状态
    """
    try:
        # 检查用户是否存在
        if not user_mgr.user_exists(request.user_id):
            # 自动注册
            user_mgr.register_user(request.user_id)

        # 创建订阅
        success, msg, sub_id = user_mgr.create_subscription(
            user_id=request.user_id,
            subscription_type=request.subscription_type,
            target=request.target,
            target_display_name=request.target_display_name or request.target,
            platforms=request.platforms,
            push_channels=request.push_channels,
            push_frequency=request.push_frequency
        )

        if not success:
            raise HTTPException(status_code=400, detail=msg)

        return {
            "success": True,
            "subscription_id": sub_id,
            "message": msg
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/subscriptions/{user_id}", response_model=dict)
async def get_subscriptions(user_id: str):
    """
    获取用户订阅列表

    Args:
        user_id: 用户ID

    Returns:
        订阅列表
    """
    try:
        subscriptions = user_mgr.get_user_subscriptions(user_id)
        return {
            "user_id": user_id,
            "subscriptions": subscriptions
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats", response_model=dict)
async def get_system_stats():
    """
    获取系统统计信息

    Returns:
        系统统计
    """
    stats = {}

    if scheduler:
        stats['scheduler'] = scheduler.get_stats()

    return stats


@app.post("/api/trigger-crawl", response_model=dict)
async def trigger_crawl():
    """
    手动触发爬取任务（用于测试）

    Returns:
        触发结果
    """
    if not scheduler:
        raise HTTPException(status_code=503, detail="调度器未运行")

    try:
        # 在后台触发任务
        threading.Thread(
            target=scheduler.trigger_crawl_now,
            daemon=True
        ).start()

        return {
            "success": True,
            "message": "爬取任务已触发"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# 运行服务器
# ============================================

if __name__ == "__main__":
    import uvicorn

    # 运行服务器
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
