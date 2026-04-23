#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据采集任务测试脚本

测试大宗商品数据的定时采集功能
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from trendradar.jobs.data_collector import DataCollectorJob


def test_data_collector():
    """测试数据采集器"""
    print("\n" + "=" * 60)
    print("  测试：数据采集任务")
    print("=" * 60)

    # 检查配置文件
    if not os.path.exists("config/data_sources.yaml"):
        print("\n⚠️  配置文件不存在")
        print("请先复制示例配置:")
        print("  cp config/data_sources_example.yaml config/data_sources.yaml")
        return

    # 创建数据采集任务
    job = DataCollectorJob(
        config_path="config/data_sources.yaml",
        db_path="output/commodity_data.db",
    )

    try:
        # 测试1: 强制采集所有数据源
        print("\n" + "-" * 60)
        print("测试1: 强制采集所有数据源")
        print("-" * 60)
        stats = job.run(force=True)

        if stats["total"] > 0:
            print(f"\n✓ 采集完成")
            print(f"  总数: {stats['total']}")
            print(f"  成功: {stats['success']}")
            print(f"  失败: {stats['failed']}")
            print(f"  跳过: {stats['skipped']}")

            if stats["success"] > 0:
                print("\n成功采集的数据源:")
                for result in stats["results"]:
                    if result["success"]:
                        print(f"  - {result['source_id']}: {result['record_count']} 条")

            if stats["failed"] > 0:
                print("\n失败的数据源:")
                for result in stats["results"]:
                    if not result["success"]:
                        print(f"  - {result['source_id']}: {result['error']}")

        # 测试2: 显示统计信息
        print("\n" + "-" * 60)
        print("测试2: 数据库统计信息")
        print("-" * 60)

        db_stats = job.get_statistics()
        if db_stats:
            print(f"\n总数据量: {db_stats['total_count']} 条")
            print(f"数据源数量: {db_stats['source_count']} 个")
            print(f"数据日期范围: {db_stats['earliest_date']} ~ {db_stats['latest_date']}")

            print("\n按产品统计（前10个）:")
            for product, count in list(db_stats["by_product"].items())[:10]:
                print(f"  {product:20s}: {count:>6d} 条")

            print("\n按类别统计:")
            for category, count in db_stats["by_category"].items():
                print(f"  {category:20s}: {count:>6d} 条")

            print("\n按数据源统计（前5个）:")
            for source_id, count in list(db_stats["by_source"].items())[:5]:
                print(f"  {source_id:30s}: {count:>6d} 条")

        # 测试3: 智能采集（根据更新频率）
        print("\n" + "-" * 60)
        print("测试3: 智能采集（只采集需要更新的数据源）")
        print("-" * 60)
        print("提示: 由于刚刚采集过，这次应该全部跳过")

        stats2 = job.run(force=False)
        print(f"\n✓ 智能采集完成")
        print(f"  跳过: {stats2['skipped']} 个（未到更新时间）")
        print(f"  采集: {stats2['success']} 个")

    finally:
        job.cleanup()

    print("\n" + "=" * 60)
    print("  测试完成")
    print("=" * 60)
    print("\n下一步:")
    print("  1. 查看数据库: sqlite3 output/commodity_data.db")
    print("  2. 查询数据: SELECT * FROM commodity_data LIMIT 10;")
    print("  3. 查看日志: SELECT * FROM data_fetch_log ORDER BY fetch_time DESC;")
    print()


def main():
    """主函数"""
    test_data_collector()


if __name__ == "__main__":
    main()
