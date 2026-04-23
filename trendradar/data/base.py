# coding=utf-8
"""
数据源基类定义
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class DataSourceType(Enum):
    """数据源类型"""
    AKSHARE = "akshare"          # AKShare数据源
    WEB_SCRAPE = "web_scrape"    # 网页爬取
    API = "api"                   # API接口
    FILE = "file"                 # 文件读取


@dataclass
class DataPoint:
    """数据点"""
    source_id: str              # 数据源ID
    date: datetime              # 数据日期
    value: float                # 数值
    category: str               # 数据类别（price/production/inventory/macro）
    data_type: str              # 数据类型（spot/future/exchange等）
    product: str                # 产品（steel/copper/aluminum等）
    unit: str = ""              # 单位
    region: str = "China"       # 地区
    metadata: Dict = field(default_factory=dict)  # 额外信息


class DataSourceBase(ABC):
    """数据源基类"""

    def __init__(self, source_id: str, config: Dict):
        """
        初始化数据源

        Args:
            source_id: 数据源唯一ID
            config: 配置字典
        """
        self.source_id = source_id
        self.config = config
        self.name = config.get("name", "")
        self.enabled = config.get("enabled", True)
        self.data_category = config.get("data_category", "")
        self.data_type = config.get("data_type", "")
        self.product = config.get("product", "")

    @abstractmethod
    def fetch(self) -> List[DataPoint]:
        """
        获取数据

        Returns:
            数据点列表
        """
        pass

    def is_enabled(self) -> bool:
        """检查是否启用"""
        return self.enabled

    def get_info(self) -> Dict:
        """获取数据源信息"""
        return {
            "id": self.source_id,
            "name": self.name,
            "type": self.config.get("type"),
            "category": self.data_category,
            "product": self.product,
            "enabled": self.enabled
        }
