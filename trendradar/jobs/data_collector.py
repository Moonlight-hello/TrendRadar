#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大宗商品数据采集任务

定期采集配置的数据源，保存到数据库
支持不同的更新频率：实时（hourly）、日度（daily）、月度（monthly）
"""

import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

from trendradar.data import DataSourceManager
from trendradar.storage.data_storage import DataStorage


class DataCollectorJob:
    """大宗商品数据采集任务"""

    def __init__(
        self,
        config_path: str = "config/data_sources.yaml",
        db_path: str = "output/commodity_data.db",
        timezone: str = "Asia/Shanghai",
    ):
        """
        初始化数据采集任务

        Args:
            config_path: 数据源配置文件路径
            db_path: 数据库文件路径
            timezone: 时区
        """
        self.config_path = config_path
        self.db_path = db_path
        self.timezone = timezone
        self.manager = None
        self.storage = None

    def _init_components(self):
        """初始化组件（延迟加载）"""
        if self.manager is None:
            if not os.path.exists(self.config_path):
                print(f"[数据采集] 配置文件不存在: {self.config_path}")
                return False

            try:
                self.manager = DataSourceManager(self.config_path)
                print(f"[数据采集] 加载了 {len(self.manager.sources)} 个数据源")
            except Exception as e:
                print(f"[数据采集] 加载配置失败: {e}")
                return False

        if self.storage is None:
            try:
                # 确保输出目录存在
                db_dir = Path(self.db_path).parent
                db_dir.mkdir(parents=True, exist_ok=True)

                self.storage = DataStorage(self.db_path)
                print(f"[数据采集] 数据库已连接: {self.db_path}")
            except Exception as e:
                print(f"[数据采集] 数据库连接失败: {e}")
                return False

        return True

    def should_collect(self, source_id: str) -> bool:
        """
        判断数据源是否应该采集

        基于上次采集时间和配置的更新频率判断

        Args:
            source_id: 数据源ID

        Returns:
            是否应该采集
        """
        if not self.storage:
            return False

        # 获取上次采集记录
        last_fetch = self.storage.get_last_fetch_log(source_id)

        if not last_fetch:
            # 从未采集过，应该采集
            return True

        last_time = last_fetch.get("fetch_time")
        status = last_fetch.get("status")
        record_count = last_fetch.get("record_count", 0)

        if not last_time:
            return True

        # 获取数据源配置
        source = self.manager.sources.get(source_id)
        if not source:
            return False

        # 获取更新频率配置（默认为每小时）
        update_config = getattr(source, "update_frequency", "hourly")
        if isinstance(update_config, dict):
            frequency = update_config.get("frequency", "hourly")
        else:
            frequency = update_config

        # 计算时间间隔
        now = datetime.now()
        time_diff = now - last_time

        # 根据频率判断是否应该采集
        if frequency == "hourly":
            # 每小时更新：间隔 >= 1 小时
            return time_diff >= timedelta(hours=1)
        elif frequency == "daily":
            # 每日更新：间隔 >= 1 天
            return time_diff >= timedelta(days=1)
        elif frequency == "weekly":
            # 每周更新：间隔 >= 7 天
            return time_diff >= timedelta(days=7)
        elif frequency == "monthly":
            # 每月更新：间隔 >= 30 天
            return time_diff >= timedelta(days=30)
        else:
            # 未知频率，默认每小时
            return time_diff >= timedelta(hours=1)

    def collect_source(self, source_id: str) -> Dict:
        """
        采集单个数据源

        Args:
            source_id: 数据源ID

        Returns:
            采集结果 {success, record_count, error}
        """
        result = {
            "source_id": source_id,
            "success": False,
            "record_count": 0,
            "error": None,
        }

        try:
            # 获取数据
            print(f"[数据采集] 开始采集: {source_id}")
            data_points = self.manager.fetch_one(source_id)

            if not data_points:
                result["error"] = "无数据返回"
                print(f"[数据采集] {source_id}: 无数据返回")
                return result

            # 保存到数据库
            saved_count = self.storage.save(data_points)
            result["success"] = True
            result["record_count"] = saved_count

            print(f"[数据采集] {source_id}: 成功保存 {saved_count} 条数据")

            # 记录采集日志
            self.storage.log_fetch(
                source_id=source_id,
                status="success",
                record_count=saved_count,
                error_message=None,
            )

        except Exception as e:
            result["error"] = str(e)
            print(f"[数据采集] {source_id}: 采集失败 - {e}")

            # 记录失败日志
            if self.storage:
                self.storage.log_fetch(
                    source_id=source_id,
                    status="failed",
                    record_count=0,
                    error_message=str(e),
                )

        return result

    def run(self, force: bool = False) -> Dict:
        """
        执行数据采集任务

        Args:
            force: 是否强制采集（忽略更新频率检查）

        Returns:
            采集结果统计
        """
        print("\n" + "=" * 60)
        print("  大宗商品数据采集任务")
        print("=" * 60)

        # 初始化组件
        if not self._init_components():
            return {
                "total": 0,
                "success": 0,
                "failed": 0,
                "skipped": 0,
                "results": [],
            }

        # 统计信息
        stats = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "skipped": 0,
            "results": [],
        }

        # 获取所有启用的数据源
        sources = self.manager.list_sources()
        stats["total"] = len(sources)

        print(f"\n发现 {stats['total']} 个数据源")

        # 遍历数据源
        for source_info in sources:
            source_id = source_info["id"]

            # 检查是否应该采集
            if not force and not self.should_collect(source_id):
                stats["skipped"] += 1
                print(f"[数据采集] {source_id}: 跳过（未到更新时间）")
                continue

            # 采集数据
            result = self.collect_source(source_id)
            stats["results"].append(result)

            if result["success"]:
                stats["success"] += 1
            else:
                stats["failed"] += 1

        # 输出统计
        print("\n" + "-" * 60)
        print("采集统计:")
        print(f"  总数: {stats['total']}")
        print(f"  成功: {stats['success']}")
        print(f"  失败: {stats['failed']}")
        print(f"  跳过: {stats['skipped']}")
        print("=" * 60 + "\n")

        return stats

    def get_statistics(self) -> Optional[Dict]:
        """
        获取数据库统计信息

        Returns:
            统计信息字典
        """
        if not self._init_components():
            return None

        return self.storage.get_statistics()

    def cleanup(self):
        """清理资源"""
        if self.storage:
            self.storage.close()
            self.storage = None


def main():
    """测试入口"""
    import argparse

    parser = argparse.ArgumentParser(description="大宗商品数据采集任务")
    parser.add_argument(
        "--force",
        action="store_true",
        help="强制采集所有数据源（忽略更新频率）",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="显示数据库统计信息",
    )
    parser.add_argument(
        "--config",
        default="config/data_sources.yaml",
        help="数据源配置文件路径",
    )
    parser.add_argument(
        "--db",
        default="output/commodity_data.db",
        help="数据库文件路径",
    )

    args = parser.parse_args()

    # 创建任务
    job = DataCollectorJob(
        config_path=args.config,
        db_path=args.db,
    )

    try:
        if args.stats:
            # 显示统计信息
            stats = job.get_statistics()
            if stats:
                print("\n" + "=" * 60)
                print("  数据库统计信息")
                print("=" * 60)
                print(f"\n总数据量: {stats['total_count']} 条")
                print(f"数据源数量: {stats['source_count']} 个")
                print(f"最早数据: {stats['earliest_date']}")
                print(f"最新数据: {stats['latest_date']}")

                print("\n按产品统计:")
                for product, count in list(stats["by_product"].items())[:10]:
                    print(f"  {product:20s}: {count:>6d} 条")

                print("\n按类别统计:")
                for category, count in stats["by_category"].items():
                    print(f"  {category:20s}: {count:>6d} 条")

                print("\n按数据源统计:")
                for source_id, count in list(stats["by_source"].items())[:10]:
                    print(f"  {source_id:30s}: {count:>6d} 条")

                print("=" * 60 + "\n")
        else:
            # 执行采集任务
            job.run(force=args.force)

    finally:
        job.cleanup()


if __name__ == "__main__":
    main()
