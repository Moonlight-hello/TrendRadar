# MediaCrawlerPro 通用平台适配框架设计

> 日期: 2026-04-24 | 版本: 1.0

---

## 📋 设计目标

创建一个**配置驱动**的通用平台适配框架，使得新增平台只需添加配置（URL、Cookie、签名服务等），无需编写大量重复代码。

### 核心理念

```
配置即平台 (Configuration as Platform)
```

- **声明式配置** - 用JSON/YAML定义平台特性
- **约定优于配置** - 遵循统一的目录结构和命名规范
- **可插拔架构** - 平台实现完全解耦
- **最小化代码** - 新增平台只需几十行配置

---

## 🏗️ 当前架构分析

### MediaCrawlerPro-Python 架构优点

1. **设计模式成熟** - 工厂模式、模板方法、处理器模式、策略模式
2. **高度模块化** - 每个平台独立目录，易于维护
3. **抽象层次清晰** - AbstractCrawler, AbstractStore, AbstractApiClient
4. **异步并发支持** - 全程async/await
5. **工具齐全** - 账号池、代理池、缓存、签名服务、断点续爬

### 当前架构局限性

1. **平台间代码重复度高** - 每个平台的core.py、client.py结构相似，大量重复代码
2. **配置分散** - URL、API端点、字段映射散落在各个文件中
3. **新增平台成本高** - 需要创建8-10个文件（core, client, handlers, processors等）
4. **灵活性不足** - 小改动需要修改Python代码，不能热更新

---

## 🎯 通用框架设计

### 核心理念：三层解耦

```
配置层 (Configuration Layer)
    ↓
适配层 (Adapter Layer)
    ↓
执行层 (Execution Layer)
```

### 1. 配置层 - 声明式平台定义

#### 配置文件结构

```yaml
# platforms/xiaohongshu.yaml

platform:
  id: xhs
  name: 小红书
  display_name: "小红书 XiaoHongShu"

api:
  base_url: "https://edith.xiaohongshu.com"
  endpoints:
    search: "/api/sns/web/v1/search/notes"
    note_detail: "/api/sns/web/v1/note/{note_id}"
    user_posts: "/api/sns/web/v1/user/{user_id}/posted"
    comments: "/api/sns/web/v1/comment/page"

  headers:
    User-Agent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    Referer: "https://www.xiaohongshu.com/"
    Accept: "application/json"

  requires_signature: true
  signature_service:
    type: "rpc"  # rpc | local | none
    endpoint: "/sign/xhs"

  requires_authentication: true
  authentication:
    type: "cookie"  # cookie | token | oauth
    cookie_fields:
      - "web_session"
      - "xsec_token"

features:
  supported_crawl_types:
    - search        # 关键词搜索
    - detail        # 帖子详情
    - creator       # 创作者主页
    - homefeed      # 首页推荐

  supported_content_types:
    - note          # 图文笔记
    - video         # 视频

  enable_comments: true
  enable_replies: true
  enable_creator_info: true

fields:
  # 内容字段映射
  content:
    id: "note_id"
    title: "title"
    content: "desc"
    url: "note_url"
    author_id: "user.user_id"
    author_name: "user.nickname"
    publish_time: "time"
    like_count: "liked_count"
    comment_count: "comment_count"
    share_count: "share_count"

  # 评论字段映射
  comment:
    id: "id"
    content: "content"
    author_id: "user_info.user_id"
    author_name: "user_info.nickname"
    create_time: "create_time"
    like_count: "like_count"
    sub_comment_count: "sub_comment_count"

pagination:
  type: "cursor"  # cursor | offset | page
  cursor_field: "cursor"
  page_size_field: "num"
  default_page_size: 20
  max_page_size: 100

rate_limit:
  requests_per_second: 2
  concurrent_requests: 3
  retry_times: 3
  retry_delay: 2

concurrency:
  max_content_tasks: 10
  max_comment_tasks: 5

checkpoint:
  enable: true
  storage: "file"  # file | redis

data_storage:
  formats:
    - csv
    - json
    - db
  csv_path: "data/xhs"
  json_path: "data/xhs"
  db_table_prefix: "xhs_"
```

---

### 2. 适配层 - 通用平台适配器

#### 核心类：UniversalPlatformAdapter

