# coding=utf-8
"""
数据源管理器 - 配置驱动的数据获取系统
"""

import yaml
import os
from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd

from .base import DataSourceBase, DataSourceType, DataPoint

# 动态导入AKShare
try:
    import akshare as ak
    AKSHARE_AVAILABLE = True
except ImportError:
    AKSHARE_AVAILABLE = False
    print("⚠️  AKShare未安装，请运行: pip install akshare")


class AKShareDataSource(DataSourceBase):
    """AKShare数据源"""

    def __init__(self, source_id: str, config: Dict):
        super().__init__(source_id, config)
        self.function = config.get("function", "")
        self.params = config.get("params", {})
        self.field_mapping = config.get("field_mapping", {})

    def fetch(self) -> List[DataPoint]:
        """获取AKShare数据"""
        if not AKSHARE_AVAILABLE:
            raise ImportError("AKShare未安装")

        try:
            # 动态调用AKShare函数
            func = getattr(ak, self.function)
            df = func(**self.params)

            if df is None or df.empty:
                print(f"⚠️  [{self.name}] 返回空数据")
                return []

            # 转换为DataPoint列表
            data_points = self._convert_to_datapoints(df)

            print(f"✓ [{self.name}] 成功获取 {len(data_points)} 条数据")
            return data_points

        except Exception as e:
            print(f"✗ [{self.name}] 获取失败: {e}")
            return []

    def _convert_to_datapoints(self, df: pd.DataFrame) -> List[DataPoint]:
        """转换DataFrame为DataPoint列表"""
        data_points = []

        # 识别日期列和数值列
        date_field = self.field_mapping.get("date", self._guess_date_field(df))
        value_field = self.field_mapping.get("value") or self.field_mapping.get("close") or self._guess_value_field(df)

        if not date_field or not value_field:
            print(f"⚠️  [{self.name}] 无法识别日期或数值字段")
            return []

        for _, row in df.iterrows():
            try:
                # 解析日期
                date_str = str(row.get(date_field, ""))
                if not date_str or date_str == "nan":
                    continue

                date = pd.to_datetime(date_str)

                # 解析数值
                value_str = row.get(value_field)
                if pd.isna(value_str):
                    continue

                value = float(value_str)

                # 创建数据点
                data_point = DataPoint(
                    source_id=self.source_id,
                    date=date,
                    value=value,
                    category=self.data_category,
                    data_type=self.data_type,
                    product=self.product,
                    unit=self._guess_unit(value_field),
                    metadata={
                        "source": self.name,
                        "raw_data": row.to_dict()
                    }
                )
                data_points.append(data_point)

            except Exception as e:
                # 跳过解析失败的行
                continue

        return data_points

    def _guess_date_field(self, df: pd.DataFrame) -> Optional[str]:
        """猜测日期字段"""
        date_candidates = ["日期", "时间", "date", "time", "月份", "年份"]
        for col in df.columns:
            if any(keyword in str(col).lower() for keyword in date_candidates):
                return col
        return None

    def _guess_value_field(self, df: pd.DataFrame) -> Optional[str]:
        """猜测数值字段"""
        value_candidates = ["收盘价", "价格", "close", "price", "数值", "value", "产量", "消费量"]
        for col in df.columns:
            if any(keyword in str(col).lower() for keyword in value_candidates):
                return col

        # 如果没找到，返回第一个数值列
        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                return col

        return None

    def _guess_unit(self, field_name: str) -> str:
        """猜测单位"""
        field_lower = str(field_name).lower()

        if "价格" in field_lower or "price" in field_lower:
            return "元/吨"
        elif "产量" in field_lower or "消费" in field_lower:
            return "万吨"
        elif "库存" in field_lower or "仓单" in field_lower:
            return "吨"

        return ""


class DataSourceManager:
    """数据源管理器"""

    def __init__(self, config_path: str):
        """
        初始化数据源管理器

        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.sources: Dict[str, DataSourceBase] = {}
        self.global_config: Dict = {}

        if os.path.exists(config_path):
            self._load_config()
        else:
            print(f"⚠️  配置文件不存在: {config_path}")

    def _load_config(self):
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            self.global_config = config.get("global", {})
            data_sources = config.get("data_sources", {})

            # 加载每个数据源
            for source_id, source_config in data_sources.items():
                if not source_config.get("enabled", True):
                    continue

                source_type = source_config.get("type", "")

                # 根据类型创建数据源实例
                if source_type == "akshare":
                    source = AKShareDataSource(source_id, source_config)
                # elif source_type == "web_scrape":
                #     source = WebScrapeDataSource(source_id, source_config)
                # elif source_type == "api":
                #     source = APIDataSource(source_id, source_config)
                else:
                    print(f"⚠️  未知数据源类型: {source_type} ({source_id})")
                    continue

                self.sources[source_id] = source

            print(f"✓ 成功加载 {len(self.sources)} 个数据源")

        except Exception as e:
            print(f"✗ 加载配置文件失败: {e}")

    def fetch_all(self) -> Dict[str, List[DataPoint]]:
        """
        获取所有数据源的数据

        Returns:
            {数据源ID: 数据点列表}
        """
        results = {}

        print(f"\n开始获取 {len(self.sources)} 个数据源的数据...\n")

        for source_id, source in self.sources.items():
            try:
                data_points = source.fetch()
                results[source_id] = data_points
            except Exception as e:
                print(f"✗ [{source.name}] 获取失败: {e}")
                results[source_id] = []

        # 统计
        total_count = sum(len(points) for points in results.values())
        success_count = sum(1 for points in results.values() if len(points) > 0)

        print(f"\n✓ 数据获取完成: 成功{success_count}/{len(self.sources)}个数据源, 共{total_count}条数据")

        return results

    def fetch_one(self, source_id: str) -> List[DataPoint]:
        """
        获取单个数据源的数据

        Args:
            source_id: 数据源ID

        Returns:
            数据点列表
        """
        source = self.sources.get(source_id)
        if not source:
            raise ValueError(f"数据源不存在: {source_id}")

        return source.fetch()

    def list_sources(self) -> List[Dict]:
        """
        列出所有数据源

        Returns:
            数据源信息列表
        """
        return [source.get_info() for source in self.sources.values()]

    def get_sources_by_category(self, category: str) -> List[str]:
        """
        按类别获取数据源ID列表

        Args:
            category: 数据类别（price/inventory/production/macro）

        Returns:
            数据源ID列表
        """
        return [
            source_id
            for source_id, source in self.sources.items()
            if source.data_category == category
        ]

    def get_sources_by_product(self, product: str) -> List[str]:
        """
        按产品获取数据源ID列表

        Args:
            product: 产品名称（steel/copper/aluminum等）

        Returns:
            数据源ID列表
        """
        return [
            source_id
            for source_id, source in self.sources.items()
            if source.product == product
        ]
