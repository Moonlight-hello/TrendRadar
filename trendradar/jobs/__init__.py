# coding=utf-8
"""
TrendRadar Jobs Module

定时任务模块，包含各种后台任务的实现
"""

from trendradar.jobs.data_collector import DataCollectorJob

__all__ = ["DataCollectorJob"]