```python
# framework/universal_adapter.py

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path
import yaml
import jinja2

@dataclass
class PlatformConfig:
    """平台配置模型"""
    id: str
    name: str
    display_name: str
    api: Dict[str, Any]
    features: Dict[str, Any]
    fields: Dict[str, Dict[str, str]]
    pagination: Dict[str, Any]
    rate_limit: Dict[str, Any]
    concurrency: Dict[str, int]
    checkpoint: Dict[str, Any]
    data_storage: Dict[str, Any]

    @classmethod
    def from_yaml(cls, yaml_path: str) -> "PlatformConfig":
        """从YAML文件加载配置"""
        with open(yaml_path) as f:
            data = yaml.safe_load(f)
        return cls(**data['platform'], **data)


class UniversalApiClient:
    """通用API客户端"""

    def __init__(self, config: PlatformConfig):
        self.config = config
        self.base_url = config.api['base_url']
        self.headers = config.api.get('headers', {})
        self._client: Optional[httpx.AsyncClient] = None

        # 签名服务
        self.signature_handler = self._create_signature_handler()

        # 认证处理
        self.auth_handler = self._create_auth_handler()

    def _create_signature_handler(self):
        """创建签名处理器"""
        if not self.config.api.get('requires_signature'):
            return None

        sig_config = self.config.api['signature_service']
        if sig_config['type'] == 'rpc':
            return RpcSignatureHandler(sig_config['endpoint'])
        elif sig_config['type'] == 'local':
            return LocalSignatureHandler()
        return None

    def _create_auth_handler(self):
        """创建认证处理器"""
        if not self.config.api.get('requires_authentication'):
            return None

        auth_config = self.config.api['authentication']
        if auth_config['type'] == 'cookie':
            return CookieAuthHandler(auth_config['cookie_fields'])
        elif auth_config['type'] == 'token':
            return TokenAuthHandler()
        return None

    async def request(self, endpoint_name: str, **params) -> Dict:
        """
        统一请求方法

        Args:
            endpoint_name: 端点名称（如 'search', 'note_detail'）
            **params: 请求参数
        """
        # 获取端点URL模板
        endpoint_template = self.config.api['endpoints'][endpoint_name]

        # 渲染URL（支持路径参数）
        url = jinja2.Template(endpoint_template).render(**params)
        full_url = f"{self.base_url}{url}"

        # 添加签名
        if self.signature_handler:
            params = await self.signature_handler.sign(params)

        # 添加认证
        headers = self.headers.copy()
        if self.auth_handler:
            headers.update(await self.auth_handler.get_auth_headers())

        # 发送请求
        response = await self._client.request(
            method=params.pop('method', 'GET'),
            url=full_url,
            headers=headers,
            params=params
        )

        return response.json()


class UniversalFieldMapper:
    """通用字段映射器"""

    def __init__(self, config: PlatformConfig):
        self.content_mapping = config.fields['content']
        self.comment_mapping = config.fields.get('comment', {})

    def map_content(self, raw_data: Dict) -> Dict:
        """将原始数据映射为标准格式"""
        return {
            standard_key: self._extract_value(raw_data, field_path)
            for standard_key, field_path in self.content_mapping.items()
        }

    def map_comment(self, raw_data: Dict) -> Dict:
        """映射评论数据"""
        return {
            standard_key: self._extract_value(raw_data, field_path)
            for standard_key, field_path in self.comment_mapping.items()
        }

    def _extract_value(self, data: Dict, path: str) -> Any:
        """提取嵌套字段值（支持user.user_id格式）"""
        keys = path.split('.')
        value = data
        for key in keys:
            value = value.get(key)
            if value is None:
                return None
        return value


class UniversalProcessor:
    """通用处理器"""

    def __init__(
        self,
        client: UniversalApiClient,
        field_mapper: UniversalFieldMapper,
        config: PlatformConfig
    ):
        self.client = client
        self.field_mapper = field_mapper
        self.config = config

    async def search(self, keyword: str) -> List[Dict]:
        """通用搜索方法"""
        # 检查是否支持搜索
        if 'search' not in self.config.features['supported_crawl_types']:
            raise ValueError(f"Platform {self.config.id} does not support search")

        # 调用API
        raw_data = await self.client.request('search', keyword=keyword)

        # 提取内容列表（假设统一在'items'字段）
        items = raw_data.get('data', {}).get('items', [])

        # 映射字段
        return [self.field_mapper.map_content(item) for item in items]

    async def get_comments(self, content_id: str) -> List[Dict]:
        """通用获取评论方法"""
        if not self.config.features.get('enable_comments'):
            return []

        raw_data = await self.client.request('comments', content_id=content_id)
        items = raw_data.get('data', {}).get('comments', [])

        return [self.field_mapper.map_comment(item) for item in items]


class UniversalCrawler(AbstractCrawler):
    """通用爬虫"""

    def __init__(self, config: PlatformConfig):
        self.config = config

        # 初始化组件
        self.client = UniversalApiClient(config)
        self.field_mapper = UniversalFieldMapper(config)
        self.processor = UniversalProcessor(self.client, self.field_mapper, config)

        # 初始化处理器
        self.checkpoint_manager = create_checkpoint_manager()

        # 并发控制
        self.content_semaphore = asyncio.Semaphore(config.concurrency['max_content_tasks'])
        self.comment_semaphore = asyncio.Semaphore(config.concurrency['max_comment_tasks'])

    async def async_initialize(self):
        """异步初始化"""
        # 代理池
        if config.ENABLE_IP_PROXY:
            proxy_pool = await create_ip_pool()

        # 账号池
        account_pool = AccountWithIpPoolManager(
            platform_name=self.config.id,
            account_save_type=config.ACCOUNT_POOL_SAVE_TYPE,
            proxy_ip_pool=proxy_pool
        )
        await account_pool.async_initialize()

        self.client.account_pool = account_pool

    async def start(self):
        """启动爬虫"""
        crawl_type = config.CRAWLER_TYPE

        if crawl_type == 'search':
            await self._handle_search()
        elif crawl_type == 'detail':
            await self._handle_detail()
        elif crawl_type == 'creator':
            await self._handle_creator()
        elif crawl_type == 'homefeed':
            await self._handle_homefeed()

    async def _handle_search(self):
        """处理搜索爬虫"""
        keywords = config.KEYWORDS
        for keyword in keywords:
            contents = await self.processor.search(keyword)

            for content in contents:
                # 保存内容
                await self.store.store_content(content)

                # 爬取评论
                if self.config.features.get('enable_comments'):
                    comments = await self.processor.get_comments(content['id'])
                    for comment in comments:
                        await self.store.store_comment(comment)
```

