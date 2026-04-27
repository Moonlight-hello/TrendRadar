# 🎯 智能股票监控系统 - 演示文档

## ✅ 系统已部署成功

当前系统状态：
- ✅ 智能监控服务运行中 (端口 8000)
- ✅ Webhook接收器运行中 (端口 9000)
- ✅ 自动监控循环已启动
- ✅ 已成功采集和分析股票000973的舆论数据

## 📊 实际运行数据

### 最新监控报告 (2026-04-27 15:46:57)

**股票代码**: 000973

**数据采集**:
- 东方财富股吧: 208帖 + 267评

**智能分析结果**:
- **情绪统计**: 积极19.33% / 消极4.41% / 中性76.26%
- **看多看空**: 看多76.53% / 看空23.47% → **看多占优**
- **高质量评论**: 发现1条 (0.48%)

**高质量帖子示例**:
> 锂电隔膜+超薄隔膜+业绩暴增+广东国资1、公司预计2026年一季度归母净利润5...
> - 作者: 关注牛股最新消息
> - 特征: 有依据, 有结论
> - 互动: 5评论 / 1002阅读

## 🚀 快速测试订阅功能

### 测试1: 使用Python脚本订阅

```bash
python3 simple_client_test.py
```

**预期结果**:
- 创建新的监控任务
- 自动采集000973股票数据
- 30-60秒后收到分析报告
- 系统每10分钟自动推送更新

### 测试2: 使用curl订阅

```bash
# 步骤1: 创建任务
TASK_ID=$(curl -X POST "http://localhost:8000/api/v2/create_task" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "demo_user",
    "description": "监控000973股票的情绪和看多看空比例",
    "webhook_url": "http://localhost:9000/webhook/generic"
  }' | python3 -c "import sys,json; print(json.load(sys.stdin)['task_id'])")

echo "任务ID: $TASK_ID"

# 步骤2: 配置任务
curl -X POST "http://localhost:8000/api/v2/configure_task" \
  -H "Content-Type: application/json" \
  -d "{
    \"task_id\": \"$TASK_ID\",
    \"stock_code\": \"000973\",
    \"analysis_types\": [\"sentiment\", \"bull_bear\", \"quality_posts\"],
    \"platforms\": [\"eastmoney\"],
    \"interval_minutes\": 10
  }"

echo "✅ 订阅成功！系统将每10分钟推送分析报告"
echo "查看报告: http://localhost:9000/messages"
```

### 测试3: 查看所有推送的报告

```bash
# 查看最新3条报告
curl -s http://localhost:9000/messages | python3 << 'EOF'
import json, sys
msgs = json.load(sys.stdin)
if isinstance(msgs, dict) and 'messages' in msgs:
    msgs = msgs['messages']

print(f"📬 共收到 {len(msgs)} 条推送\n")
for msg in msgs[-3:]:  # 最新3条
    print("="*60)
    if 'data' in msg:
        print(msg['data'].get('content', ''))
    print(f"\n推送时间: {msg.get('time', 'N/A')}\n")
EOF
```

## 🎮 完整工作流演示

### 场景: 用户订阅股票舆论监控

**步骤1️⃣ : 用户输入自然语言**
```
"我想监控000973这只股票的舆论信息，关注情绪统计、看多看空比例和有价值的评论"
```

**步骤2️⃣ : AI理解意图**
```json
{
  "intent": "monitor_stock",
  "entities": {
    "stock_code": "000973"
  },
  "suggested_analysis": [
    "sentiment",      // 情绪统计
    "bull_bear",      // 看多看空
    "quality_posts"   // 有价值评论
  ],
  "suggested_platforms": [
    "eastmoney"       // 东方财富股吧
  ]
}
```

**步骤3️⃣ : 用户确认配置**
```
✅ 股票: 000973
✅ 分析: 情绪统计 + 看多看空 + 有价值评论
✅ 平台: 东方财富
✅ 频率: 每10分钟
```

**步骤4️⃣ : 爬虫Agent采集数据**
```
🕷️  爬虫Agent开始采集...
  ✅ eastmoney: 208帖 + 267评
```

**步骤5️⃣ : 分析Agent智能分析**
```
🔍 分析Agent开始分析...
  ✅ 完成 3 项分析
    - 情绪统计: 积极19.33% / 消极4.41% / 中性76.26%
    - 看多看空: 看多76.53% / 看空23.47%
    - 高质量帖子: 发现1条
```

**步骤6️⃣ : 生成结构化报告**
```markdown
# 📊 股票 000973 智能监控报告

**生成时间**: 2026-04-27 15:46:57

## 📈 数据概况
- 东方财富: 208帖 + 267评

## 🔍 智能分析
### 😊 情绪统计
- 积极: 19.33%
- 消极: 4.41%
- 中性: 76.26%

### 📊 看多看空
- 看多: 76.53%
- 看空: 23.47%
- **结论**: 看多占优

### ⭐ 有价值的评论
发现 1 条高质量帖子...
```

**步骤7️⃣ : Webhook推送给用户**
```
📬 推送报告...
  ✅ 推送成功
```

## 📋 系统特性演示

