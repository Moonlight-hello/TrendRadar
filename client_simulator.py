#!/usr/bin/env python3
"""
客户端模拟器 - 测试智能股票监控系统
模拟用户订阅股票舆论信息的完整流程
"""

import requests
import json
import time
from typing import Dict, Any
from datetime import datetime

class MonitoringClient:
    """智能监控系统客户端"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.task_id = None

    def print_section(self, title: str):
        """打印分隔线"""
        print("\n" + "="*80)
        print(f"  {title}")
        print("="*80 + "\n")

    def create_task(self, description: str) -> Dict[str, Any]:
        """
        步骤1: 创建监控任务
        用户输入自然语言描述，AI理解意图并返回配置建议
        """
        self.print_section("📝 步骤1: 用户输入自然语言描述")
        print(f"用户描述: {description}\n")

        url = f"{self.base_url}/api/v2/create_task"
        payload = {
            "user_id": "test_user_001",  # 模拟用户ID
            "description": description,
            "webhook_url": "http://localhost:9000/webhook/generic"
        }

        print(f"🔄 发送请求到: {url}")
        response = self.session.post(url, json=payload)

        if response.status_code != 200:
            print(f"❌ 请求失败: {response.status_code}")
            print(response.text)
            return None

        result = response.json()
        self.task_id = result.get("task_id")

        print("✅ AI理解结果:")
        print(f"   任务ID: {self.task_id}")
        print(f"   股票代码: {result['intent']['entities'].get('stock_code', 'N/A')}")
        print(f"   检测到的意图: {result['intent'].get('intent', 'N/A')}")

        print("\n💡 AI建议的配置选项:")
        options = result.get('configuration_options', {})
        print(f"   股票: {options.get('stock_code', 'N/A')}")
        print(f"   分析维度: {', '.join(options.get('analysis_types', []))}")
        print(f"   监控平台: {', '.join(options.get('platforms', []))}")
        print(f"   更新频率: 每 {options.get('interval_minutes', 'N/A')} 分钟")

        return result

    def configure_task(self,
                      task_id: str,
                      stock_code: str,
                      analysis_types: list,
                      platforms: list,
                      interval_minutes: int = 10) -> bool:
        """
        步骤2: 确认配置
        用户确认或调整AI建议的配置
        """
        self.print_section("✅ 步骤2: 用户确认配置")

        config = {
            "task_id": task_id,
            "stock_code": stock_code,
            "analysis_types": analysis_types,
            "platforms": platforms,
            "interval_minutes": interval_minutes
        }

        print("用户确认的配置:")
        print(f"   股票代码: {stock_code}")
        print(f"   分析维度: {', '.join(analysis_types)}")
        print(f"   监控平台: {', '.join(platforms)}")
        print(f"   更新频率: 每 {interval_minutes} 分钟\n")

        url = f"{self.base_url}/api/v2/configure_task"
        response = self.session.post(url, json=config)

        if response.status_code != 200:
            print(f"❌ 配置失败: {response.status_code}")
            print(response.text)
            return False

        result = response.json()
        print(f"✅ {result.get('message', '任务配置成功')}")
        if 'next_execution' in result:
            print(f"   下次执行时间: {result['next_execution']}")

        return True

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """查询任务状态"""
        url = f"{self.base_url}/api/v2/task/{task_id}"
        response = self.session.get(url)

        if response.status_code != 200:
            print(f"❌ 查询失败: {response.status_code}")
            return None

        return response.json()

    def trigger_task(self, task_id: str) -> bool:
        """手动触发任务执行"""
        self.print_section("🚀 步骤3: 手动触发任务执行")

        url = f"{self.base_url}/api/v2/trigger/{task_id}"
        print(f"🔄 发送触发请求到: {url}\n")

        response = self.session.post(url)

        if response.status_code != 200:
            print(f"❌ 触发失败: {response.status_code}")
            print(response.text)
            return False

        result = response.json()
        print(f"✅ {result['message']}")
        return True

    def wait_for_execution(self, task_id: str, timeout: int = 120):
        """等待任务执行完成"""
        self.print_section("⏳ 步骤4: 等待任务执行")

        print(f"等待任务执行完成 (最长等待{timeout}秒)...\n")

        start_time = time.time()
        while time.time() - start_time < timeout:
            status = self.get_task_status(task_id)
            if not status:
                time.sleep(3)
                continue

            print(f"[{datetime.now().strftime('%H:%M:%S')}] 状态: {status.get('status', 'unknown')}")

            if status.get('status') == 'completed':
                print("\n✅ 任务执行完成!")

                # 显示执行结果
                if 'last_result' in status and status['last_result']:
                    self.print_section("📊 执行结果")
                    result = status['last_result']

                    # 数据概况
                    if 'data_summary' in result:
                        print("数据采集:")
                        for platform, stats in result['data_summary'].items():
                            print(f"  - {platform}: {stats['posts']}帖 + {stats['comments']}评")

                    # 分析结果
                    if 'analysis_results' in result:
                        print("\n智能分析:")
                        for analysis_type, data in result['analysis_results'].items():
                            if analysis_type == 'sentiment':
                                print(f"  - 情绪统计: 积极{data['positive_ratio']:.1%} / "
                                      f"消极{data['negative_ratio']:.1%} / "
                                      f"中性{data['neutral_ratio']:.1%}")
                            elif analysis_type == 'bull_bear':
                                print(f"  - 看多看空: 看多{data['bull_ratio']:.1%} / "
                                      f"看空{data['bear_ratio']:.1%} → {data['conclusion']}")
                            elif analysis_type == 'quality_posts':
                                print(f"  - 高质量帖子: {data['count']}条 ({data['percentage']:.2%})")

                    print(f"\n🕐 执行时间: {result.get('execution_time', 'N/A')}")
                    print(f"📬 推送状态: {result.get('push_status', 'N/A')}")

                return True

            time.sleep(3)

        print(f"\n⏰ 等待超时 ({timeout}秒)")
        return False

    def check_webhook_messages(self):
        """检查Webhook接收到的消息"""
        self.print_section("📬 步骤5: 查看Webhook推送的报告")

        try:
            url = "http://localhost:9000/messages"
            response = requests.get(url)

            if response.status_code != 200:
                print("❌ 无法获取Webhook消息")
                return

            messages = response.json()

            if not messages:
                print("暂无收到任何消息")
                return

            print(f"共收到 {len(messages)} 条推送消息\n")

            # 显示最新的消息
            if messages:
                latest = messages[-1]
                print("📄 最新报告:")
                print("-" * 80)
                print(latest.get('content', ''))
                print("-" * 80)
                print(f"\n推送时间: {latest.get('timestamp', 'N/A')}")

        except Exception as e:
            print(f"❌ 检查Webhook消息失败: {e}")


def main():
    """主测试流程"""
    print("\n" + "="*80)
    print("🤖 智能股票监控系统 - 客户端模拟器")
    print("="*80)

    client = MonitoringClient()

    # 用户自然语言描述
    user_description = "我想监控000973这只股票的舆论信息，关注情绪统计、看多看空比例和有价值的评论"

    # 步骤1: 创建任务
    result = client.create_task(user_description)
    if not result:
        print("❌ 创建任务失败")
        return

    task_id = result['task_id']
    options = result.get('configuration_options', {})

    # 步骤2: 确认配置
    success = client.configure_task(
        task_id=task_id,
        stock_code=options.get('stock_code', '000973'),
        analysis_types=options.get('analysis_types', ['sentiment', 'bull_bear', 'quality_posts']),
        platforms=options.get('platforms', ['eastmoney']),
        interval_minutes=10  # 10分钟执行一次
    )

    if not success:
        print("❌ 配置任务失败")
        return

    # 询问用户是否立即触发
    print("\n" + "="*80)
    print("✅ 任务配置完成！")
    print("="*80)
    print("\n选项:")
    print("  1. 立即触发执行并等待结果")
    print("  2. 等待定时任务自动执行（每10分钟）")
    print("  3. 退出")

    choice = input("\n请选择 (1/2/3): ").strip()

    if choice == "1":
        # 步骤3: 手动触发
        if client.trigger_task(task_id):
            # 步骤4: 等待执行完成
            client.wait_for_execution(task_id)

            # 步骤5: 查看Webhook推送
            time.sleep(2)  # 等待webhook推送
            client.check_webhook_messages()

    elif choice == "2":
        print(f"\n✅ 任务已启动，将每10分钟自动执行")
        print(f"   任务ID: {task_id}")
        print(f"   查询状态: GET {client.base_url}/api/v2/task/{task_id}")
        print(f"   查看推送: GET http://localhost:9000/messages")
        print(f"   API文档: {client.base_url}/docs")

    else:
        print("\n👋 已退出")

    print("\n" + "="*80)
    print("✅ 测试完成!")
    print("="*80 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 用户中断")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
