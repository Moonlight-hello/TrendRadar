#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试智能监控系统 - 完整流程演示
"""

import asyncio
import httpx


async def test_full_workflow():
    """测试完整工作流程"""
    print("\n" + "="*80)
    print("🤖 智能监控系统 - 完整流程测试")
    print("="*80 + "\n")

    base_url = "http://localhost:8000"
    client = httpx.AsyncClient()

    # ============================================================================
    # 步骤1: 用户输入自然语言描述
    # ============================================================================
    print("步骤1️⃣ : 用户输入自然语言")
    print("-" * 80)

    user_input = "我想监控000973这只股票的全部舆论情况，关注情绪统计、看多看空比例、以及有价值的评论"

    print(f"用户输入: {user_input}\n")

    # 创建任务
    response = await client.post(f"{base_url}/api/v2/create_task", json={
        "user_id": "user_demo_001",
        "description": user_input,
        "webhook_url": "http://localhost:9000/webhook/generic",
        "webhook_type": "generic"
    })

    result1 = response.json()
    task_id = result1['task_id']

    print(f"✅ 任务已创建: {task_id}\n")

    # ============================================================================
    # 步骤2: AI理解并生成配置选项
    # ============================================================================
    print("\n步骤2️⃣ : AI理解意图并生成配置选项")
    print("-" * 80)

    intent = result1['intent']
    print(f"AI识别到的意图: {intent['intent']}")
    print(f"提取的实体: {intent['entities']}")
    print(f"推荐的分析类型: {intent['suggested_analysis']}")
    print(f"推荐的平台: {intent['suggested_platforms']}\n")

    options = result1['configuration_options']

    print("📝 可选分析维度:")
    for i, opt in enumerate(options['analysis_options'], 1):
        tag = " ⭐(推荐)" if opt['recommended'] else ""
        print(f"  {i}. {opt['name']}{tag}")
        print(f"     {opt['description']}")

    print("\n🌐 可选平台:")
    for i, opt in enumerate(options['platform_options'], 1):
        status = "✅可用" if opt['available'] else "❌未实现"
        tag = " ⭐(推荐)" if opt['recommended'] else ""
        print(f"  {i}. {opt['name']} [{status}]{tag}")
        print(f"     {opt['description']}")

    # ============================================================================
    # 步骤3: 用户选择配置
    # ============================================================================
    print("\n步骤3️⃣ : 用户确认配置")
    print("-" * 80)

    # 用户选择
    selected_analysis = ["sentiment", "bull_bear", "quality_posts"]
    selected_platforms = ["eastmoney"]

    print(f"选择的分析维度: {selected_analysis}")
    print(f"选择的平台: {selected_platforms}")
    print(f"监控间隔: 300秒 (5分钟)\n")

    # 提交配置
    stock_code = intent['entities'].get('stock_code', options['stock_code'])
    if not stock_code:
        stock_code = "000973"  # 默认值

    response = await client.post(f"{base_url}/api/v2/configure_task", json={
        "task_id": task_id,
        "stock_code": stock_code,
        "analysis_types": selected_analysis,
        "platforms": selected_platforms,
        "interval": 300
    })

    result2 = response.json()
    print(f"✅ {result2['message']}\n")

    # ============================================================================
    # 步骤4-7: 等待后台执行（爬取、分析、生成报告、推送）
    # ============================================================================
    print("\n步骤4️⃣ -7️⃣ : 后台执行中...")
    print("-" * 80)
    print("🕷️  爬虫Agent正在采集数据...")
    print("🔍 分析Agent正在分析数据...")
    print("📄 正在生成报告...")
    print("📬 正在推送到Webhook...\n")

    print("⏳ 等待30秒...")
    await asyncio.sleep(30)

    # ============================================================================
    # 查看任务状态
    # ============================================================================
    print("\n查看任务状态")
    print("-" * 80)

    response = await client.get(f"{base_url}/api/v2/task/{task_id}")
    task_info = response.json()

    print(f"任务ID: {task_info['task_id']}")
    print(f"状态: {task_info['status']}")
    print(f"股票代码: {task_info['stock_code']}")
    print(f"上次报告: {task_info['last_report_time']}")

    # ============================================================================
    # 查看Webhook收到的报告
    # ============================================================================
    print("\n查看推送的报告")
    print("-" * 80)

    webhook_receiver_url = "http://localhost:9000/messages"
    try:
        response = await client.get(webhook_receiver_url)
        messages = response.json()

        if messages['count'] > 0:
            latest = messages['messages'][0]
            print(f"✅ 收到 {messages['count']} 条推送")
            print(f"\n最新报告预览:")
            print("-" * 80)
            content = latest['data']['content']
            # 只显示前500字符
            print(content[:500] + "...\n")
        else:
            print("⚠️  暂未收到推送（可能还在执行中）")
    except Exception as e:
        print(f"❌ 无法连接到Webhook接收器: {e}")
        print("提示: 请先运行 `python3 test_client.py server` 启动接收器")

    print("\n" + "="*80)
    print("✅ 测试完成！")
    print("="*80 + "\n")

    await client.aclose()


if __name__ == "__main__":
    asyncio.run(test_full_workflow())
