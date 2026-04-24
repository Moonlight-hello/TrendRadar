# coding=utf-8
"""
TrendRadar FastAPI 服务入口

整合原有模块提供 RESTful API
"""

import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# 导入 TrendRadar 原有模块
from trendradar.context import AppContext
from trendradar.core import load_config
from trendradar.crawler import DataFetcher
from trendradar.ai import AIAnalyzer
from trendradar.notification import NotificationDispatcher

# 导入用户系统
from trendradar.user import UserManager
from trendradar.integrations.telegram import TrendRadarBot, PushService


# ============================================
# FastAPI 应用初始化
# ============================================

app = FastAPI(
    title="TrendRadar API",
    description="AI驱动的热点新闻聚合与分析系统",
    version="6.1.0"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================
# 全局配置
# ============================================

# 数据库路径
DB_PATH = os.getenv("TRENDRADAR_DB_PATH", "./data/trendradar.db")

# Telegram Bot Token
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# 全局实例
app_context: Optional[AppContext] = None
user_manager: Optional[UserManager] = None
telegram_bot: Optional[TrendRadarBot] = None


# ============================================
# Pydantic 模型
# ============================================

class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    version: str
    services: dict


class TrendingRequest(BaseModel):
    """热榜请求"""
    platform: str  # zhihu/weibo/bilibili
    limit: int = 50


# ============================================
# 应用生命周期
# ============================================

@app.on_event("startup")
async def startup_event():
    """应用启动"""
    global app_context, user_manager, telegram_bot

    print("=" * 60)
    print("TrendRadar Server 启动中...")
    print("=" * 60)

    # 1. 初始化应用上下文
    config = load_config()
    app_context = AppContext(config)
    print("✅ 应用上下文初始化完成")

    # 2. 初始化用户管理器
    user_manager = UserManager(DB_PATH)
    print(f"✅ 用户管理器初始化完成 (数据库: {DB_PATH})")

    # 3. 初始化 Telegram Bot（如果配置了）
    if TELEGRAM_BOT_TOKEN:
        try:
            telegram_bot = TrendRadarBot(
                token=TELEGRAM_BOT_TOKEN,
                db_path=DB_PATH
            )
            # telegram_bot.setup()
            print("✅ Telegram Bot 初始化完成")
        except Exception as e:
            print(f"⚠️  Telegram Bot 初始化失败: {e}")

    print("=" * 60)
    print("🚀 TrendRadar Server 启动完成！")
    print("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭"""
    print("\n停止 TrendRadar Server...")
    if telegram_bot:
        print("✅ Telegram Bot 已停止")
    print("👋 TrendRadar Server 已关闭")


# ============================================
# API 路由
# ============================================

@app.get("/", response_model=dict)
async def root():
    """根路径"""
    return {
        "name": "TrendRadar API",
        "version": "6.1.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查"""
    services = {
        "app_context": app_context is not None,
        "user_manager": user_manager is not None,
        "telegram_bot": telegram_bot is not None,
    }

    return HealthResponse(
        status="healthy" if all(services.values()) else "degraded",
        version="6.1.0",
        services=services
    )


@app.post("/api/trending")
async def get_trending(request: TrendingRequest):
    """
    获取热榜数据

    使用原有的 DataFetcher
    """
    if not app_context:
        raise HTTPException(status_code=503, detail="Service not ready")

    try:
        fetcher = DataFetcher()
        response, platform_id, alias = fetcher.fetch_data(request.platform)

        if not response:
            raise HTTPException(status_code=404, detail="Failed to fetch data")

        import json
        data = json.loads(response)

        return {
            "platform": request.platform,
            "count": len(data.get("data", [])),
            "items": data.get("data", [])[:request.limit]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/user/{user_id}")
async def get_user_info(user_id: str):
    """获取用户信息"""
    if not user_manager:
        raise HTTPException(status_code=503, detail="User service not ready")

    try:
        user_info = user_manager.get_user_info(user_id)
        return user_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# 运行服务器
# ============================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
