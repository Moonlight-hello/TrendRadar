# CommunitySpy 工具集成报告

> **完成日期**: 2026-04-20
> **集成版本**: v1.0

---

## 📋 集成概述

成功将 CommunitySpy 项目（东方财富股吧评论爬虫）封装为 TrendRadar Agent 系统的标准工具，实现了统一的协议接口和多种使用方式。

---

## ✅ 完成的工作

### 1. 核心爬虫封装 ✓

**文件**: `trendradar/agent/tools/data_sources/communityspy/spider.py`

**功能**:
- 提取原项目的核心爬虫类 `EastMoneyCommentSpider`
- 简化接口，保留核心功能
- 支持帖子和评论爬取
- SQLite 数据持久化
- 上下文管理器支持

**核心方法**:
```python
class EastMoneyCommentSpider:
    def __init__(stock_code, db_path)       # 初始化
    def fetch_posts(page, page_size)        # 获取帖子列表
    def fetch_comments(post_id, page)       # 获取评论列表
    def crawl(max_pages, max_posts, ...)    # 执行爬取
    def close()                              # 关闭资源
```

### 2. 工具适配器实现 ✓

**文件**: `trendradar/agent/tools/data_sources/communityspy/tool.py`

**实现的工具**:

#### CommunitySpyTool (爬取工具)
```python
参数:
- stock_code: str (必需)
- max_pages: int = 10
- max_posts: int = 100
- include_comments: bool = True
- delay: float = 1.0
- db_path: Optional[str] = None

返回:
{
    "success": bool,
    "stock_code": str,
    "stats": {
        "posts_count": int,
        "comments_count": int,
        "errors": list
    },
    "db_path": str,
    "message": str
}
```

#### CommunitySpyQueryTool (查询工具)
```python
参数:
- db_path: str (必需)
- query_type: str = "posts"  # posts, comments, stats
- limit: int = 100
- start_date: Optional[str]
- end_date: Optional[str]

返回:
{
    "success": bool,
    "query_type": str,
    "count": int,
    "data": list
}
```

### 3. 命令行工具 ✓

**文件**: `trendradar/agent/tools/data_sources/communityspy/cli.py`

**功能**:
```bash
# 基本用法
python cli.py 301293

# 完整参数
python cli.py 301293 \
    --max-pages 5 \
    --max-posts 50 \
    --delay 2.0 \
    --no-comments \
    --db-path ./data/db.db \
    --output result.json
```

### 4. 完整文档 ✓

创建的文档:
- `README.md` - 工具使用文档
- `COMMUNITYSPY_INTEGRATION.md` - 集成报告（本文档）
- `examples/communityspy_demo.py` - 使用示例

---

## 🏗️ 目录结构

```
TrendRadar/
├── trendradar/
│   └── agent/
│       └── tools/
│           └── data_sources/
│               └── communityspy/          # 新增
│                   ├── __init__.py        ✅ 模块初始化
│                   ├── spider.py          ✅ 核心爬虫
│                   ├── tool.py            ✅ 工具适配器
│                   ├── cli.py             ✅ 命令行工具
│                   └── README.md          ✅ 使用文档
│
├── examples/
│   └── communityspy_demo.py               ✅ 使用示例
│
├── COMMUNITYSPY_INTEGRATION.md            ✅ 集成报告
└── AGENT_SYSTEM_DESIGN.md                 ✓ Agent 设计文档
```

---

## 🎯 统一工具协议

### 协议接口

CommunitySpy 遵循 TrendRadar Agent 系统的统一工具协议：

```python
class BaseTool(ABC):
    """工具基类"""

    # 元数据
    name: str                    # 工具名称
    description: str             # 工具描述
    category: str                # 工具类别
    parameters: Dict             # 参数定义

    # 核心方法
    def execute(self, **kwargs) -> Dict:
        """执行工具，返回标准化结果"""
        pass

    def validate_params(self, **kwargs) -> bool:
        """验证参数"""
        pass

    def get_metadata(self) -> Dict:
        """获取工具元数据"""
        pass
```

### 标准返回格式

所有工具必须返回以下格式的字典：

```python
{
    "success": bool,      # 是否成功 (必需)
    "data": Any,          # 数据结果 (可选)
    "error": str,         # 错误信息 (失败时必需)
    "message": str,       # 提示信息 (可选)
    "metadata": Dict      # 元数据 (可选)
}
```

### 参数定义格式

```python
parameters = {
    "param_name": {
        "type": "string",         # 类型: string, integer, boolean, array, object, number
        "description": "描述",
        "required": True/False,   # 是否必需
        "default": value          # 默认值 (可选)
    }
}
```

---

## 🚀 使用方式

### 方式 1: Agent 系统集成（推荐）

```python
from trendradar.agent import AgentHarness, Task
from trendradar.agent.agents import CrawlerAgent
from trendradar.agent.tools.data_sources.communityspy import CommunitySpyTool

# 初始化
harness = AgentHarness()
harness.register_tool(CommunitySpyTool(), "data_source")
harness.register_agent("crawler", CrawlerAgent)

# 执行任务
task = Task(
    type="collect_data",
    params={
        "data_sources": [{
            "type": "communityspy",
            "stock_code": "301293"
        }]
    }
)

result = harness.run(task, "crawler")
```

### 方式 2: 直接使用工具

```python
from trendradar.agent.tools.data_sources.communityspy import CommunitySpyTool

tool = CommunitySpyTool()
result = tool.execute(
    stock_code="301293",
    max_posts=100
)
```

### 方式 3: 使用爬虫类

```python
from trendradar.agent.tools.data_sources.communityspy import EastMoneyCommentSpider

with EastMoneyCommentSpider("301293") as spider:
    stats = spider.crawl(max_posts=100)
```

