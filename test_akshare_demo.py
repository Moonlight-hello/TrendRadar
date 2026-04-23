#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AKShare 数据获取演示
演示如何使用AKShare获取钢材/金属行业数据
"""

import sys

# 检查AKShare是否安装
try:
    import akshare as ak
    print("✓ AKShare已安装")
except ImportError:
    print("✗ AKShare未安装")
    print("\n请运行以下命令安装:")
    print("  pip install akshare")
    sys.exit(1)

import pandas as pd
from datetime import datetime


def print_section(title):
    """打印分隔符"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def demo_futures_price():
    """演示：期货价格数据"""
    print_section("1. 期货价格数据")

    try:
        # 螺纹钢期货
        print("\n📊 螺纹钢期货（RB）:")
        df = ak.futures_main_sina(symbol="RB0")
        print(df.tail())
        print(f"   最新收盘价: {df.iloc[-1]['收盘价']:.2f} 元/吨")

        # 铜期货
        print("\n📊 铜期货（CU）:")
        df = ak.futures_main_sina(symbol="CU0")
        print(df.tail())
        print(f"   最新收盘价: {df.iloc[-1]['收盘价']:.2f} 元/吨")

        # 铝期货
        print("\n📊 铝期货（AL）:")
        df = ak.futures_main_sina(symbol="AL0")
        print(df.tail())
        print(f"   最新收盘价: {df.iloc[-1]['收盘价']:.2f} 元/吨")

    except Exception as e:
        print(f"✗ 获取失败: {e}")


def demo_warehouse_data():
    """演示：仓单库存数据"""
    print_section("2. 交易所仓单库存")

    try:
        # 上期所仓单
        print("\n📦 上海期货交易所仓单:")
        df = ak.get_shfe_warehouse()
        print(df.head(10))

        # 大商所仓单
        print("\n📦 大连商品交易所仓单:")
        df = ak.get_dce_warehouse()
        print(df.head(10))

    except Exception as e:
        print(f"✗ 获取失败: {e}")


def demo_macro_data():
    """演示：宏观经济数据"""
    print_section("3. 宏观经济数据")

    try:
        # PMI指数
        print("\n📈 PMI指数（制造业）:")
        df = ak.macro_china_pmi()
        print(df.tail())
        print(f"   最新PMI: {df.iloc[-1]['制造业PMI']}")

        # 粗钢产量
        print("\n🏭 粗钢产量:")
        df = ak.macro_china_steel_production()
        print(df.tail())

    except Exception as e:
        print(f"✗ 获取失败: {e}")


def demo_spot_price():
    """演示：现货价格数据"""
    print_section("4. 现货价格数据")

    try:
        # 螺纹钢现货
        print("\n💰 螺纹钢现货价格:")
        # 注意：这个接口可能需要调整
        df = ak.spot_goods_price(symbol="螺纹钢")
        print(df.head())

    except Exception as e:
        print(f"✗ 获取失败: {e}")
        print("   提示: 现货价格接口可能需要特定参数或已更新")


def demo_trade_data():
    """演示：进出口数据"""
    print_section("5. 进出口数据")

    try:
        # 钢材进出口
        print("\n🌐 钢材进出口数据:")
        df = ak.china_trade_goods(symbol="钢材")
        print(df.tail())

    except Exception as e:
        print(f"✗ 获取失败: {e}")
        print("   提示: 部分接口可能已更新或需要特定参数")


def list_available_futures():
    """列出可用的期货品种"""
    print_section("附录：主要期货品种代码")

    futures_list = {
        "金属": {
            "CU": "铜",
            "AL": "铝",
            "ZN": "锌",
            "PB": "铅",
            "NI": "镍",
            "SN": "锡",
            "AU": "黄金",
            "AG": "白银"
        },
        "黑色系": {
            "RB": "螺纹钢",
            "HC": "热轧卷板",
            "I": "铁矿石",
            "J": "焦炭",
            "JM": "焦煤",
            "SF": "硅铁",
            "SM": "锰硅"
        },
        "能源化工": {
            "FU": "燃料油",
            "BU": "沥青",
            "SC": "原油",
            "PTA": "PTA",
            "MA": "甲醇"
        },
        "农产品": {
            "C": "玉米",
            "M": "豆粕",
            "Y": "豆油",
            "P": "棕榈油"
        }
    }

    for category, items in futures_list.items():
        print(f"\n{category}:")
        for code, name in items.items():
            print(f"  {code:6s} - {name}")


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("  AKShare 数据获取演示")
    print("  支持钢材、金属、宏观等多种数据")
    print("=" * 60)

    # 运行演示
    demo_futures_price()
    demo_warehouse_data()
    demo_macro_data()
    # demo_spot_price()  # 可能需要调整
    # demo_trade_data()  # 可能需要调整

    # 列出可用品种
    list_available_futures()

    print("\n" + "=" * 60)
    print("  演示完成！")
    print("=" * 60)
    print("\n提示:")
    print("  1. 部分接口可能因AKShare版本更新而调整")
    print("  2. 如遇到错误，请查看AKShare文档更新")
    print("  3. 访问: https://akshare.akfamily.xyz/")
    print()


if __name__ == "__main__":
    main()
