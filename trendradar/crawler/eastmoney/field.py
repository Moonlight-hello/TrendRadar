# -*- coding: utf-8 -*-
"""
东方财富股吧字段枚举定义
"""

from enum import Enum


class SearchSortType(Enum):
    """搜索排序类型"""
    LATEST = "latest"  # 最新
    HOTTEST = "hottest"  # 最热


class PostType(Enum):
    """帖子类型"""
    POST = "post"  # 普通帖子
    COMMENT = "comment"  # 评论
    REPLY = "reply"  # 回复


class ContentType(Enum):
    """内容类型"""
    TEXT = "text"  # 文本
    IMAGE = "image"  # 图片
    VIDEO = "video"  # 视频
    LINK = "link"  # 链接