### 方式 4: 命令行工具

```bash
cd /path/to/TrendRadar/trendradar/agent/tools/data_sources/communityspy
python cli.py 301293 --max-posts 100
```

---

## 📊 数据结构

### 数据库表结构

#### posts 表
```sql
CREATE TABLE posts (
    id INTEGER PRIMARY KEY,
    post_id TEXT UNIQUE,
    stock_code TEXT,
    title TEXT,
    content TEXT,
    publish_time TIMESTAMP,
    user_id TEXT,
    user_nickname TEXT,
    click_count INTEGER,
    comment_count INTEGER,
    like_count INTEGER,
    created_at TIMESTAMP
)
```

#### comments 表
```sql
CREATE TABLE comments (
    id INTEGER PRIMARY KEY,
    comment_id TEXT UNIQUE,
    post_id TEXT,
    content TEXT,
    publish_time TIMESTAMP,
    user_id TEXT,
    user_nickname TEXT,
    like_count INTEGER,
    created_at TIMESTAMP
)
```

---

## 🔄 与原项目的关系

### 原项目结构

```
/Users/wangxinlong/Code/communityspy/
├── communityspy.py              # 原始爬虫（34KB）
├── communityspy_new.py          # 新版爬虫（51KB）
├── db_tool.py                   # 数据库工具
├── analyze_timeline.py          # 时间线分析
├── knowledge_distiller.py       # 知识蒸馏
└── ...
```

### 集成策略

**提取的内容**:
- ✅ 核心爬虫类 → `spider.py`
- ✅ 数据库表结构
- ✅ API 接口调用逻辑

**保留在原项目**:
- ❌ 数据分析功能 (`analyze_timeline.py`)
- ❌ 知识蒸馏功能 (`knowledge_distiller.py`)
- ❌ SQL 生成器 (`sql_generator.py`)
- ❌ 其他高级功能

**原因**:
- 爬虫功能适合集成到 TrendRadar
- 分析功能独立性强，保持原项目独立使用
- 可以从 TrendRadar 导出数据，再用原项目分析

---

## 🎨 设计亮点

### 1. 统一协议

所有工具遵循相同的接口规范，易于:
- Agent 调用
- 工具组合
- 系统扩展

### 2. 多种使用方式

提供 4 种使用方式，满足不同场景:
- Agent 系统：自动化工作流
- 工具类：灵活调用
- 爬虫类：精细控制
- 命令行：快速测试

### 3. 数据持久化

SQLite 数据库自动管理:
- 自动创建表结构
- 增量数据更新
- 支持查询导出

### 4. 完整文档

提供详细文档:
- 使用说明
- API 参考
- 示例代码
- 最佳实践

---

## ⚠️ 注意事项

### 1. 请求频率

```python
# 建议设置合理的延迟
delay = 1.0  # 建议 1-2 秒
```

### 2. Cookie 更新

某些接口可能需要登录 Cookie，如遇到 403 错误：

```python
# 在 spider.py 中更新 Cookie
self.cookie = "your_new_cookie"
```

### 3. 数据量控制

首次爬取建议小数据量测试：

```python
# 测试配置
max_pages = 1
max_posts = 10
```

### 4. 存储空间

SQLite 数据库会占用磁盘空间：
- 1000 条帖子 + 5000 条评论 ≈ 10-20 MB
- 定期清理旧数据

---

## 📈 后续扩展

### 短期计划

- [ ] 支持更多查询条件（关键词搜索、用户过滤）
- [ ] 实现数据导出功能（CSV、JSON）
- [ ] 添加爬取进度回调
- [ ] 支持断点续爬

### 中期计划

- [ ] 集成情感分析工具
- [ ] 支持实时监控模式
- [ ] Web 界面管理
- [ ] 数据可视化

### 长期计划

- [ ] 支持更多社区平台（雪球、淘股吧）
- [ ] AI 驱动的内容分析
- [ ] 异常检测和预警
- [ ] 分布式爬取

---

## 🔗 相关资源

### 内部文档

- [Agent 系统设计](AGENT_SYSTEM_DESIGN.md)
- [Agent 系统实施总结](IMPLEMENTATION_SUMMARY.md)
- [CommunitySpy 工具文档](trendradar/agent/tools/data_sources/communityspy/README.md)

### 原项目文档

- [原项目路径](/Users/wangxinlong/Code/communityspy)
- [分析工具说明](/Users/wangxinlong/Code/communityspy/ANALYSIS_README.md)
- [知识管道说明](/Users/wangxinlong/Code/communityspy/KNOWLEDGE_PIPELINE_README.md)

### 使用示例

- [CommunitySpy 演示](examples/communityspy_demo.py)
- [Agent 系统演示](examples/agent_system_demo.py)

---

## 📝 总结

### 核心成果

1. **成功封装** ✅
   - 核心爬虫功能完整提取
   - 符合统一工具协议
   - 多种使用方式

2. **良好设计** ✅
   - 清晰的接口定义
   - 标准的返回格式
   - 完善的文档

3. **易于扩展** ✅
   - 模块化结构
   - 可插拔设计
   - 协议统一

### 价值体现

- **复用性**: 原项目功能可在 TrendRadar 中复用
- **标准化**: 统一工具协议便于系统扩展
- **灵活性**: 多种使用方式满足不同需求
- **可维护**: 清晰的代码结构和完整文档

### 下一步

1. 测试工具在实际场景中的表现
2. 根据反馈优化接口和功能
3. 实现更多数据源工具
4. 完善 Agent 协作机制

---

**完成日期**: 2026-04-20
**版本**: v1.0
**状态**: ✅ 已完成

---

## 🙏 致谢

感谢原 CommunitySpy 项目提供的优秀爬虫实现。
感谢 TrendRadar Agent 系统提供的标准化框架。
