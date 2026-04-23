# CommunitySpy - 东方财富股吧评论爬虫工具

## 📖 简介

CommunitySpy 是一个专门爬取东方财富股吧评论的工具，已集成到 TrendRadar Agent 系统中。

## 🎯 功能特性

- ✅ 爬取股吧帖子列表
- ✅ 爬取帖子详情
- ✅ 爬取帖子评论
- ✅ SQLite 数据持久化
- ✅ 支持增量爬取
- ✅ 自动请求延迟
- ✅ 统一工具接口

## 📁 文件结构

```
communityspy/
├── __init__.py       # 模块初始化
├── spider.py         # 核心爬虫类
├── tool.py           # TrendRadar 工具适配器
├── cli.py            # 命令行工具
└── README.md         # 本文档
```

## 🚀 使用方式

### 方式 1: 作为 TrendRadar Agent 工具

```python
from trendradar.agent import AgentHarness, Task
from trendradar.agent.agents import CrawlerAgent
from trendradar.agent.tools.data_sources.communityspy import CommunitySpyTool

# 1. 初始化
harness = AgentHarness()
harness.register_tool(CommunitySpyTool(), "data_source")
harness.register_agent("crawler", CrawlerAgent)

# 2. 创建任务
task = Task(
    type="collect_data",
    params={
        "data_sources": [{
            "type": "communityspy",
            "stock_code": "301293",
            "max_posts": 100
        }]
    }
)

# 3. 执行任务
result = harness.run(task, "crawler")
print(result.data)
```

### 方式 2: 直接使用工具类

```python
from trendradar.agent.tools.data_sources.communityspy import CommunitySpyTool

# 创建工具实例
tool = CommunitySpyTool()

# 执行爬取
result = tool.execute(
    stock_code="301293",
    max_pages=5,
    max_posts=50,
    include_comments=True,
    delay=1.0
)

print(f"成功: {result['success']}")
print(f"统计: {result['stats']}")
print(f"数据库: {result['db_path']}")
```

### 方式 3: 使用爬虫类

```python
from trendradar.agent.tools.data_sources.communityspy import EastMoneyCommentSpider

# 创建爬虫实例
with EastMoneyCommentSpider("301293") as spider:
    # 执行爬取
    stats = spider.crawl(
        max_pages=10,
        max_posts=100,
        include_comments=True,
        delay=1.0
    )

    print(f"帖子数: {stats['posts_count']}")
    print(f"评论数: {stats['comments_count']}")
```

### 方式 4: 命令行工具

```bash
# 基本用法
cd /path/to/TrendRadar/trendradar/agent/tools/data_sources/communityspy
python cli.py 301293

# 指定参数
python cli.py 301293 \
    --max-pages 5 \
    --max-posts 50 \
    --delay 2.0 \
    --output result.json

# 不爬取评论
python cli.py 301293 --no-comments

# 自定义数据库路径
python cli.py 301293 --db-path ./data/my_db.db
```

## 📊 数据结构

### 数据库表结构

#### posts 表（帖子表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| post_id | TEXT | 帖子ID（唯一） |
| stock_code | TEXT | 股票代码 |
| title | TEXT | 帖子标题 |
| content | TEXT | 帖子内容 |
| publish_time | TIMESTAMP | 发布时间 |
| user_id | TEXT | 用户ID |
| user_nickname | TEXT | 用户昵称 |
| click_count | INTEGER | 点击数 |
| comment_count | INTEGER | 评论数 |
| like_count | INTEGER | 点赞数 |
| created_at | TIMESTAMP | 创建时间 |

#### comments 表（评论表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| comment_id | TEXT | 评论ID（唯一） |
| post_id | TEXT | 所属帖子ID |
| content | TEXT | 评论内容 |
| publish_time | TIMESTAMP | 发布时间 |
| user_id | TEXT | 用户ID |
| user_nickname | TEXT | 用户昵称 |
| like_count | INTEGER | 点赞数 |
| created_at | TIMESTAMP | 创建时间 |

### 工具返回格式

