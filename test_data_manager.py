#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试数据源管理器
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from trendradar.data import DataSourceManager


def main():
    print("=" * 60)
    print("  数据源管理器测试")
    print("=" * 60)

    # 1. 创建数据源管理器
    config_path = "config/data_sources.yaml"

    if not os.path.exists(config_path):
        print(f"\n⚠️  配置文件不存在: {config_path}")
        print("请先复制示例配置:")
        print(f"  cp config/data_sources_example.yaml {config_path}")
        return

    manager = DataSourceManager(config_path)

    # 2. 列出所有数据源
    print("\n" + "-" * 60)
    print("可用数据源:")
    print("-" * 60)

    sources = manager.list_sources()
    if not sources:
        print("  (无数据源配置)")
        return

    for source in sources:
        status = "✓ 启用" if source['enabled'] else "✗ 禁用"
        print(f"  {status} | {source['id']:30s} | {source['name']}")

    # 3. 测试获取单个数据源
    print("\n" + "-" * 60)
    print("测试获取单个数据源（螺纹钢期货）:")
    print("-" * 60)

    try:
        data = manager.fetch_one("rebar_future_price")

        if data:
            print(f"\n成功获取 {len(data)} 条数据")
            print("\n最近5条数据:")
            for dp in data[-5:]:
                print(f"  {dp.date.strftime('%Y-%m-%d')}: {dp.value:>8.2f} {dp.unit}")
        else:
            print("  (无数据)")

    except Exception as e:
        print(f"✗ 获取失败: {e}")

    # 4. 测试批量获取（仅前3个）
    print("\n" + "-" * 60)
    print("测试批量获取（前3个数据源）:")
    print("-" * 60)

    # 只测试前3个数据源
    test_sources = list(manager.sources.keys())[:3]

    for source_id in test_sources:
        try:
            data = manager.fetch_one(source_id)
            source_name = manager.sources[source_id].name

            if data:
                latest = data[-1]
                print(f"  ✓ {source_name:20s}: {len(data):4d}条, 最新={latest.value:.2f} {latest.unit}")
            else:
                print(f"  ✗ {source_name:20s}: 无数据")

        except Exception as e:
            print(f"  ✗ {source_id}: {e}")

    print("\n" + "=" * 60)
    print("  测试完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
