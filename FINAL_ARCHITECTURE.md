# 智能股票监控系统 - 最终架构文档

## 🎯 核心理念

**从"订阅接口"到"AI对话系统"**

用户不再需要理解技术细节，只需用自然语言描述需求，系统通过AI理解意图、引导配置、多Agent协作完成监控和分析。

---

## 📐 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                      用户交互层                              │
│  用户输入: "监控000973的全部舆论，关注情绪和看多看空"        │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                    AI意图识别层                              │
│  • 提取实体 (股票代码、时间等)                               │
│  • 识别分析需求 (情绪、看多看空、质量评论等)                 │
│  • 推荐数据源 (东方财富、知乎、微博等)                       │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                    配置引导层                                │
│  • 生成可选配置项                                           │
│  • 引导用户选择分析维度                                      │
│  • 确认监控平台和频率                                        │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                    任务管理层                                │
│  • 创建和存储任务                                           │
│  • 定时调度任务执行                                         │
│  • 管理任务生命周期                                         │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                    爬虫Agent层                               │
│  • 东方财富爬虫 ✅                                           │
│  • 知乎爬虫 (待实现)                                         │
│  • 微博爬虫 (待实现)                                         │
│  • 雪球爬虫 (待实现)                                         │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                    分析Agent层                               │
│  • 情绪分析 (积极/消极/中性)                                 │
│  • 看多看空比例                                              │
│  • 高质量评论识别                                            │
│  • 活跃用户识别                                              │
│  • 热门话题提取                                              │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                    报告生成层                                │
│  • 结构化Markdown报告                                        │
│  • 数据可视化 (图表、统计)                                   │
│  • AI总结和建议                                              │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                    推送层                                    │
│  • Webhook推送 (飞书/钉钉/企业微信)                          │
│  • 微信公众号推送                                            │
│  • 邮件推送                                                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔄 完整工作流程

### 步骤1: 用户输入自然语言

**输入示例**:
```
"我想监控000973这只股票的全部舆论情况，
关注情绪统计、看多看空比例、以及有价值的评论"
```

**API调用**:
```bash
POST /api/v2/create_task
{
  "user_id": "user123",
  "description": "...",
  "webhook_url": "https://...",
  "webhook_type": "feishu"
}
```

---

### 步骤2: AI理解意图并生成配置选项

**AI识别结果**:
```json
{
  "intent": "monitor_stock",
  "entities": {
    "stock_code": "000973"
  },
  "suggested_analysis": [
    "sentiment",      // 情绪统计
    "bull_bear",      // 看多看空
    "quality_posts"   // 有价值的评论
  ],
  "suggested_platforms": [
    "eastmoney"       // 东方财富
  ]
}
```

**生成的配置选项**:
- ✅ 情绪统计 (推荐)
- ✅ 看多看空比例 (推荐)
- ✅ 有价值的评论 (推荐)
- ⬜ 活跃用户分析
- ⬜ 热门话题

**可选平台**:
- ✅ 东方财富股吧 (可用)
- ⬜ 知乎 (未实现)
- ⬜ 微博 (未实现)

---

### 步骤3: 用户确认配置

**用户选择**:
- 分析维度: `[情绪统计, 看多看空, 有价值评论]`
- 平台: `[东方财富]`
- 监控间隔: `300秒` (5分钟)

**API调用**:
```bash
POST /api/v2/configure_task
{
  "task_id": "task_xxx",
  "stock_code": "000973",
  "analysis_types": ["sentiment", "bull_bear", "quality_posts"],
  "platforms": ["eastmoney"],
  "interval": 300
}
```

---

### 步骤4-7: 后台自动执行

#### 4. 爬虫Agent采集数据

```python
# 东方财富爬虫
result = await crawl_eastmoney_stock(
    stock_code="000973",
    max_pages=3,
    enable_comments=True,
    max_comments_per_post=50
)
# 输出: 150条帖子 + 800条评论
```

#### 5. 分析Agent智能分析

**情绪分析**:
```
- 积极: 120条 (35%)
- 消极: 40条 (12%)
- 中性: 180条 (53%)
```

**看多看空**:
```
- 看多: 80条 (65%)
- 看空: 43条 (35%)
- 市场情绪: 看多占优
```

**高质量评论**:
```
发现8条高质量帖子 (5.3%)
1. "一季度业绩预增2664%分析及投资建议"
   特征: 有理论, 有依据, 有结论
   评论: 23 | 阅读: 1500
```

#### 6. 生成结构化报告

生成Markdown格式报告，包含:
- 数据概况
- 情绪统计
- 看多看空分析
- 高质量评论
- AI总结