```python
{
    "success": True,
    "stock_code": "301293",
    "stats": {
        "posts_count": 100,
        "comments_count": 500,
        "errors": []
    },
    "db_path": "eastmoney_301293.db",
    "message": "成功爬取 100 条帖子和 500 条评论"
}
```

## 🔧 查询工具

除了爬取工具，还提供了查询工具：

```python
from trendradar.agent.tools.data_sources.communityspy import CommunitySpyQueryTool

# 创建查询工具
query_tool = CommunitySpyQueryTool()

# 查询帖子
result = query_tool.execute(
    db_path="eastmoney_301293.db",
    query_type="posts",
    limit=100,
    start_date="2024-01-01",
    end_date="2024-12-31"
)

print(f"查询到 {result['count']} 条帖子")
for post in result['data']:
    print(f"- {post['title']}")

# 查询统计信息
stats_result = query_tool.execute(
    db_path="eastmoney_301293.db",
    query_type="stats"
)

print(f"统计信息: {stats_result['stats']}")
```

## 🎨 统一工具协议

CommunitySpy 遵循 TrendRadar Agent 系统的统一工具协议：

### 工具接口

```python
class BaseTool:
    """工具基类"""

    name: str            # 工具名称
    description: str     # 工具描述
    category: str        # 工具类别
    parameters: Dict     # 参数定义

    def execute(self, **kwargs) -> Dict:
        """执行工具，返回标准化结果"""
        pass
```

### 标准返回格式

所有工具必须返回包含以下字段的字典：

```python
{
    "success": bool,     # 是否成功
    "data": Any,         # 数据结果
    "error": str,        # 错误信息（可选）
    "message": str       # 提示信息（可选）
}
```

## 📝 参数说明

### CommunitySpyTool 参数

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| stock_code | string | ✅ | - | 股票代码 |
| max_pages | integer | ❌ | 10 | 最大爬取页数 |
| max_posts | integer | ❌ | 100 | 最大爬取帖子数 |
| include_comments | boolean | ❌ | True | 是否爬取评论 |
| delay | number | ❌ | 1.0 | 请求延迟（秒） |
| db_path | string | ❌ | auto | 数据库路径 |

### CommunitySpyQueryTool 参数

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| db_path | string | ✅ | - | 数据库路径 |
| query_type | string | ❌ | posts | 查询类型 |
| limit | integer | ❌ | 100 | 结果数量限制 |
| start_date | string | ❌ | - | 开始日期 |
| end_date | string | ❌ | - | 结束日期 |

## ⚠️ 注意事项

1. **请求频率**: 建议设置合理的 delay 参数（建议 1-2 秒），避免请求过快被封禁
2. **数据量**: 首次爬取建议先用小数据量测试（max_posts=10）
3. **存储空间**: SQLite 数据库会占用一定磁盘空间，注意清理
4. **网络稳定**: 需要稳定的网络连接，建议在网络良好时爬取
5. **Cookie**: 某些接口可能需要登录 Cookie，如遇到问题请更新 spider.py 中的 Cookie

## 🔄 与原项目的关系

本工具从原 `/Users/wangxinlong/Code/communityspy` 项目提取核心功能：

- `communityspy.py` → `spider.py` (核心爬虫类)
- 新增 `tool.py` (TrendRadar 工具适配器)
- 新增 `cli.py` (命令行工具)

原项目的其他功能（数据分析、知识蒸馏等）保持独立，可以从数据库中读取数据进行分析。

## 🚧 后续扩展

计划支持的功能：

- [ ] 支持其他社区平台（雪球、淘股吧等）
- [ ] 实时监控模式
- [ ] 情感分析集成
- [ ] 异常检测
- [ ] 数据导出为 CSV/JSON
- [ ] Web 界面

## 📚 相关文档

- [TrendRadar Agent 系统设计](../../../../../AGENT_SYSTEM_DESIGN.md)
- [原 CommunitySpy 项目文档](/Users/wangxinlong/Code/communityspy/ANALYSIS_README.md)
- [工具开发指南](../../../../../docs/tool_development_guide.md)

---

**版本**: v1.0
**更新日期**: 2026-04-20
**维护者**: TrendRadar Team
