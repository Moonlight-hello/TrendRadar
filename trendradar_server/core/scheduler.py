# -*- coding: utf-8 -*-
"""
定时任务调度器
使用APScheduler管理定时任务：爬取、分析、推送
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

# 导入核心模块
try:
    from .crawler_agent import CrawlerAgent
    from .analyzer_agent import AnalyzerAgent
    from .user_manager import UserManager
except ImportError:
    from crawler_agent import CrawlerAgent
    from analyzer_agent import AnalyzerAgent
    from user_manager import UserManager


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TrendRadarScheduler:
    """
    TrendRadar定时任务调度器

    功能：
    1. 定时爬取订阅数据
    2. 自动AI分析
    3. 推送通知给用户
    4. 会员过期检查
    5. Token余额警告
    """

    def __init__(
        self,
        user_manager: UserManager,
        crawler_agent: CrawlerAgent,
        analyzer_agent: AnalyzerAgent,
        push_service=None,  # PushService实例（可选）
        crawl_interval_minutes: int = 30
    ):
        """
        初始化调度器

        Args:
            user_manager: 用户管理器
            crawler_agent: 爬虫Agent
            analyzer_agent: 分析Agent
            push_service: 推送服务（可选）
            crawl_interval_minutes: 爬取间隔（分钟）
        """
        self.user_mgr = user_manager
        self.crawler = crawler_agent
        self.analyzer = analyzer_agent
        self.push_service = push_service
        self.crawl_interval = crawl_interval_minutes

        # 创建调度器
        self.scheduler = BackgroundScheduler()
        self.is_running = False

        # 统计信息
        self.stats = {
            'total_runs': 0,
            'success_runs': 0,
            'failed_runs': 0,
            'last_run': None,
            'last_error': None
        }

    def start(self):
        """启动调度器"""
        if self.is_running:
            logger.warning("调度器已经在运行中")
            return

        # 添加任务
        self._add_jobs()

        # 启动调度器
        self.scheduler.start()
        self.is_running = True

        logger.info("=" * 60)
        logger.info("TrendRadar 调度器已启动")
        logger.info(f"爬取间隔: 每{self.crawl_interval}分钟")
        logger.info("=" * 60)

    def stop(self):
        """停止调度器"""
        if not self.is_running:
            logger.warning("调度器未运行")
            return

        self.scheduler.shutdown(wait=False)
        self.is_running = False
        logger.info("调度器已停止")

    def _add_jobs(self):
        """添加定时任务"""

        # 1. 主任务：爬取+分析+推送
        self.scheduler.add_job(
            func=self._crawl_analyze_push_job,
            trigger=IntervalTrigger(minutes=self.crawl_interval),
            id='crawl_analyze_push',
            name='爬取分析推送任务',
            replace_existing=True,
            max_instances=1  # 防止任务堆积
        )

        # 2. 每日任务：会员过期检查（每天凌晨2点）
        self.scheduler.add_job(
            func=self._check_membership_expiry,
            trigger=CronTrigger(hour=2, minute=0),
            id='check_membership',
            name='会员过期检查',
            replace_existing=True
        )

        # 3. 每小时任务：Token余额预警
        self.scheduler.add_job(
            func=self._check_token_balance,
            trigger=CronTrigger(minute=0),
            id='check_token_balance',
            name='Token余额检查',
            replace_existing=True
        )

        logger.info("定时任务已添加:")
        logger.info(f"  - 爬取分析推送: 每{self.crawl_interval}分钟")
        logger.info("  - 会员检查: 每天凌晨2点")
        logger.info("  - 余额检查: 每小时")

    # ============================================
    # 主任务：爬取 + 分析 + 推送
    # ============================================

    def _crawl_analyze_push_job(self):
        """
        主任务：爬取数据 → AI分析 → 推送给用户
        """
        try:
            logger.info("=" * 60)
            logger.info(f"开始执行爬取分析任务 [{datetime.now()}]")

            # 1. 获取所有活跃订阅
            subscriptions = self.user_mgr.get_all_active_subscriptions()

            if not subscriptions:
                logger.info("没有活跃订阅，跳过任务")
                return

            logger.info(f"找到 {len(subscriptions)} 个活跃订阅")

            # 2. 按用户分组订阅
            user_subscriptions = {}
            for sub in subscriptions:
                user_id = sub['user_id']
                if user_id not in user_subscriptions:
                    user_subscriptions[user_id] = []
                user_subscriptions[user_id].append(sub)

            # 3. 处理每个用户的订阅
            success_count = 0
            failed_count = 0

            for user_id, subs in user_subscriptions.items():
                logger.info(f"\n处理用户 {user_id} 的 {len(subs)} 个订阅...")

                # 检查用户状态
                user_info = self.user_mgr.get_user_info(user_id)
                if user_info['membership']['is_expired']:
                    logger.warning(f"  用户 {user_id} 会员已过期，跳过")
                    continue

                # 处理每个订阅
                for sub in subs:
                    try:
                        result = self._process_subscription(user_id, sub)
                        if result:
                            success_count += 1
                        else:
                            failed_count += 1
                    except Exception as e:
                        logger.error(f"  订阅 {sub['id']} 处理失败: {e}")
                        failed_count += 1

            # 4. 更新统计
            self.stats['total_runs'] += 1
            self.stats['success_runs'] += success_count
            self.stats['failed_runs'] += failed_count
            self.stats['last_run'] = datetime.now().isoformat()

            logger.info(f"\n任务完成: 成功 {success_count}, 失败 {failed_count}")
            logger.info("=" * 60)

        except Exception as e:
            self.stats['last_error'] = str(e)
            logger.error(f"任务执行失败: {e}", exc_info=True)

    def _process_subscription(self, user_id: str, subscription: dict) -> bool:
        """
        处理单个订阅：爬取 → 分析 → 推送

        Args:
            user_id: 用户ID
            subscription: 订阅信息

        Returns:
            是否成功
        """
        sub_id = subscription['id']
        target = subscription['target']
        platforms = subscription.get('platforms', ['eastmoney'])

        logger.info(f"  处理订阅 #{sub_id}: {target}")

        # 1. 爬取数据
        all_data = []
        for platform in platforms:
            success, msg, data = self.crawler.crawl(
                user_id=user_id,
                platform=platform,
                target=target,
                max_items=50,
                subscription_id=sub_id
            )

            if success:
                logger.info(f"    {platform}: 爬取到 {len(data)} 条数据")
                all_data.extend(data)
            else:
                logger.warning(f"    {platform}: 爬取失败 - {msg}")

        if not all_data:
            logger.warning(f"  订阅 #{sub_id} 没有数据，跳过")
            return False

        # 2. AI分析
        success, msg, analysis = self.analyzer.analyze(
            user_id=user_id,
            data=all_data,
            analysis_type='comprehensive',
            subscription_id=sub_id
        )

        if not success:
            logger.warning(f"  订阅 #{sub_id} 分析失败: {msg}")
            return False

        logger.info(f"    分析完成，消耗 {analysis['tokens_used']} Token")

        # 3. 推送给用户
        if self.push_service:
            push_result = self._push_to_user(user_id, sub_id, subscription, analysis)
            if push_result:
                logger.info(f"    推送成功")
            else:
                logger.warning(f"    推送失败")
        else:
            logger.info("    未配置推送服务，跳过推送")

        # 4. 更新最后推送时间
        self.user_mgr.update_last_push(sub_id)

        return True

    def _push_to_user(
        self,
        user_id: str,
        subscription_id: int,
        subscription: dict,
        analysis: dict
    ) -> bool:
        """
        推送分析结果给用户

        Args:
            user_id: 用户ID
            subscription_id: 订阅ID
            subscription: 订阅信息
            analysis: 分析结果

        Returns:
            是否成功
        """
        try:
            # 格式化推送内容
            title = f"📊 {subscription['target_display_name']} 更新"

            # 提取关键信息
            sentiment = analysis.get('sentiment', 'neutral')
            sentiment_emoji = {
                'positive': '📈',
                'negative': '📉',
                'neutral': '➡️'
            }.get(sentiment, '➡️')

            summary = analysis.get('summary', analysis.get('content', ''))[:500]

            content = (
                f"{sentiment_emoji} 市场情绪: {sentiment}\n"
                f"📝 数据量: {analysis['data_count']}条\n"
                f"🏷️ 平台: {analysis['platform']}\n\n"
                f"摘要:\n{summary}\n\n"
                f"💡 Token消耗: {analysis['tokens_used']}\n"
                f"💰 剩余余额: {analysis['remaining_balance']}"
            )

            # 调用推送服务
            if asyncio.iscoroutinefunction(self.push_service.push_to_user):
                # 异步推送
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                success, msg = loop.run_until_complete(
                    self.push_service.push_to_user(
                        user_id=user_id,
                        subscription_id=subscription_id,
                        title=title,
                        content=content
                    )
                )
                loop.close()
            else:
                # 同步推送
                success, msg = self.push_service.push_to_user(
                    user_id=user_id,
                    subscription_id=subscription_id,
                    title=title,
                    content=content
                )

            return success

        except Exception as e:
            logger.error(f"推送失败: {e}")
            return False

    # ============================================
    # 辅助任务
    # ============================================

    def _check_membership_expiry(self):
        """检查会员过期（每天执行）"""
        try:
            logger.info("执行会员过期检查...")

            # 这里可以查询即将过期的会员并发送提醒
            # 示例逻辑：
            # expired_users = self.user_mgr.get_expired_users()
            # for user in expired_users:
            #     send_expiry_notification(user)

            logger.info("会员检查完成")

        except Exception as e:
            logger.error(f"会员检查失败: {e}")

    def _check_token_balance(self):
        """检查Token余额（每小时执行）"""
        try:
            logger.info("执行Token余额检查...")

            # 这里可以查询余额不足的用户并发送提醒
            # 示例逻辑：
            # low_balance_users = self.user_mgr.get_low_balance_users(threshold=1000)
            # for user in low_balance_users:
            #     send_balance_warning(user)

            logger.info("余额检查完成")

        except Exception as e:
            logger.error(f"余额检查失败: {e}")

    # ============================================
    # 手动触发任务
    # ============================================

    def trigger_crawl_now(self):
        """手动触发爬取任务"""
        logger.info("手动触发爬取任务...")
        self._crawl_analyze_push_job()

    def get_stats(self) -> dict:
        """获取调度器统计信息"""
        return {
            **self.stats,
            'is_running': self.is_running,
            'next_run': self._get_next_run_time()
        }

    def _get_next_run_time(self) -> Optional[str]:
        """获取下次运行时间"""
        job = self.scheduler.get_job('crawl_analyze_push')
        if job and job.next_run_time:
            return job.next_run_time.isoformat()
        return None


# ============================================
# 使用示例
# ============================================

if __name__ == "__main__":
    import time

    # 初始化组件
    user_mgr = UserManager("/tmp/test_scheduler.db")
    crawler = CrawlerAgent(user_mgr)
    analyzer = AnalyzerAgent(user_mgr, mock_mode=True)

    # 创建测试用户和订阅
    user_id = "telegram_test_scheduler"
    user_mgr.register_user(user_id)

    success, msg, sub_id = user_mgr.create_subscription(
        user_id=user_id,
        subscription_type='stock',
        target='TSLA',
        platforms=['eastmoney'],
        push_channels=['telegram']
    )

    print(f"创建订阅: {success} - {msg}")

    # 创建调度器（每1分钟执行一次，用于测试）
    scheduler = TrendRadarScheduler(
        user_manager=user_mgr,
        crawler_agent=crawler,
        analyzer_agent=analyzer,
        push_service=None,  # 暂不配置推送
        crawl_interval_minutes=1
    )

    # 启动调度器
    scheduler.start()

    # 运行5分钟后停止
    try:
        print("\n调度器运行中，按Ctrl+C停止...\n")
        time.sleep(300)
    except KeyboardInterrupt:
        print("\n停止调度器...")

    scheduler.stop()

    # 打印统计信息
    stats = scheduler.get_stats()
    print(f"\n统计信息:")
    print(f"  总运行次数: {stats['total_runs']}")
    print(f"  成功: {stats['success_runs']}")
    print(f"  失败: {stats['failed_runs']}")
    print(f"  最后运行: {stats['last_run']}")
