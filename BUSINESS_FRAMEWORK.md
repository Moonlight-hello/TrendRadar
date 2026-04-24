# TrendRadar - 产品业务框架

> 版本: v1.0 | 更新: 2026-04-23

---

## 1. 产品定位

**AI驱动的自定义信息聚合分析平台，目前主打投资场景，这个场景的用户付费意愿最强烈**

- **核心用户**: 个人投资者、专业交易员
- **核心价值**: 自动抓取股票吧数据和其他社区关于股票的讨论 + AI分析 + 多渠道推送
- **商业模式**: AI中转服务计费（按Token消耗）订阅制会员费用。

---

## 2. 业务架构

```
┌─────────────────────────────────────────────────┐
│           前端 被动接受订阅投递推送。               │
│     公众号 / 小程序 / Web / Telegram Bot        │
└──────────────────┬──────────────────────────────┘
                   │ HTTP REST API
┌──────────────────▼──────────────────────────────┐
│              FastAPI Server                     │
│  /api/subscription   - 提交订阅内容。后端拆解需要哪些内容           │
│  /api/tasks/xxxx  - 接受服务端的推送内容呈现给用户        │
│  /api/results    - 付费和状态查询             │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│         TrendRadar Agent (定时轮询。针对信息密度)             │
│  ├─ CrawlerAgent  - 股票吧/雪球/东财/权威的库存数据库等等/研报调研数据/XXX其他平台可以由前台配置           │
│  ├─ AnalyzerAgent - AI分析 (数据真实性验证，信息真伪验证。上下文维护，用户持续提问以及解答）          │
│  └─ NotifierAgent - Telegram/飞书/微信          │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│              New API 网关                       │
│  http://45.197.145.24:3000/v1                  │
│  Token计费 + 多模型管理                          │
└─────────────────────────────────────────────────┘
```

---

## 3. 核心流程

### 3.1 用户请求流程

```
1. 用户输入关注的内容。比如我关注某只股票的情况或者动态。
   ↓
2. FastAPI 创建任务 (返回 task_id)
   ↓
3. Agent 爬取股票吧和其他平台的关键数据 (异步)，对于数据做一个灵活的处理。是否涉及AI编写脚本呢？？？
   ↓
4. Agent 调用 New API 传递数据并且进行 后端 AI 分析，
   ↓
5. 保存结果到 SQLite
   ↓
6. 将聚合后的有价值的内容整理推送给用户。
```

### 3.2 任务状态机

```
pending → processing → completed
           ↓
         failed
```

---

## 4. 技术栈

### 后端服务

- **FastAPI** - RESTful API
- **SQLite** - 任务队列 + 结果缓存
- **TrendRadar Agent** - 爬虫 + AI分析

### AI分析

- **LiteLLM** - 统一AI接口
- **New API Gateway** - AI中转服务
- **支持模型**: DeepSeek, GPT-4, Claude等

### 推送系统

- **Telegram Bot**
- **飞书/钉钉 Webhook**
- **企业微信**

---

## 5. 数据源

### 5.1 股票社区

- 东方财富股吧
- 雪球
- 淘股吧
- 新浪股吧

### 5.2 新闻资讯

- RSS订阅
- 财经新闻网站

---

## 6. MVP功能

### Phase 1: 基础服务 (1周)

- [X] FastAPI Server骨架
- [ ] 任务队列 (SQLite)
- [ ] 基础CRUD接口
- [ ] 健康检查

### Phase 2: Agent集成 (1周)

- [ ] 股票吧爬虫Agent
- [ ] 配置New API网关
- [ ] AI分析Pipeline
- [ ] 结果存储

### Phase 3: 前端集成 (1周)

- [ ] API文档
- [ ] 测试脚本
- [ ] Telegram Bot (可选)

---

## 7. API设计 (简化版)

### 提交分析任务

```bash
POST /api/analyze
{
  "symbol": "TSLA",          # 股票代码
  "source": "xueqiu",        # 数据源
  "max_posts": 50            # 最多分析帖子数
}

Response:
{
  "task_id": "abc123",
  "status": "pending"
}
```

### 查询任务状态

```bash
GET /api/tasks/abc123

Response:
{
  "task_id": "abc123",
  "status": "completed",
  "progress": 100,
  "result": {
    "summary": "市场情绪积极...",
    "sentiment": "positive",
    "posts_analyzed": 50
  }
}
```

---

## 8. 部署架构

### 服务器环境

- **IP**: 45.197.145.24
- **路径**: /home/project/code/trendradar_server/
- **运行**: `uvicorn main:app --host 0.0.0.0 --port 8000`

### New API 网关

- **地址**: http://45.197.145.24:3000
- **Token**: sk-QlwwecImBL1Yx0p2ji8Awsr0ROuD6HPeimWQIRBtgqYSPnXj

---

## 9. 商业模式

### 收入来源

- **AI调用成本**: 用户消耗的Token按比例分成
- **订阅费用**: 月度/年度会员 (可选)
- **API调用**: 第三方集成按次计费

### 成本结构

- **AI成本**: 按Token计费 (DeepSeek约0.001元/1K tokens)
- **服务器**: 固定成本
- **带宽**: 按流量

---

## 10. 关键文件

### 服务器代码

```
/home/project/code/
├── server/                 # FastAPI服务
│   ├── main.py            # API入口
│   ├── tasks.py           # 任务管理
│   └── db.py              # 数据库
├── config/                # 配置
│   └── config.yaml        # 指向New API
└── agents/                # TrendRadar Agent
```

### 配置示例

```yaml
# config/config.yaml
ai:
  api_base: "http://45.197.145.24:3000/v1"
  api_key: "sk-QlwwecImBL1Yx0p2ji8Awsr0ROuD6HPeimWQIRBtgqYSPnXj"
  model: "deepseek/deepseek-chat"
```

---

## 11. 下一步行动

### 本周任务

1. ✅ 清理项目md文件
2. ✅ 创建FastAPI服务骨架
3. ✅ 实现任务队列 (SQLite)
4. ✅ 配置Agent连接New API
5. ✅ 实现AI分析Agent
6. ✅ 创建定时任务调度器
7. ✅ 完整工作流程测试

### 本月目标

- ✅ MVP服务上线
- ✅ 完成基础API测试
- ✅ Telegram Bot集成
- ⏳ 部署到生产服务器
- ⏳ 真实API对接测试
