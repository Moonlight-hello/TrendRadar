# coding=utf-8
"""
通用平台适配框架 - 示例实现

展示如何通过配置文件快速接入新平台
"""

import asyncio
import httpx
import yaml
import jinja2
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path
from abc import ABC, abstractmethod


# ============================================
# 配置模型
# ============================================

@dataclass
class PlatformConfig:
    """平台配置模型"""

    # 基础信息
    id: str
    name: str
    display_name: str
    description: str = ""
    website: str = ""

    # API配置
    api: Dict[str, Any] = field(default_factory=dict)

    # 功能特性
    features: Dict[str, Any] = field(default_factory=dict)

    # 字段映射
    fields: Dict[str, Dict[str, str]] = field(default_factory=dict)

    # 分页配置
    pagination: Dict[str, Any] = field(default_factory=dict)

    # 请求参数模板
    request_params: Dict[str, Any] = field(default_factory=dict)

    # 速率限制
    rate_limit: Dict[str, Any] = field(default_factory=dict)

    # 并发控制
    concurrency: Dict[str, int] = field(default_factory=dict)

    # 数据存储
    data_storage: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_yaml(cls, yaml_path: str) -> "PlatformConfig":
        """从YAML文件加载配置"""
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        platform_data = data.get('platform', {})

        return cls(
            id=platform_data.get('id'),
            name=platform_data.get('name'),
            display_name=platform_data.get('display_name'),
            description=platform_data.get('description', ''),
            website=platform_data.get('website', ''),
            api=data.get('api', {}),
            features=data.get('features', {}),
            fields=data.get('fields', {}),
            pagination=data.get('pagination', {}),
            request_params=data.get('request_params', {}),
            rate_limit=data.get('rate_limit', {}),
            concurrency=data.get('concurrency', {}),
            data_storage=data.get('data_storage', {}),
        )


# ============================================
# 字段映射器
# ============================================

class UniversalFieldMapper:
    """通用字段映射器"""

    def __init__(self, config: PlatformConfig):
        self.config = config
        self.content_mapping = config.fields.get('content', {})
        self.comment_mapping = config.fields.get('comment', {})
        self.creator_mapping = config.fields.get('creator', {})

    def map_content(self, raw_data: Dict) -> Dict:
        """将原始数据映射为标准格式"""
        mapped = {}

        for standard_key, field_path in self.content_mapping.items():
            if standard_key == 'extra':
                # 处理额外字段
                continue
            elif standard_key == 'url_template':
                # 处理URL模板
                mapped['url'] = self._render_template(field_path, raw_data)
            else:
                # 普通字段提取
                value = self._extract_value(raw_data, field_path)
                mapped[standard_key] = value

        # 处理额外字段
        if 'extra' in self.content_mapping:
            mapped['extra'] = {}
            for extra_field in self.content_mapping['extra']:
                mapped['extra'][extra_field] = raw_data.get(extra_field)

        return mapped

    def map_comment(self, raw_data: Dict) -> Dict:
        """映射评论数据"""
        return {
            standard_key: self._extract_value(raw_data, field_path)
            for standard_key, field_path in self.comment_mapping.items()
        }

    def map_creator(self, raw_data: Dict) -> Dict:
        """映射创作者数据"""
        return {
            standard_key: self._extract_value(raw_data, field_path)
            for standard_key, field_path in self.creator_mapping.items()
        }

    def _extract_value(self, data: Dict, path: str) -> Any:
        """
        提取嵌套字段值

        支持格式:
        - "field_name" - 直接字段
        - "user.user_id" - 嵌套字段
        - "data[0].id" - 数组索引
        """
        if not path:
            return None

        keys = path.replace('[', '.').replace(']', '').split('.')
        value = data

        for key in keys:
            if value is None:
                return None

            # 处理数组索引
            if key.isdigit():
                try:
                    value = value[int(key)]
                except (IndexError, TypeError):
                    return None
            else:
                # 处理字典键
                if isinstance(value, dict):
                    value = value.get(key)
                else:
                    return None

        return value

    def _render_template(self, template: str, data: Dict) -> str:
        """渲染Jinja2模板"""
        try:
            return jinja2.Template(template).render(**data)
        except Exception:
            return template


# ============================================
# API客户端
# ============================================