---

### 3. 执行层 - 工厂和注册

#### 配置驱动的工厂

```python
# framework/platform_factory.py

class UniversalPlatformFactory:
    """通用平台工厂"""

    _platforms: Dict[str, PlatformConfig] = {}

    @classmethod
    def register_from_config(cls, config_path: str):
        """从配置文件注册平台"""
        config = PlatformConfig.from_yaml(config_path)
        cls._platforms[config.id] = config

    @classmethod
    def register_all_platforms(cls, config_dir: str = "platforms"):
        """注册所有平台"""
        config_dir = Path(config_dir)
        for config_file in config_dir.glob("*.yaml"):
            cls.register_from_config(str(config_file))

    @classmethod
    def create_crawler(cls, platform_id: str) -> AbstractCrawler:
        """创建爬虫实例"""
        if platform_id not in cls._platforms:
            raise ValueError(f"Platform {platform_id} not registered")

        config = cls._platforms[platform_id]

        # 检查是否有自定义实现
        custom_crawler = cls._try_load_custom_crawler(platform_id)
        if custom_crawler:
            return custom_crawler()

        # 使用通用爬虫
        return UniversalCrawler(config)

    @classmethod
    def _try_load_custom_crawler(cls, platform_id: str):
        """尝试加载自定义爬虫实现"""
        try:
            module = __import__(f"media_platform.{platform_id}.core", fromlist=[''])
            crawler_class_name = f"{platform_id.capitalize()}Crawler"
            return getattr(module, crawler_class_name, None)
        except ImportError:
            return None

    @classmethod
    def list_platforms(cls) -> List[str]:
        """列出所有已注册平台"""
        return list(cls._platforms.keys())
```

---

## 📁 新的目录结构

```
MediaCrawlerPro-Python/
├── main.py                          # 使用UniversalPlatformFactory
├── framework/                       # ✨ 通用框架（新增）
│   ├── __init__.py
│   ├── universal_adapter.py         # 通用适配器
│   ├── platform_factory.py          # 平台工厂
│   ├── field_mapper.py              # 字段映射器
│   ├── signature_handler.py         # 签名处理器
│   ├── auth_handler.py              # 认证处理器
│   └── pagination_handler.py        # 分页处理器
│
├── platforms/                       # ✨ 平台配置（新增）
│   ├── xiaohongshu.yaml
│   ├── douyin.yaml
│   ├── bilibili.yaml
│   ├── weibo.yaml
│   ├── kuaishou.yaml
│   ├── tieba.yaml
│   ├── zhihu.yaml
│   └── eastmoney.yaml               # 东方财富配置
│
├── media_platform/                  # 平台特定实现（可选）
│   ├── xhs/                         # 如果需要特殊逻辑，保留
│   │   ├── core.py                  # 继承UniversalCrawler
│   │   └── custom_processor.py      # 自定义处理
│   └── eastmoney/                   # 东方财富（可选保留）
│
├── base/                            # 基础抽象类（保留）
├── config/                          # 全局配置（保留）
├── model/                           # 数据模型（保留）
├── repo/                            # 数据存储（保留）
├── pkg/                             # 工具库（保留）
└── schema/                          # 数据库Schema（保留）
```

