# 客户端使用指南

## 📖 概述

智能股票监控系统提供了两个Python客户端工具来模拟用户订阅股票舆论信息：

1. **simple_client_test.py** - 简化版快速测试（推荐）
2. **client_simulator.py** - 完整交互式模拟器

## 🚀 快速开始

### 前提条件

确保服务已启动：
```bash
# 检查智能监控服务 (端口8000)
curl http://localhost:8000/

# 检查Webhook接收器 (端口9000)
curl http://localhost:9000/
```

### 方式一：快速测试（推荐）

```bash
python3 simple_client_test.py
```

这个脚本会自动完成：
1. 创建监控任务（订阅000973股票）
2. 配置分析维度（情绪统计、看多看空、有价值评论）
3. 等待数据采集和分析
4. 显示推送的报告

**输出示例：**
```
================================================================================
🤖 智能股票监控系统 - 快速测试
================================================================================

📝 步骤1: 创建监控任务...
✅ 任务创建成功
   任务ID: task_xxxx
   股票代码: 000973

⚙️  步骤2: 配置任务...
✅ 任务配置成功，系统正在进行首次数据采集...

⏳ 步骤3: 等待数据采集和分析 (约30-60秒)...
   (爬虫Agent采集数据 → 分析Agent分析 → 生成报告 → Webhook推送)

✅ 收到分析报告！

================================================================================
📊 股票 000973 舆论监控报告
================================================================================
# 📊 股票 000973 智能监控报告

**生成时间**: 2026-04-27 15:13:32

---

## 📈 数据概况

### EASTMONEY
- 帖子数: 209
- 评论数: 267

## 🔍 智能分析

### 😊 情绪统计

- 积极: 92 (19.33%)
- 消极: 21 (4.41%)
- 中性: 363 (76.26%)

### 📊 看多看空

- 看多: 75 (76.53%)
- 看空: 23 (23.47%)
- **市场情绪**: 看多占优

### ⭐ 有价值的评论

发现 1 条高质量帖子 (0.48%)

1. **锂电隔膜+超薄隔膜+业绩暴增+广东国资...**
   - 作者: 关注牛股最新消息 | 特征: 有依据, 有结论
   - 评论: 5 | 阅读: 1002

---

*本报告由AI智能生成*
================================================================================

📋 任务信息:
   任务ID: task_xxxx
   状态: active
   下次执行: 约10分钟后

================================================================================
✅ 订阅成功！系统将每10分钟自动采集分析并推送报告
================================================================================
```

### 方式二：交互式模拟器

```bash
python3 client_simulator.py
```

这个脚本提供交互式体验：
1. 输入自然语言描述
2. AI理解意图并提供配置建议
3. 选择是否立即触发或等待定时执行
4. 查看详细的执行过程和结果

**交互示例：**
```
选项:
  1. 立即触发执行并等待结果
  2. 等待定时任务自动执行（每10分钟）
  3. 退出

请选择 (1/2/3): 1
```

## 📊 查看推送的报告

### 通过Webhook接收器查看所有报告

```bash
# 查看所有收到的消息
curl http://localhost:9000/messages | python3 -m json.tool

# 查看最近的报告
curl -s http://localhost:9000/messages | python3 -m json.tool | tail -100
```

### 查看服务日志

```bash
# 查看智能监控服务日志
tail -f logs/intelligent_service.log

# 查看Webhook接收日志
tail -f logs/webhook_receiver.log
```

## 🔍 API调用示例

### 1. 创建监控任务

```bash
curl -X POST "http://localhost:8000/api/v2/create_task" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "description": "我想监控000973这只股票的舆论信息，关注情绪统计、看多看空比例和有价值的评论",
    "webhook_url": "http://localhost:9000/webhook/generic"
  }'
```

**响应：**
```json
{
  "task_id": "task_xxxx",
  "intent": {
    "intent": "monitor_stock",
    "entities": {"stock_code": "000973"},
    "suggested_analysis": ["sentiment", "bull_bear", "quality_posts"],
    "suggested_platforms": ["eastmoney"]
  },
  "configuration_options": {
    "stock_code": "000973",
    "analysis_options": [...],
    "platform_options": [...]
  },
  "next_step": "请调用 /api/v2/configure_task 完成配置"
}
```

### 2. 配置任务

```bash
curl -X POST "http://localhost:8000/api/v2/configure_task" \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "task_xxxx",
    "stock_code": "000973",
    "analysis_types": ["sentiment", "bull_bear", "quality_posts"],
    "platforms": ["eastmoney"],
    "interval_minutes": 10
  }'
```

**响应：**
```json
{
  "success": true,
  "message": "任务已激活，正在进行首次采集分析...",
  "task_id": "task_xxxx"
}
```

### 3. 查询任务状态

```bash
curl "http://localhost:8000/api/v2/task/task_xxxx"
```

### 4. 手动触发任务

```bash
curl -X POST "http://localhost:8000/api/v2/trigger/task_xxxx"
```

