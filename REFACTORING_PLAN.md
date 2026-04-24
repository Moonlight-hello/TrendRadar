# TrendRadar 项目重构方案

> 解决架构混乱、代码重复、爬虫不可用等问题

---

## 🔍 问题分析

### 1. 项目结构混乱

**当前结构**：
```
TrendRadar/
├── trendradar/          # 原有项目（完整架构）
│   ├── agent/          # Agent系统
│   ├── crawler/        # RSS爬虫
│   ├── notification/   # 通知系统
│   ├── core/          # 核心模块
│   └── storage/       # 存储层
└── trendradar_server/  # 新建的服务（重复实现）❌
    ├── core/          # 重复的核心模块
    ├── user/          # 用户管理
    └── main.py        # FastAPI入口
```

**问题**：
- ❌ 两套独立的系统，功能重复
- ❌ `trendradar_server` 没有复用原有代码
- ❌ 架构不统一，维护困难

### 2. 代码重复

**重复的模块**：
1. **UserManager**
   - `trendradar_server/core/user_manager.py` (完整版)
   - `trendradar_server/user/manager.py` (简化版 MinimalUserManager)
   - ❌ 两个类功能相同，接口不统一

2. **数据库Schema**
   - `schema.sql` (完整版)
   - `schema_minimal.sql` (简化版)
   - `schema_simple.sql` (极简版)
   - ❌ 三个版本造成混乱

3. **Scheduler调度器**
   - `trendradar/core/scheduler.py` (原有)
   - `trendradar_server/core/scheduler.py` (新建)
   - ❌ 功能重复

### 3. 爬虫问题

**当前实现**：
```python
# trendradar_server/core/crawler_agent.py
sys.path.append('/Users/wangxinlong/Code/communityspy')  # ❌ 硬编码路径
from communityspy_new import EastMoneyCommentSpider
```

**问题**：
- ❌ 依赖外部项目 communityspy，路径硬编码
- ❌ 导入失败时使用Mock数据，用户无感知
- ❌ 没有检查爬虫是否真正可用

**原有实现**：
```python
# trendradar/crawler/fetcher.py
# 使用 NewsNow API 抓取数据
api_url = "https://newsnow.busiyi.world/api/s"
```
- ✅ 使用稳定的API服务
- ✅ 支持多平台（热榜聚合）

---

## 🎯 重构目标

### 1. 统一项目架构

**新结构**：
```
TrendRadar/
├── trendradar/              # 核心库（保留原有）
│   ├── agent/              # Agent系统
│   ├── crawler/            # 爬虫模块
│   ├── notification/       # 通知系统
│   ├── core/              # 核心模块
│   ├── storage/           # 存储层
│   └── server/            # ← 新增：Web服务层
│       ├── api/           # FastAPI路由
│       ├── models/        # Pydantic模型
│       ├── services/      # 业务逻辑
│       └── main.py        # 服务入口
├── user_system/           # ← 独立：用户管理系统
│   ├── manager.py         # 统一的UserManager
│   ├── telegram_bot.py    # Telegram Bot
│   ├── push_service.py    # 推送服务
│   └── schema.sql         # 统一的数据库Schema
└── tests/                 # 测试（顶层）
    ├── test_crawler.py
    ├── test_analyzer.py
    └── test_server.py
```

### 2. 代码整合原则

1. **单一数据源**：删除重复的爬虫实现，统一使用原有的 `DataFetcher`
2. **统一用户管理**：合并 `UserManager` 和 `MinimalUserManager`
3. **统一Schema**：只保留一个完整的 `schema.sql`
4. **复用调度器**：扩展原有 `scheduler.py`，而非重写

### 3. 爬虫修复

**方案A：使用原有API** (推荐)
```python
# 复用 trendradar/crawler/fetcher.py
from trendradar.crawler.fetcher import DataFetcher

fetcher = DataFetcher()
data = fetcher.fetch_data(source="weibo", limit=50)
```

**方案B：集成communityspy** (备选)
```python
# 正确的集成方式
try:
    from communityspy_new import EastMoneyCommentSpider
except ImportError:
    logger.warning("CommunitySpy not installed, using API fallback")
    # 回退到API方式
```

---

## 📝 重构步骤

### Phase 1: 清理重复代码 (1小时)

1. **删除重复目录**
   ```bash
   rm -rf trendradar_server/
   ```

2. **创建新的服务层**
   ```bash
   mkdir -p trendradar/server/{api,models,services}
   ```

3. **迁移用户系统**
   ```bash
   mv trendradar_server/user/ user_system/
   # 合并 UserManager
   ```

### Phase 2: 重构服务层 (2小时)

1. **FastAPI服务**
   - 移动 `main.py` → `trendradar/server/main.py`
   - 重构路由 → `trendradar/server/api/`
   - 复用原有模块

2. **统一调度器**
   - 扩展 `trendradar/core/scheduler.py`
   - 集成用户管理
   - 添加任务队列

3. **爬虫统一**
   - 使用 `trendradar/crawler/fetcher.py`
   - 添加东方财富支持（如需要）
   - 删除Mock实现

### Phase 3: 测试和文档 (1小时)

1. **测试覆盖**
   - 移动测试到顶层 `tests/`
   - 修复导入路径
   - 运行完整测试

2. **更新文档**
   - 统一 README
   - 更新启动指南
   - 添加架构图

---

## 🚀 执行计划

### 立即执行

1. ✅ 创建此重构方案文档
2. ⏳ 备份当前代码
3. ⏳ 执行 Phase 1
4. ⏳ 执行 Phase 2
5. ⏳ 执行 Phase 3

### 风险控制

- 在新分支进行重构
- 保留原有功能不变
- 逐步测试验证

---

## 📊 预期成果

### 代码质量

- ✅ 消除重复代码 (预计减少 40% 代码量)
- ✅ 统一架构风格
- ✅ 提高可维护性

### 功能完整性

- ✅ 爬虫真正可用
- ✅ 用户系统清晰
- ✅ API服务稳定

### 开发效率

- ✅ 新功能开发更快
- ✅ Bug修复更容易
- ✅ 团队协作更顺畅
