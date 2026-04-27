#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试客户端 - 模拟用户订阅和接收Webhook
"""

import asyncio
import json
from datetime import datetime
from typing import Optional

import httpx
from fastapi import FastAPI, Request
import uvicorn


# ============================================================================
# 模拟Webhook接收服务器
# ============================================================================

app = FastAPI(title="模拟Webhook接收器")

# 存储接收到的消息
received_messages = []


@app.post("/webhook/feishu")
async def receive_feishu_webhook(request: Request):
    """模拟飞书Webhook接收"""
    data = await request.json()

    message = {
        "time": datetime.now().isoformat(),
        "type": "feishu",
        "data": data
    }
    received_messages.append(message)

    print("\n" + "="*80)
    print("📬 收到飞书Webhook推送")
    print("="*80)

    # 解析飞书卡片
    if "card" in data:
        card = data["card"]
        if "header" in card:
            print(f"标题: {card['header']['title']['content']}")
        if "elements" in card:
            for element in card["elements"]:
                if element.get("tag") == "markdown":
                    print(f"\n内容:\n{element['content']}")

    print("="*80 + "\n")

    return {"success": True}


@app.post("/webhook/generic")
async def receive_generic_webhook(request: Request):
    """模拟通用Webhook接收"""
    data = await request.json()

    message = {
        "time": datetime.now().isoformat(),
        "type": "generic",
        "data": data
    }
    received_messages.append(message)

    print("\n" + "="*80)
    print("📬 收到通用Webhook推送")
    print("="*80)
    print(f"标题: {data.get('title', 'N/A')}")
    print(f"\n内容:\n{data.get('content', 'N/A')}")
    print("="*80 + "\n")

    return {"success": True}


@app.get("/messages")
async def get_messages():
    """查看收到的所有消息"""
    return {
        "count": len(received_messages),
        "messages": received_messages
    }


@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "Webhook接收器",
        "endpoints": {
            "飞书": "/webhook/feishu",
            "通用": "/webhook/generic",
            "查看消息": "/messages"
        },
        "received_count": len(received_messages)
    }


# ============================================================================
# 测试脚本
# ============================================================================

class StockMonitorClient:
    """股票监控客户端"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient()

    async def subscribe(self, stock_code: str, webhook_url: str,
                       webhook_type: str = "generic", user_id: Optional[str] = None,
                       interval: int = 300):
        """订阅股票"""
        data = {
            "stock_code": stock_code,
            "webhook_url": webhook_url,
            "webhook_type": webhook_type,
            "user_id": user_id,
            "interval": interval
        }

        response = await self.client.post(f"{self.base_url}/api/subscribe", json=data)
        return response.json()

    async def unsubscribe(self, stock_code: str, user_id: Optional[str] = None):
        """取消订阅"""
        data = {
            "stock_code": stock_code,
            "user_id": user_id
        }

        response = await self.client.post(f"{self.base_url}/api/unsubscribe", json=data)
        return response.json()

    async def get_subscriptions(self, user_id: str):
        """获取用户订阅"""
        response = await self.client.get(f"{self.base_url}/api/subscriptions/{user_id}")
        return response.json()

    async def trigger_crawl(self, stock_code: str):
        """手动触发爬取"""
        response = await self.client.post(f"{self.base_url}/api/trigger/{stock_code}")
        return response.json()

    async def get_stats(self, stock_code: str):
        """获取统计"""
        response = await self.client.get(f"{self.base_url}/api/stocks/{stock_code}/stats")
        return response.json()

    async def close(self):
        """关闭客户端"""
        await self.client.aclose()


# ============================================================================
# 测试场景
# ============================================================================

async def test_scenario_1():
    """场景1: 基本订阅流程"""
    print("\n" + "="*80)
    print("测试场景1: 基本订阅流程")
    print("="*80 + "\n")

    client = StockMonitorClient()

    # 1. 订阅股票
    print("1️⃣ 订阅股票 000973...")
    result = await client.subscribe(
        stock_code="000973",
        webhook_url="http://localhost:9000/webhook/generic",
        webhook_type="generic",
        user_id="test_user_001",
        interval=120  # 2分钟
    )
    print(f"✅ {result['message']}")
    print(f"订阅ID: {result['subscription_id']}\n")

    # 2. 查看订阅
    print("2️⃣ 查看我的订阅...")
    subs = await client.get_subscriptions("test_user_001")
    print(f"✅ 共有 {subs['count']} 个订阅\n")

    # 3. 手动触发爬取
    print("3️⃣ 手动触发爬取...")
    result = await client.trigger_crawl("000973")
    print(f"✅ {result['message']}\n")

    print("等待30秒，查看是否收到Webhook推送...")
    await asyncio.sleep(30)

    # 4. 取消订阅
    print("\n4️⃣ 取消订阅...")
    result = await client.unsubscribe("000973", "test_user_001")
    print(f"✅ {result['message']}\n")

    await client.close()


async def test_scenario_2_feishu():
    """场景2: 飞书Webhook模拟"""
    print("\n" + "="*80)
    print("测试场景2: 飞书Webhook模拟")
    print("="*80 + "\n")

    client = StockMonitorClient()

    # 订阅使用飞书格式
    print("1️⃣ 订阅股票（飞书格式）...")
    result = await client.subscribe(
        stock_code="000973",
        webhook_url="http://localhost:9000/webhook/feishu",
        webhook_type="feishu",
        user_id="feishu_user_001"
    )
    print(f"✅ {result['message']}\n")

    # 触发爬取
    print("2️⃣ 触发爬取...")
    await client.trigger_crawl("000973")
    print("✅ 已触发，等待接收...\n")

    await asyncio.sleep(30)

    await client.close()


async def test_scenario_3_stats():
    """场景3: 查询统计信息"""
    print("\n" + "="*80)
    print("测试场景3: 查询统计信息")
    print("="*80 + "\n")

    client = StockMonitorClient()

    stats = await client.get_stats("000973")

    print(f"股票代码: {stats['stock_code']}")
    print(f"帖子总数: {stats['post_count']}")
    print(f"评论总数: {stats['comment_count']}")
    print(f"最新时间: {stats['latest_post_time']}\n")

    await client.close()


def main():
    """主函数"""
    import sys

    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python3 test_client.py server    # 启动Webhook接收服务器")
        print("  python3 test_client.py test1     # 测试基本订阅流程")
        print("  python3 test_client.py test2     # 测试飞书Webhook")
        print("  python3 test_client.py test3     # 测试查询统计")
        return

    command = sys.argv[1]

    if command == "server":
        # 启动Webhook接收服务器
        print("="*80)
        print("🚀 启动Webhook接收服务器")
        print("="*80)
        print("服务地址: http://localhost:9000")
        print("飞书Webhook: http://localhost:9000/webhook/feishu")
        print("通用Webhook: http://localhost:9000/webhook/generic")
        print("="*80 + "\n")

        uvicorn.run(app, host="0.0.0.0", port=9000, log_level="info")

    elif command == "test1":
        asyncio.run(test_scenario_1())

    elif command == "test2":
        asyncio.run(test_scenario_2_feishu())

    elif command == "test3":
        asyncio.run(test_scenario_3_stats())

    else:
        print(f"未知命令: {command}")


if __name__ == "__main__":
    main()
