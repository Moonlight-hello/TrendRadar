#!/usr/bin/env python3
"""
简化版客户端测试 - 快速测试订阅000973股票
"""

import requests
import time
import json

def main():
    print("\n" + "="*80)
    print("🤖 智能股票监控系统 - 快速测试")
    print("="*80 + "\n")

    base_url = "http://localhost:8000"

    # 步骤1: 创建任务
    print("📝 步骤1: 创建监控任务...")
    create_resp = requests.post(
        f"{base_url}/api/v2/create_task",
        json={
            "user_id": "test_user",
            "description": "我想监控000973这只股票的舆论信息，关注情绪统计、看多看空比例和有价值的评论",
            "webhook_url": "http://localhost:9000/webhook/generic"
        }
    )

    if create_resp.status_code != 200:
        print(f"❌ 创建失败: {create_resp.text}")
        return

    result = create_resp.json()
    task_id = result['task_id']
    stock_code = result['intent']['entities'].get('stock_code', '000973')

    print(f"✅ 任务创建成功")
    print(f"   任务ID: {task_id}")
    print(f"   股票代码: {stock_code}\n")

    # 步骤2: 配置任务
    print("⚙️  步骤2: 配置任务...")
    config_resp = requests.post(
        f"{base_url}/api/v2/configure_task",
        json={
            "task_id": task_id,
            "stock_code": stock_code,
            "analysis_types": ["sentiment", "bull_bear", "quality_posts"],
            "platforms": ["eastmoney"],
            "interval_minutes": 10
        }
    )

    if config_resp.status_code != 200:
        print(f"❌ 配置失败: {config_resp.text}")
        return

    print("✅ 任务配置成功，系统正在进行首次数据采集...\n")

    # 步骤3: 等待执行并查看结果
    print("⏳ 步骤3: 等待数据采集和分析 (约30-60秒)...")
    print("   (爬虫Agent采集数据 → 分析Agent分析 → 生成报告 → Webhook推送)")

    # 获取当前消息数
    messages_resp = requests.get("http://localhost:9000/messages")
    initial_count = len(messages_resp.json()) if messages_resp.status_code == 200 else 0

    # 等待新消息
    max_wait = 90
    start_time = time.time()

    while time.time() - start_time < max_wait:
        time.sleep(3)
        try:
            messages_resp = requests.get("http://localhost:9000/messages")
            if messages_resp.status_code == 200:
                messages = messages_resp.json()
                if len(messages) > initial_count:
                    # 收到新消息
                    print("\n✅ 收到分析报告！\n")
                    print("="*80)
                    print("📊 股票 000973 舆论监控报告")
                    print("="*80)
                    latest = messages[-1]
                    print(latest.get('content', ''))
                    print("="*80)
                    print(f"\n推送时间: {latest.get('timestamp', 'N/A')}\n")

                    # 显示任务信息
                    task_resp = requests.get(f"{base_url}/api/v2/task/{task_id}")
                    if task_resp.status_code == 200:
                        task_info = task_resp.json()
                        print("📋 任务信息:")
                        print(f"   任务ID: {task_id}")
                        print(f"   状态: {task_info.get('status', 'N/A')}")
                        print(f"   下次执行: 约10分钟后")
                        print(f"   查询API: {base_url}/api/v2/task/{task_id}")

                    print("\n" + "="*80)
                    print("✅ 订阅成功！系统将每10分钟自动采集分析并推送报告")
                    print("="*80 + "\n")
                    return

        except Exception as e:
            print(f"检查消息时出错: {e}")

        # 显示进度
        elapsed = int(time.time() - start_time)
        print(f"\r   已等待 {elapsed}秒...", end='', flush=True)

    print(f"\n\n⏰ 等待超时 ({max_wait}秒)")
    print("   任务可能仍在后台执行，请稍后查看: http://localhost:9000/messages\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 测试中断")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