class UniversalApiClient:
    """通用API客户端"""

    def __init__(self, config: PlatformConfig):
        self.config = config
        self.base_url = config.api.get('base_url', '')
        self.headers = config.api.get('headers', {})
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def close(self):
        """关闭客户端"""
        if self._client:
            await self._client.aclose()

    def get_client(self) -> httpx.AsyncClient:
        """获取HTTP客户端"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                headers=self.headers,
                timeout=30.0,
                follow_redirects=True
            )
        return self._client

    async def request(
        self,
        endpoint_name: str,
        **params
    ) -> Dict:
        """
        统一请求方法

        Args:
            endpoint_name: 端点名称（如 'search_stock', 'stock_posts'）
            **params: 请求参数

        Returns:
            响应数据
        """
        # 获取端点URL
        endpoint = self.config.api.get('endpoints', {}).get(endpoint_name)
        if not endpoint:
            raise ValueError(f"Endpoint {endpoint_name} not found in config")

        # 渲染URL（支持路径参数）
        url = self._render_url(endpoint, params)
        full_url = f"{self.base_url}{url}"

        # 获取请求参数模板
        request_config = self.config.request_params.get(endpoint_name, {})
        method = request_config.get('method', 'GET')
        param_template = request_config.get('params', {})

        # 渲染请求参数
        rendered_params = self._render_params(param_template, params)

        # 发送请求
        client = self.get_client()
        try:
            response = await client.request(
                method=method,
                url=full_url,
                params=rendered_params if method == 'GET' else None,
                json=rendered_params if method == 'POST' else None
            )
            response.raise_for_status()

            return response.json()

        except httpx.HTTPStatusError as e:
            print(f"[UniversalApiClient] HTTP error {e.response.status_code}: {e}")
            raise
        except Exception as e:
            print(f"[UniversalApiClient] Request error: {e}")
            raise

    def _render_url(self, template: str, params: Dict) -> str:
        """渲染URL模板"""
        return jinja2.Template(template).render(**params)

    def _render_params(self, template: Dict, params: Dict) -> Dict:
        """渲染请求参数模板"""
        rendered = {}

        for key, value_template in template.items():
            if isinstance(value_template, str) and '{' in value_template:
                # 渲染模板字符串
                rendered[key] = jinja2.Template(value_template).render(**params)
            else:
                # 直接使用值
                rendered[key] = value_template

        return rendered


# ============================================
# 处理器
# ============================================

class UniversalProcessor:
    """通用数据处理器"""

    def __init__(
        self,
        client: UniversalApiClient,
        field_mapper: UniversalFieldMapper,
        config: PlatformConfig
    ):
        self.client = client
        self.field_mapper = field_mapper
        self.config = config

    async def search(self, keyword: str, **kwargs) -> List[Dict]:
        """
        通用搜索方法

        Args:
            keyword: 搜索关键词
            **kwargs: 额外参数

        Returns:
            标准化的内容列表
        """
        # 检查是否支持搜索
        supported_types = self.config.features.get('supported_crawl_types', [])
        if 'search' not in supported_types:
            raise ValueError(f"Platform {self.config.id} does not support search")

        # 调用API（假设端点名为 'search' 或 'search_stock'）
        endpoint = 'search_stock' if 'search_stock' in self.config.api.get('endpoints', {}) else 'search'

        raw_data = await self.client.request(endpoint, keyword=keyword, **kwargs)

        # 提取内容列表（使用配置的路径）
        data_path = self.config.pagination.get('response', {}).get('data_field', 'data')
        items = self._extract_value(raw_data, data_path) or []

        # 映射字段
        return [self.field_mapper.map_content(item) for item in items]

    async def get_content_list(self, **kwargs) -> List[Dict]:
        """
        获取内容列表

        Args:
            **kwargs: 查询参数（如 stock_code, page 等）

        Returns:
            标准化的内容列表
        """
        # 调用API
        raw_data = await self.client.request('stock_posts', **kwargs)

        # 提取列表
        data_path = self.config.pagination.get('response', {}).get('data_field', 'data')
        items = self._extract_value(raw_data, data_path) or []

        # 映射字段
        return [self.field_mapper.map_content(item) for item in items]

    async def get_comments(self, content_id: str, **kwargs) -> List[Dict]:
        """
        获取评论列表

        Args:
            content_id: 内容ID
            **kwargs: 额外参数

        Returns:
            标准化的评论列表
        """
        if not self.config.features.get('enable_comments'):
            return []

        # 调用API
        raw_data = await self.client.request('post_comments', post_id=content_id, **kwargs)

        # 提取列表
        data_path = self.config.pagination.get('response', {}).get('data_field', 'data')
        items = self._extract_value(raw_data, data_path) or []

        # 映射字段
        return [self.field_mapper.map_comment(item) for item in items]

    def _extract_value(self, data: Dict, path: str) -> Any:
        """提取嵌套字段值（同 UniversalFieldMapper）"""
        if not path:
            return data

        keys = path.split('.')
        value = data

        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None

            if value is None:
                return None

        return value


# ============================================
# 平台工厂
# ============================================

class UniversalPlatformFactory:
    """通用平台工厂"""

    _platforms: Dict[str, PlatformConfig] = {}

    @classmethod
    def register_from_config(cls, config_path: str):
        """从配置文件注册平台"""
        config = PlatformConfig.from_yaml(config_path)
        cls._platforms[config.id] = config
        print(f"[Factory] Registered platform: {config.display_name} ({config.id})")

    @classmethod
    def register_all_platforms(cls, config_dir: str = "platforms"):
        """注册所有平台"""
        config_dir = Path(config_dir)

        if not config_dir.exists():
            print(f"[Factory] Config directory not found: {config_dir}")
            return

        for config_file in config_dir.glob("*.yaml"):
            try:
                cls.register_from_config(str(config_file))
            except Exception as e:
                print(f"[Factory] Failed to register {config_file}: {e}")

    @classmethod
    def create_crawler(cls, platform_id: str) -> "UniversalCrawler":
        """创建爬虫实例"""
        if platform_id not in cls._platforms:
            raise ValueError(f"Platform {platform_id} not registered")

        config = cls._platforms[platform_id]
        return UniversalCrawler(config)

    @classmethod
    def list_platforms(cls) -> List[str]:
        """列出所有已注册平台"""
        return list(cls._platforms.keys())

    @classmethod
    def get_platform_info(cls, platform_id: str) -> Optional[PlatformConfig]:
        """获取平台配置信息"""
        return cls._platforms.get(platform_id)


# ============================================
# 通用爬虫
# ============================================

class UniversalCrawler:
    """通用爬虫"""

    def __init__(self, config: PlatformConfig):
        self.config = config

        # 初始化组件
        self.client = UniversalApiClient(config)
        self.field_mapper = UniversalFieldMapper(config)
        self.processor = UniversalProcessor(self.client, self.field_mapper, config)

    async def search(self, keyword: str, limit: int = 20) -> List[Dict]:
        """
        搜索内容

        Args:
            keyword: 搜索关键词
            limit: 返回数量限制

        Returns:
            内容列表
        """
        print(f"[{self.config.display_name}] Searching: {keyword}")

        results = await self.processor.search(keyword=keyword)

        print(f"[{self.config.display_name}] Found {len(results)} items")

        return results[:limit]

    async def get_content_with_comments(
        self,
        content_id: str,
        max_comments: int = 50
    ) -> Dict:
        """
        获取内容及其评论

        Args:
            content_id: 内容ID
            max_comments: 最大评论数

        Returns:
            包含内容和评论的字典
        """
        print(f"[{self.config.display_name}] Fetching content: {content_id}")

        # 获取评论
        comments = await self.processor.get_comments(content_id)

        print(f"[{self.config.display_name}] Found {len(comments)} comments")

        return {
            'content_id': content_id,
            'comments': comments[:max_comments]
        }

    async def close(self):
        """关闭爬虫"""
        await self.client.close()


# ============================================
# 使用示例
# ============================================

async def example_usage():
    """使用示例"""

    print("=" * 60)
    print("通用平台适配框架 - 使用示例")
    print("=" * 60)

    # 1. 注册平台（从配置文件）
    print("\n1. 注册平台")
    config_path = "examples/platform_config_example_eastmoney.yaml"

    if not Path(config_path).exists():
        print(f"配置文件不存在: {config_path}")
        print("请先创建配置文件")
        return

    UniversalPlatformFactory.register_from_config(config_path)

    # 2. 列出已注册平台
    print("\n2. 已注册平台:")
    platforms = UniversalPlatformFactory.list_platforms()
    for platform_id in platforms:
        info = UniversalPlatformFactory.get_platform_info(platform_id)
        print(f"  - {info.display_name} ({info.id})")

    # 3. 创建爬虫
    print("\n3. 创建爬虫")
    crawler = UniversalPlatformFactory.create_crawler("eastmoney")

    # 4. 执行爬取（示例）
    print("\n4. 执行爬取（模拟）")
    print("  注意：这只是框架示例，实际API可能不同")

    try:
        # 搜索示例（需要实际API）
        # results = await crawler.search("贵州茅台")
        # print(f"  搜索结果: {len(results)} 条")

        print("  框架已就绪，可以开始爬取")

    finally:
        # 5. 关闭爬虫
        await crawler.close()
        print("\n5. 爬虫已关闭")

    print("\n" + "=" * 60)
    print("示例完成")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(example_usage())
