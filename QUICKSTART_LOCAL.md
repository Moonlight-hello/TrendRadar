# TrendRadar 本地快速启动指南

> **最后更新**: 2026-04-20

---

## 🚀 快速开始（5分钟）

### Step 1: 环境准备

```bash
# 进入项目目录
cd /Users/wangxinlong/Code/TrendRadar

# 检查 Python 版本（需要 Python 3.10+）
python3 --version

# 如果没有虚拟环境，创建一个
python3 -m venv .venv

# 激活虚拟环境
source .venv/bin/activate  # macOS/Linux
# 或
.venv\Scripts\activate     # Windows
```

### Step 2: 安装依赖

```bash
# 安装项目依赖
pip install -r requirements.txt

# 如果需要 CommunitySpy 功能，额外安装
pip install requests
```

### Step 3: 快速测试

#### 测试 1: 热榜爬虫工具

```bash
# 运行热榜爬虫演示
python examples/agent_system_demo.py
```

#### 测试 2: CommunitySpy 工具

```bash
# 测试股吧爬虫（会爬取少量数据）
cd trendradar/agent/tools/data_sources/communityspy
python3 cli.py 301293 --max-posts 5 --no-comments

# 查看结果
ls -lh eastmoney_301293.db
```

#### 测试 3: Agent 系统完整演示

```bash
# 回到项目根目录
cd /Users/wangxinlong/Code/TrendRadar

# 运行完整演示
python3 examples/communityspy_demo.py
```

---

## 📖 详细说明

### 1. 测试 CommunitySpy 工具

创建测试脚本：

```python
# test_communityspy.py
from trendradar.agent.tools.data_sources.communityspy import CommunitySpyTool

# 创建工具
tool = CommunitySpyTool()

# 执行爬取（少量数据测试）
result = tool.execute(
    stock_code="301293",
    max_pages=1,
    max_posts=5,
    include_comments=False,
    delay=1.0
)

print(f"成功: {result['success']}")
print(f"统计: {result['stats']}")
print(f"数据库: {result['db_path']}")
```

运行：
```bash
python3 test_communityspy.py
```

### 2. 测试原有 TrendRadar 功能

```bash
# 测试热榜爬取
python3 -m trendradar

# 查看帮助
python3 -m trendradar --help
```

### 3. 测试 Agent 系统

```python
# test_agent.py
from trendradar.agent import AgentHarness
from trendradar.agent.tools.data_sources import HotNewsScraperTool

# 初始化
harness = AgentHarness()
harness.register_tool(HotNewsScraperTool(), "data_source")

# 查看已注册的工具
tools = harness.tool_registry.list_tools()
print(f"已注册的工具: {tools}")
```

---

## 🔧 常见问题

### Q1: 找不到模块

```bash
# 确保在项目根目录
cd /Users/wangxinlong/Code/TrendRadar

# 确认虚拟环境已激活
which python3
# 应该显示: /Users/wangxinlong/Code/TrendRadar/.venv/bin/python3

# 重新安装依赖
pip install -r requirements.txt
```

### Q2: 导入错误

```python
# 添加项目路径到 sys.path
import sys
from pathlib import Path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
```

### Q3: CommunitySpy 爬取失败

可能原因：
1. 网络连接问题
2. Cookie 过期（需要更新 spider.py 中的 cookie）
3. API 接口变更

解决方案：
```python
# 在 spider.py 中更新 Cookie
# 从浏览器开发者工具复制最新的 Cookie
```

---

## 📊 验证成功

运行成功后，你应该看到：

### CommunitySpy 工具
```bash
✅ eastmoney_301293.db 文件已创建
✅ 数据库包含 posts 和 comments 表
✅ 爬取统计信息正常输出
```

### Agent 系统
```bash
✅ 工具注册成功
✅ Agent 初始化成功
✅ 上下文管理正常
```

### TrendRadar 原有功能
```bash
✅ 配置加载正常
✅ 热榜数据爬取成功
✅ 存储功能正常
```

---

## 🎯 下一步

本地测试成功后，你可以：

1. **申请服务器资源**
   - 查看 [服务器部署方案](DEPLOYMENT_GUIDE.md)
   - 推荐配置：2核4G，50G 磁盘

2. **配置定时任务**
   - 设置 cron job 定时爬取
   - 配置数据清理策略

3. **集成更多功能**
   - 添加数据分析
   - 接入通知推送
   - 配置 AI 分析

---

## 📝 快速命令参考

```bash
# 环境管理
source .venv/bin/activate              # 激活虚拟环境
deactivate                             # 退出虚拟环境

# 运行测试
python3 examples/agent_system_demo.py  # Agent 系统演示
python3 examples/communityspy_demo.py  # CommunitySpy 演示

# CommunitySpy CLI
cd trendradar/agent/tools/data_sources/communityspy
python3 cli.py 301293 --max-posts 10   # 爬取 10 条帖子

# 原有 TrendRadar
python3 -m trendradar                  # 运行一次
python3 -m trendradar --help           # 查看帮助

# 数据库查看
sqlite3 eastmoney_301293.db            # 打开数据库
.tables                                # 查看表
SELECT COUNT(*) FROM posts;            # 统计帖子数
.quit                                  # 退出
```

---

## 🆘 获取帮助

遇到问题？

1. 查看日志输出
2. 检查文档：
   - [Agent 系统设计](AGENT_SYSTEM_DESIGN.md)
   - [CommunitySpy 文档](trendradar/agent/tools/data_sources/communityspy/README.md)
3. 查看示例代码
4. 提交 Issue

---

**祝你运行顺利！🎉**