### 特性1: 多维度智能分析

系统支持5种分析维度：

1. **情绪统计** - 分析讨论区整体情绪（积极/消极/中性）
2. **看多看空比例** - 统计看多和看空的声音占比
3. **有价值的评论** - 筛选有理论、有依据、有结论的高质量分析
4. **活跃用户分析** - 识别频繁发帖的用户，警惕可能的水军
5. **热门话题** - 提取讨论最多的话题和关键词

### 特性2: 自然语言交互

用户无需了解技术细节，用自然语言描述需求：
- ✅ "我想监控000973的舆论"
- ✅ "帮我关注茅台股票的看多看空情况"
- ✅ "追踪比亚迪的讨论热度和情绪变化"

AI自动理解意图并生成配置建议。

### 特性3: 自动定时监控

配置一次，持续监控：
- 用户设定监控频率（如每10分钟）
- 系统自动采集、分析、推送
- 无需手动触发，全自动运行

### 特性4: 多平台支持（规划中）

当前支持:
- ✅ 东方财富股吧

即将支持:
- 🔜 知乎
- 🔜 微博
- 🔜 雪球

### 特性5: 灵活的推送方式

支持多种Webhook格式：
- ✅ 飞书机器人
- ✅ 钉钉机器人
- ✅ 企业微信
- ✅ 通用Webhook (JSON)

## 🔍 实时监控展示

### 查看当前活跃任务

```bash
# 查询数据库中的所有活跃任务
sqlite3 tasks.db << 'EOF'
.headers on
.mode column
SELECT
  task_id,
  stock_code,
  status,
  datetime(created_at, 'localtime') as created_at,
  datetime(last_report_time, 'localtime') as last_report
FROM tasks
WHERE status = 'active'
ORDER BY created_at DESC
LIMIT 10;
EOF
```

### 实时查看系统日志

```bash
# 终端1: 查看智能监控服务日志
tail -f logs/intelligent_service.log

# 终端2: 查看Webhook接收日志
tail -f logs/webhook_receiver.log
```

### 监控系统性能

```bash
# 查看任务执行统计
sqlite3 tasks.db << 'EOF'
SELECT
  status,
  COUNT(*) as count
FROM tasks
GROUP BY status;
EOF

# 查看最近10次报告生成时间
sqlite3 tasks.db << 'EOF'
SELECT
  task_id,
  stock_code,
  datetime(last_report_time, 'localtime') as report_time
FROM tasks
WHERE last_report_time IS NOT NULL
ORDER BY last_report_time DESC
LIMIT 10;
EOF
```

## 🎨 可视化展示

### API文档界面

访问 http://localhost:8000/docs 查看完整的API文档（Swagger UI）

包含：
- API endpoint列表
- 请求/响应示例
- 在线测试功能

### Webhook消息查看

访问 http://localhost:9000/messages 查看所有推送的报告

返回JSON格式的所有消息列表。

## 📚 代码示例

### Python客户端示例

```python
import requests

# 创建监控任务
response = requests.post(
    "http://localhost:8000/api/v2/create_task",
    json={
        "user_id": "my_user_id",
        "description": "监控000973股票的情绪和看多看空",
        "webhook_url": "https://my-webhook-url.com"
    }
)

task_id = response.json()['task_id']
stock_code = response.json()['intent']['entities']['stock_code']

# 配置任务
requests.post(
    "http://localhost:8000/api/v2/configure_task",
    json={
        "task_id": task_id,
        "stock_code": stock_code,
        "analysis_types": ["sentiment", "bull_bear"],
        "platforms": ["eastmoney"],
        "interval_minutes": 15
    }
)

print(f"✅ 成功订阅股票{stock_code}的监控")
```

### JavaScript客户端示例

```javascript
// 创建监控任务
const createTask = async () => {
  const response = await fetch('http://localhost:8000/api/v2/create_task', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      user_id: 'my_user_id',
      description: '监控000973股票的情绪和看多看空',
      webhook_url: 'https://my-webhook-url.com'
    })
  });

  const data = await response.json();
  const taskId = data.task_id;
  const stockCode = data.intent.entities.stock_code;

  // 配置任务
  await fetch('http://localhost:8000/api/v2/configure_task', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      task_id: taskId,
      stock_code: stockCode,
      analysis_types: ['sentiment', 'bull_bear'],
      platforms: ['eastmoney'],
      interval_minutes: 15
    })
  });

  console.log(`✅ 成功订阅股票${stockCode}的监控`);
};
```

## 🎯 下一步

1. **集成真实LLM** - 将IntentRecognizer替换为GPT/Claude API
2. **添加更多平台** - 实现知乎、微博、雪球爬虫
3. **增强分析能力** - 使用LLM进行深度语义分析
4. **部署到生产** - 部署到云服务器，开放公网访问
5. **微信公众号集成** - 实现微信公众号作为用户交互前端

## 📞 联系方式

- API文档: http://localhost:8000/docs
- 架构文档: `FINAL_ARCHITECTURE.md`
- 使用指南: `CLIENT_USAGE.md`

---

**系统状态**: ✅ 运行正常
**最后更新**: 2026-04-27 15:46:57
