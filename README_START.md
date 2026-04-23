# 🚀 TrendRadar 启动指南

> **快速导航**: 本地运行 → 服务器部署 → 功能扩展

---

## 📖 项目概述

TrendRadar 是一个基于 Agent 架构的智能信息监控平台，集成了：
- ✅ 热榜新闻爬虫
- ✅ RSS 订阅
- ✅ 东方财富股吧爬虫（CommunitySpy）
- ✅ AI 智能分析
- ✅ 多渠道通知推送
- ✅ 模块化 Agent 系统

---

## 🎯 现在开始

### Option 1: 本地快速测试（5分钟）

```bash
# 1. 进入项目目录
cd /Users/wangxinlong/Code/TrendRadar

# 2. 激活虚拟环境
source .venv/bin/activate

# 3. 运行快速测试
python3 test_local.py

# 4. 如果测试通过，运行演示
python3 examples/communityspy_demo.py
```

**详细指南**: 查看 [本地快速启动指南](QUICKSTART_LOCAL.md)

### Option 2: 测试 CommunitySpy 工具

```bash
# 进入工具目录
cd trendradar/agent/tools/data_sources/communityspy

# 爬取少量数据测试
python3 cli.py 301293 --max-posts 5 --no-comments

# 查看结果
ls -lh eastmoney_301293.db
sqlite3 eastmoney_301293.db "SELECT COUNT(*) FROM posts;"
```

### Option 3: 测试原有 TrendRadar 功能

```bash
# 回到项目根目录
cd /Users/wangxinlong/Code/TrendRadar

# 运行一次
python3 -m trendradar

# 查看帮助
python3 -m trendradar --help
```

---

## 📚 核心文档