---

## 🚀 使用方式

### 1. 新增平台（配置即平台）

只需创建一个YAML文件：

```yaml
# platforms/newplatform.yaml

platform:
  id: newplatform
  name: NewPlatform
  display_name: "新平台"

api:
  base_url: "https://api.newplatform.com"
  endpoints:
    search: "/v1/search"
    detail: "/v1/post/{post_id}"
  headers:
    User-Agent: "Mozilla/5.0"
  requires_signature: false
  requires_authentication: false

features:
  supported_crawl_types:
    - search
  enable_comments: true

fields:
  content:
    id: "id"
    title: "title"
    content: "content"
    url: "url"
```

启动爬虫：

```python
# main.py 无需修改

from framework.platform_factory import UniversalPlatformFactory

# 自动加载所有平台配置
UniversalPlatformFactory.register_all_platforms()

# 创建爬虫
crawler = UniversalPlatformFactory.create_crawler("newplatform")
await crawler.async_initialize()
await crawler.start()
```

### 2. 平台迁移策略

#### 阶段1: 配置化现有平台（优先级高）

1. 为每个现有平台创建YAML配置
2. 保留原有实现作为备份
3. 逐步测试配置驱动的通用爬虫

#### 阶段2: 简化代码（优先级中）

删除重复代码，只保留：
- 平台特定的签名逻辑（如果有）
- 平台特定的数据处理逻辑（如果有）

#### 阶段3: 完全通用化（优先级低）

最终只需：
- YAML配置文件
- 通用框架代码
- 少量平台特定扩展（如需要）

---

## 🎨 设计优势

### 1. 配置即平台

- **新增平台**: 5分钟（创建YAML）
- **修改API**: 1分钟（更新配置）
- **无需编程**: 非技术人员也能添加平台

### 2. 零重复代码

- **统一的Client**: UniversalApiClient
- **统一的Processor**: UniversalProcessor
- **统一的Crawler**: UniversalCrawler

### 3. 灵活可扩展

- **插件机制**: 可选择使用通用实现或自定义实现
- **热更新**: 修改配置无需重启
- **向后兼容**: 保留原有实现

### 4. 易于维护

- **集中配置**: 所有平台配置一目了然
- **版本控制**: YAML易于diff和merge
- **文档清晰**: 配置即文档

---

## 📊 对比分析

### 当前实现 vs 通用框架

| 维度 | 当前实现 | 通用框架 | 改进幅度 |
|-----|---------|---------|---------|
| **新增平台代码量** | ~800行 | ~50行配置 | 减少94% |
| **文件数量** | 8-10个 | 1个 | 减少90% |
| **开发时间** | 2-3天 | 30分钟 | 减少90% |
| **代码重复度** | 高（70%） | 低（5%） | 减少93% |
| **配置灵活性** | 低 | 高 | 提升100% |
| **热更新支持** | 否 | 是 | 新增功能 |

---

## 🔧 实施计划

### Phase 1: 框架开发（2-3天）

1. **Day 1**: 实现UniversalApiClient、UniversalFieldMapper
2. **Day 2**: 实现UniversalProcessor、UniversalCrawler
3. **Day 3**: 实现UniversalPlatformFactory、配置加载

### Phase 2: 平台迁移（1周）

1. 为现有平台创建YAML配置
2. 测试通用爬虫与原有实现的一致性
3. 逐步替换原有实现

### Phase 3: 新平台接入（持续）

1. 东方财富完整配置
2. 其他新平台快速接入

---

## ✅ 成功指标

- [ ] 通用框架代码完成
- [ ] 8个现有平台配置化
- [ ] 通过集成测试
- [ ] 新增平台时间 < 1小时
- [ ] 代码量减少 > 80%
- [ ] 配置文档完善

---

**结论**: 通过配置驱动的通用框架，可以将新增平台的成本降低90%以上，大幅提升开发效率和代码可维护性。 🎉