#### 7. Webhook推送

```bash
POST https://user-webhook-url
{
  "title": "股票 000973 智能监控报告",
  "content": "# 📊 股票 000973 智能监控报告\n\n..."
}
```

---

## 📊 数据库设计

### tasks.db

```sql
CREATE TABLE tasks (
    task_id TEXT PRIMARY KEY,           -- 任务ID
    user_id TEXT NOT NULL,              -- 用户ID
    stock_code TEXT NOT NULL,           -- 股票代码
    description TEXT,                   -- 用户描述
    status TEXT DEFAULT 'pending',      -- 状态
    analysis_types TEXT,                -- 分析类型 (JSON)
    platforms TEXT,                     -- 平台 (JSON)
    webhook_url TEXT,                   -- Webhook URL
    webhook_type TEXT DEFAULT 'generic',-- Webhook类型
    interval INTEGER DEFAULT 300,       -- 监控间隔
    last_report_time TIMESTAMP,         -- 上次报告时间
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### eastmoney_stocks.db

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
);

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
);
```

---

## 🚀 API接口清单

### 1. 创建任务

```
POST /api/v2/create_task
```

输入: 用户描述
输出: 任务ID + AI识别结果 + 配置选项

### 2. 配置任务

```
POST /api/v2/configure_task
```

输入: 任务ID + 用户选择
输出: 任务激活确认

### 3. 查询任务

```
GET /api/v2/task/{task_id}
```

输出: 任务详细信息

### 4. 手动触发

```
POST /api/v2/trigger/{task_id}
```

输出: 立即执行任务

---

## 💡 核心特性

### 1. 自然语言理解

✅ 用户用自然语言描述需求
✅ AI提取关键信息（股票代码、时间、关注点）
✅ 智能推荐分析维度和数据源

### 2. 多Agent协作

✅ **爬虫Agent**: 负责多平台数据采集
✅ **分析Agent**: 负责数据分析和洞察
✅ **配置Agent**: 引导用户完成配置
✅ **报告Agent**: 生成结构化报告

### 3. 智能分析

✅ 情绪分析 (基于关键词)
✅ 看多看空比例
✅ 高质量评论识别
✅ 活跃用户识别
✅ 热门话题提取

### 4. 灵活推送

✅ Webhook推送 (飞书/钉钉/企业微信)
✅ 支持自定义推送格式
✅ 定时自动推送

---

## 🔮 未来扩展

### 短期 (1-2周)

1. **接入真实LLM**
   - 使用GPT/Claude进行意图识别
   - 生成更智能的分析报告

2. **更多平台**
   - 知乎爬虫
   - 微博爬虫
   - 雪球爬虫

3. **更丰富的分析**
   - 情绪趋势图
   - 关键词云图
   - 用户画像分析

### 中期 (1-2月)

1. **AI Agent增强**
   - 使用LLM进行深度分析
   - 自动生成投资建议
   - 风险预警

2. **多股票关联分析**
   - 板块联动分析
   - 行业热度分析

3. **历史数据分析**
   - 趋势分析
   - 预测模型

### 长期 (3-6月)

1. **实时监控**
   - WebSocket实时推送
   - 异常事件告警

2. **用户社区**
   - 用户分享报告
   - 策略市场

3. **API开放平台**
   - 开放API给第三方
   - 插件生态

---

## 📝 部署清单

### 已完成 ✅

- [x] 东方财富爬虫
- [x] 数据存储 (SQLite)
- [x] 基础分析功能
- [x] Webhook推送
- [x] 任务管理系统
- [x] AI意图识别 (简化版)
- [x] 配置引导系统
- [x] 报告生成器

### 待完成 🔨

- [ ] 接入真实LLM
- [ ] 更多平台爬虫
- [ ] 前端界面
- [ ] 用户认证系统
- [ ] 更丰富的分析功能

---

## 🎓 关键代码

### 服务入口

```bash
# 启动智能监控服务
python3 intelligent_monitor_service.py

# 启动Webhook接收器 (测试用)
python3 test_client.py server

# 运行完整测试
python3 test_intelligent_monitor.py
```

### 核心文件

- `intelligent_monitor_service.py` - 主服务
- `trendradar/crawler/eastmoney/` - 东方财富爬虫
- `test_client.py` - 测试客户端
- `test_intelligent_monitor.py` - 完整流程测试

---

**系统已就绪，可以部署到服务器！** 🚀

后续你需要：
1. 部署服务到公网
2. 配置微信公众号后端对接
3. 或直接用飞书群机器人测试

---

**最后更新**: 2026-04-27
**版本**: v2.0
**维护者**: TrendRadar Team
