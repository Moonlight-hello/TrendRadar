"""
数据采集模块

提供大宗商品数据获取能力：
- 期货价格（实时）
- 现货价格（日度）
- 库存数据（日度/周度）
- 产量数据（月度）
- 宏观数据（月度）
"""

from .source_manager import DataSourceManager, DataPoint
from .base import DataSourceBase, DataSourceType

__all__ = [
    'DataSourceManager',
    'DataPoint',
    'DataSourceBase',
    'DataSourceType',
]