## 💡 理解工作流程

完整的智能监控流程：

```
用户输入自然语言
        ↓
AI理解意图 (IntentRecognizer)
        ↓
生成配置选项 (ConfigurationGuide)
        ↓
用户确认配置
        ↓
激活监控任务 (TaskManager)
        ↓
定时/手动触发执行
        ↓
爬虫Agent采集数据 (CrawlerAgent)
   ├─ 东方财富股吧 (当前支持)
   ├─ 知乎 (待开发)
   └─ 微博 (待开发)
        ↓
分析Agent智能分析 (AnalysisAgent)
   ├─ 情绪统计
   ├─ 看多看空比例
   ├─ 有价值的评论
   ├─ 活跃用户分析
   └─ 热门话题
        ↓
生成结构化报告 (ReportGenerator)
        ↓
推送给用户 (Webhook)
   ├─ 飞书
   ├─ 钉钉
   ├─ 企业微信
   └─ 通用Webhook
```

## 🛠️ 自定义测试

### 监控不同的股票

编辑 `simple_client_test.py` 或 `client_simulator.py` 中的描述：

```python
description = "我想监控600519(茅台)的舆论信息，关注情绪和看多看空"
```

### 调整监控频率

```python
"interval_minutes": 5  # 每5分钟执行一次
```

### 选择不同的分析维度

```python
"analysis_types": [
    "sentiment",        # 情绪统计
    "bull_bear",        # 看多看空
    "quality_posts",    # 有价值评论
    "active_users",     # 活跃用户
    "hot_topics"        # 热门话题
]
```

## 🐛 故障排除

### 问题1: 连接拒绝

**症状：** `ConnectionRefusedError` 或 `Failed to connect`

**解决：**
```bash
# 检查服务状态
ps aux | grep intelligent_monitor_service
ps aux | grep test_client

# 重启服务
kill $(cat /tmp/intelligent_service.pid)
python3 intelligent_monitor_service.py > logs/intelligent_service.log 2>&1 &
echo $! > /tmp/intelligent_service.pid

# 重启Webhook接收器
python3 test_client.py server > logs/webhook_receiver.log 2>&1 &
```

### 问题2: 等待超时

**症状：** 客户端等待超过90秒仍未收到报告

**可能原因：**
- 爬虫数据采集较慢
- 数据量较大，分析耗时

**解决：**
```bash
# 直接查看webhook消息
curl http://localhost:9000/messages | python3 -m json.tool

# 查看服务日志了解进度
tail -f logs/intelligent_service.log
```

### 问题3: Stock_code为空

**症状：** 报告标题显示"股票  智能监控报告"（股票代码缺失）

**原因：** 正则表达式未匹配到6位数字股票代码

**解决：** 在描述中明确包含6位数字，如"000973"、"600519"

### 问题4: 没有数据

**症状：** 报告显示"帖子数: 0, 评论数: 0"

**可能原因：**
- 股票代码不存在或输入错误
- 东方财富股吧暂无该股票讨论
- 网络问题导致爬虫失败

**解决：**
```bash
# 检查爬虫日志
grep "爬虫Agent" logs/intelligent_service.log | tail -20

# 手动测试爬虫
python3 -c "from trendradar.crawler.eastmoney import EastmoneyCrawler; import asyncio; asyncio.run(EastmoneyCrawler().get_stock_comments('000973', 1))"
```

## 📚 更多信息

- 完整架构文档: `FINAL_ARCHITECTURE.md`
- API文档: http://localhost:8000/docs
- 部署状态: `deployment_status.txt`

## ✅ 验证系统正常工作

运行快速健康检查：

```bash
#!/bin/bash
echo "=== 智能监控系统健康检查 ==="
echo ""

echo "1. 检查智能监控服务 (端口8000)..."
curl -s http://localhost:8000/ > /dev/null && echo "✅ 服务正常" || echo "❌ 服务异常"

echo ""
echo "2. 检查Webhook接收器 (端口9000)..."
curl -s http://localhost:9000/ > /dev/null && echo "✅ 服务正常" || echo "❌ 服务异常"

echo ""
echo "3. 检查数据库..."
[ -f "tasks.db" ] && echo "✅ tasks.db 存在" || echo "❌ tasks.db 不存在"
[ -f "eastmoney_stocks.db" ] && echo "✅ eastmoney_stocks.db 存在" || echo "❌ eastmoney_stocks.db 不存在"

echo ""
echo "4. 检查日志..."
[ -f "logs/intelligent_service.log" ] && echo "✅ 服务日志存在" || echo "❌ 服务日志不存在"
[ -f "logs/webhook_receiver.log" ] && echo "✅ Webhook日志存在" || echo "❌ Webhook日志不存在"

echo ""
echo "=== 检查完成 ==="
```

保存为 `health_check.sh` 并运行：
```bash
chmod +x health_check.sh
./health_check.sh
```
