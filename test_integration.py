#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集成测试：数据源 + 存储
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from trendradar.data import DataSourceManager
from trendradar.storage.data_storage import DataStorage


def test_data_manager():
    """测试数据源管理器"""
    print("\n" + "=" * 60)
    print("  测试1：数据源管理器")
    print("=" * 60)

    manager = DataSourceManager("config/data_sources.yaml")

    # 列出数据源
    sources = manager.list_sources()
    print(f"\n可用数据源: {len(sources)}个")

    for source in sources[:5]:  # 只显示前5个
        print(f"  - {source['id']}: {source['name']}")

    return manager


def test_fetch_single(manager):
    """测试获取单个数据源"""
    print("\n" + "=" * 60)
    print("  测试2：获取单个数据源（螺纹钢期货）")
    print("=" * 60)

    try:
        data = manager.fetch_one("rebar_future_price")

        if data:
            print(f"\n✓ 成功获取 {len(data)} 条数据")
            print("\n最近3条:")
            for dp in data[-3:]:
                print(f"  {dp.date.strftime('%Y-%m-%d')}: {dp.value:>8.2f} {dp.unit}")

            return data
        else:
            print("\n⚠️  无数据返回")
            return []

    except Exception as e:
        print(f"\n✗ 获取失败: {e}")
        return []


def test_storage(data):
    """测试数据存储"""
    print("\n" + "=" * 60)
    print("  测试3：数据存储")
    print("=" * 60)

    storage = DataStorage("output/commodity_data.db")

    # 保存数据
    if data:
        print(f"\n保存 {len(data)} 条数据...")
        storage.save(data)

        # 查询数据
        from datetime import datetime, timedelta

        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)

        results = storage.query(
            product="rebar",
            category="price",
            start_date=start_date,
            end_date=end_date
        )

        print(f"\n✓ 查询到 {len(results)} 条数据（最近7天）")

        if results:
            print("\n查询结果（前3条）:")
            for dp in results[:3]:
                print(f"  {dp.date.strftime('%Y-%m-%d')}: {dp.value:>8.2f} {dp.unit}")

    return storage


def test_statistics(storage):
    """测试统计信息"""
    print("\n" + "=" * 60)
    print("  测试4：数据库统计")
    print("=" * 60)

    stats = storage.get_statistics()

    print(f"\n总数据量: {stats['total_count']} 条")
    print(f"最新数据日期: {stats['latest_date']}")

    print("\n按产品统计:")
    for product, count in list(stats['by_product'].items())[:5]:
        print(f"  {product:15s}: {count:>5d} 条")

    print("\n按类别统计:")
    for category, count in stats['by_category'].items():
        print(f"  {category:15s}: {count:>5d} 条")


def test_batch_fetch(manager, storage):
    """测试批量获取"""
    print("\n" + "=" * 60)
    print("  测试5：批量获取前3个数据源")
    print("=" * 60)

    # 获取前3个数据源
    source_ids = list(manager.sources.keys())[:3]

    all_data = []

    for source_id in source_ids:
        try:
            data = manager.fetch_one(source_id)
            if data:
                all_data.extend(data)
                source_name = manager.sources[source_id].name
                print(f"  ✓ {source_name}: {len(data)} 条")
        except Exception as e:
            print(f"  ✗ {source_id}: {e}")

    # 保存所有数据
    if all_data:
        print(f"\n保存全部 {len(all_data)} 条数据...")
        storage.save(all_data)


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("  TrendRadar 数据源集成测试")
    print("=" * 60)

    # 检查配置文件
    if not os.path.exists("config/data_sources.yaml"):
        print("\n⚠️  配置文件不存在")
        print("请先复制示例配置:")
        print("  cp config/data_sources_example.yaml config/data_sources.yaml")
        return

    # 测试流程
    manager = test_data_manager()
    data = test_fetch_single(manager)
    storage = test_storage(data)
    test_statistics(storage)
    test_batch_fetch(manager, storage)

    print("\n" + "=" * 60)
    print("  测试完成")
    print("=" * 60)
    print("\n下一步:")
    print("  1. 查看数据库: sqlite3 output/commodity_data.db")
    print("  2. 查看统计: SELECT product, COUNT(*) FROM commodity_data GROUP BY product")
    print()


if __name__ == "__main__":
    main()