### 快速上手
- **[本地快速启动](QUICKSTART_LOCAL.md)** ⭐ 推荐先看这个
- **[测试脚本说明](#测试脚本说明)** - test_local.py 的使用

### 功能文档
- **[Agent 系统设计](AGENT_SYSTEM_DESIGN.md)** - 完整架构设计
- **[CommunitySpy 工具](trendradar/agent/tools/data_sources/communityspy/README.md)** - 股吧爬虫
- **[技术方案详细文档](技术方案详细文档.md)** - TrendRadar 原有架构

### 部署和运维
- **[服务器部署指南](DEPLOYMENT_GUIDE.md)** ⭐ 申请服务器后看这个
- **[实施总结](IMPLEMENTATION_SUMMARY.md)** - 第一阶段总结
- **[集成报告](COMMUNITYSPY_INTEGRATION.md)** - CommunitySpy 集成

### 示例代码
- `examples/agent_system_demo.py` - Agent 系统演示
- `examples/communityspy_demo.py` - CommunitySpy 演示
- `test_local.py` - 本地测试脚本

---

## 🔍 测试脚本说明

### test_local.py - 本地测试

这个脚本会自动测试 4 个核心功能：

```bash
python3 test_local.py
```

**测试内容**:
1. ✅ 模块导入 - 检查所有模块是否正确安装
2. ✅ 工具注册 - 测试 AgentHarness 和工具注册
3. ✅ 上下文管理 - 测试 Context 数据传递
4. ✅ CommunitySpy - 测试股吧爬虫基本功能

**预期输出**:
```
============================================================
TrendRadar 本地测试
============================================================

============================================================
测试 1: 模块导入
============================================================
✅ AgentHarness 导入成功
✅ Agents 导入成功
✅ BaseTool 导入成功
✅ CommunitySpy 导入成功

✅ 所有模块导入成功！

...

============================================================
测试总结
============================================================
模块导入: ✅ 通过
工具注册: ✅ 通过
上下文管理: ✅ 通过
CommunitySpy: ✅ 通过

============================================================
🎉 所有测试通过！系统运行正常！
...
============================================================
```

---

## 🛠️ 项目结构

```
TrendRadar/
├── trendradar/                    # 核心代码
│   ├── agent/                     # Agent 系统
│   │   ├── agents/                # Agent 实现
│   │   │   ├── crawler.py         # 爬虫 Agent
│   │   │   └── analyzer.py        # 分析 Agent
│   │   └── tools/                 # 工具生态
│   │       ├── data_sources/      # 数据源工具
│   │       │   ├── hot_news_scraper.py
│   │       │   ├── rss_fetcher.py
│   │       │   └── communityspy/  # 股吧爬虫 ⭐
│   │       └── ...
│   ├── core/                      # 核心业务
│   ├── crawler/                   # 爬虫模块
│   ├── ai/                        # AI 模块
│   └── ...
│
├── config/                        # 配置文件
│   └── config.yaml
│
├── examples/                      # 示例代码
│   ├── agent_system_demo.py
│   └── communityspy_demo.py
│
├── docs/                          # 文档目录
│   ├── QUICKSTART_LOCAL.md        # 本地启动 ⭐
│   ├── DEPLOYMENT_GUIDE.md        # 部署指南 ⭐
│   ├── AGENT_SYSTEM_DESIGN.md     # 系统设计
│   └── ...
│
├── test_local.py                  # 测试脚本 ⭐
├── requirements.txt               # 依赖列表
└── README_START.md                # 本文档
```

---

## 💡 常见任务

### 任务 1: 测试系统功能

```bash
# 运行完整测试
python3 test_local.py

# 如果测试失败，检查依赖
pip install -r requirements.txt
```

### 任务 2: 爬取股吧数据

```bash
# 方式 A: 使用 CLI 工具（简单）
cd trendradar/agent/tools/data_sources/communityspy
python3 cli.py 301293 --max-posts 100

# 方式 B: 使用 Python 代码（灵活）
from trendradar.agent.tools.data_sources.communityspy import CommunitySpyTool
tool = CommunitySpyTool()
result = tool.execute(stock_code="301293", max_posts=100)
```

### 任务 3: 查看爬取的数据

```bash
# 打开数据库
sqlite3 eastmoney_301293.db

# 查看表结构
.schema posts

# 统计数据
SELECT COUNT(*) FROM posts;
SELECT COUNT(*) FROM comments;

# 查看最新帖子
SELECT title, publish_time FROM posts
ORDER BY publish_time DESC
LIMIT 10;

# 退出
.quit
```

### 任务 4: 配置定时爬取

```bash
# 编辑 crontab
crontab -e

# 添加定时任务（每小时爬取一次）
0 * * * * cd /path/to/TrendRadar && /path/to/.venv/bin/python3 trendradar/agent/tools/data_sources/communityspy/cli.py 301293 --max-posts 100
```

---

## 🔄 下一步计划

### ✅ 已完成
- [x] Agent 系统架构设计
- [x] CommunitySpy 工具集成
- [x] 统一工具协议
- [x] 本地测试脚本
- [x] 使用文档
- [x] 部署指南

### 🎯 本地测试（现在）
1. 运行 `test_local.py` 验证系统
2. 测试 CommunitySpy 爬取功能
3. 查看数据是否正常存储
4. 熟悉各种使用方式

### 🚀 服务器部署（申请服务器后）
1. 参考 [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
2. 选择部署方式：传统 / Docker / Supervisor
3. 配置定时任务
4. 设置监控和告警

### 🔮 功能扩展（可选）
- [ ] 集成更多数据源（雪球、淘股吧）
- [ ] 添加数据分析功能
- [ ] 接入 AI 分析
- [ ] 配置通知推送
- [ ] Web 管理界面

---

## 📞 获取帮助

### 遇到问题？

1. **查看日志**
   ```bash
   # 如果有日志文件
   tail -f logs/trendradar.log
   ```

2. **检查文档**
   - [本地快速启动](QUICKSTART_LOCAL.md) - 常见问题解答
   - [部署指南](DEPLOYMENT_GUIDE.md) - 故障排查

3. **运行诊断**
   ```bash
   python3 test_local.py  # 运行测试脚本
   ```

### 核心命令速查

```bash
# 测试
python3 test_local.py                      # 完整测试
python3 examples/communityspy_demo.py      # 演示脚本

# CommunitySpy
cd trendradar/agent/tools/data_sources/communityspy
python3 cli.py 301293 --max-posts 10       # 爬取数据

# 数据库
sqlite3 eastmoney_301293.db                # 打开数据库
.tables                                    # 查看表
SELECT COUNT(*) FROM posts;                # 统计

# 原有功能
python3 -m trendradar                      # 运行 TrendRadar
python3 -m trendradar --help               # 查看帮助
```

---

## 🎉 开始使用

现在你可以：

1. **立即测试**:
   ```bash
   python3 test_local.py
   ```

2. **查看详细指南**:
   - 打开 [QUICKSTART_LOCAL.md](QUICKSTART_LOCAL.md)

3. **准备部署**:
   - 阅读 [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

**祝你使用愉快！** 🚀

---

**文档版本**: v1.0
**最后更新**: 2026-04-20
**维护**: TrendRadar Team
