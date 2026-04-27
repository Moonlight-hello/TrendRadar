# 股票监控系统使用指南

## 📌 系统概述

本系统基于东方财富股吧爬虫，提供股票舆情监控和情绪分析功能。

### 主要功能

1. **数据采集**: 爬取东方财富股吧的帖子和评论
2. **多账号检测**: 识别活跃用户和可能的多账号操作
3. **情绪分析**: 计算看多/看空情绪占比
4. **质量分析**: 识别有理论、有依据、有结论的高质量分析帖

---

## 🚀 快速开始

### 1. 监控单个股票

```bash
# 监控股票 000973 (佛塑科技)
python3 monitor_stock.py --stock 000973 --pages 3 --comments 50

# 参数说明:
#   --stock: 股票代码
#   --pages: 爬取页数 (默认5)
#   --comments: 每个帖子最大评论数 (默认100)
#   --no-comments: 不爬取评论
```

### 2. 监控多个股票

```bash
# 批量监控
python3 monitor_stock.py --stocks "000973,600519,000858" --pages 2 --comments 30
```

### 3. 情绪分析

```bash
# 分析已爬取的数据
python3 analyze_stock_sentiment.py \
  --file output/stocks/000973_20260426_231820.json \
  --save output/stocks/000973_sentiment.json
```

---

## 📊 分析报告示例

### 运行结果 (股票 000973)

#### 基本数据
- **帖子数**: 216条
- **评论数**: 251条
- **爬取时间**: 2026-04-26 23:18

#### 多账号检测
- **活跃用户**: 40人 (发帖/评论 ≥3条)
- **Top 3 活跃用户**:
  1. 吉普森吉他: 12条 (5帖+7评)
  2. 一红就爆: 10条 (6帖+4评)
  3. 暗绿色老韭菜: 9条 (3帖+6评)

#### 情绪分析
- **看多**: 103条 (22.06%) 🔥
- **看空**: 17条 (3.64%)
- **中性**: 347条 (74.30%)
- **情绪倾向**: **看多占优** (高出 18.42%)

#### 质量分析
- **质量帖子**: 1/216 (0.46%)
- **特征**: 包含理论、依据、结论

#### 最热门帖子
1. "4月第9只票，佛塑科技，一季报业绩炸裂..." (评论:23, 阅读:1572)
2. "4月23日交易记录" (评论:18, 阅读:3172)
3. "佛塑2026年预期业绩和市值" (评论:14, 阅读:1805)

---

## 📁 文件结构

```
TrendRadar/
├── monitor_stock.py              # 股票监控主程序
├── analyze_stock_sentiment.py    # 情绪分析程序
├── trendradar/
│   └── crawler/
│       └── eastmoney/           # 东方财富爬虫模块
│           ├── client.py        # HTTP客户端
│           ├── crawler.py       # 爬虫核心
│           └── field.py         # 字段定义
├── output/
│   └── stocks/                  # 数据输出目录
│       ├── {stock}_{time}.json              # 完整数据
│       ├── {stock}_{time}_analysis.json     # 摘要数据
│       └── {stock}_{time}_sentiment.json    # 情绪分析
└── examples/
    └── eastmoney_demo.py        # 使用示例
```

---

## 🔍 数据格式

### 爬虫输出 (JSON)

```json
{
  "stock_code": "000973",
  "posts_count": 216,
  "comments_count": 251,
  "posts": [
    {
      "post_id": "1699360534",
      "title": "帖子标题",
      "author_name": "作者",
      "author_id": "123456",
      "publish_time": "2026-04-26 12:00:00",
      "comment_count": 10,
      "read_count": 500
    }
  ],
  "comments": [
    {
      "comment_id": "123",
      "post_id": "1699360534",
      "author_name": "评论者",
      "content": "评论内容",
      "create_time": "2026-04-26 13:00:00",
      "like_count": 5
    }
  ]
}
```

### 情绪分析输出 (JSON)

```json
{
  "stock_code": "000973",
  "multiple_accounts": {
    "active_user_count": 40,
    "active_users": {
      "用户名": {
        "total_count": 12,
        "post_count": 5,
        "comment_count": 7
      }
    }
  },
  "sentiment_analysis": {
    "bullish": {
      "count": 103,
      "percentage": 22.06
    },
    "bearish": {
      "count": 17,
      "percentage": 3.64
    },
    "neutral": {
      "count": 347,
      "percentage": 74.30
    }
  },
  "quality_posts": {
    "quality_post_count": 1,
    "percentage": 0.46
  }
}
```

---

## 🎯 下一步计划

### 已完成 ✅

1. ✅ 东方财富爬虫迁移到 TrendRadar
2. ✅ 股票监控脚本
3. ✅ 情绪分析功能
4. ✅ 多账号检测
5. ✅ 质量帖子识别

### 待开发 🔨

1. **分析 Agent**:
   - 使用 AI 模型进行深度情绪分析
   - 识别异常舆情模式
   - 生成投资建议报告

2. **实时监控**:
   - 定时任务调度
   - 数据变化通知
   - 异常情绪预警

3. **数据可视化**:
   - 情绪趋势图表
   - 用户活跃度分析
   - 关键词云图

4. **集成到 TrendRadar**:
   - 添加到 config.yaml 配置
   - 统一存储到 SQLite
   - 推送通知集成

---

## 💡 使用建议

### 数据采集

1. **控制频率**: 建议每小时采集一次，避免频繁请求
2. **页数设置**: 3-5页即可覆盖大部分热点内容
3. **评论数量**: 50-100条/帖子足够分析需求

### 情绪分析

1. **关键词扩展**: 可根据实际情况调整看多/看空关键词列表
2. **阈值调整**: 多账号检测阈值建议设为 3-5 条
3. **质量判断**: 当前基于关键词匹配，后续可引入 AI 评分

### 数据存储

1. **定期清理**: 建议保留最近 30 天数据
2. **备份策略**: 重要数据定期备份到云存储
3. **索引优化**: 大量数据建议使用数据库存储

---

## ⚠️ 注意事项

1. **合规使用**: 仅用于个人学习研究，遵守网站使用条款
2. **请求频率**: 代码已内置延迟（1秒/页），请勿降低
3. **Cookie 更新**: Cookie 可能过期，需定期更新 (在 `client.py` 中配置)
4. **数据准确性**: 情绪分析基于关键词匹配，存在误判可能

---

## 🔗 相关文档

- **东方财富爬虫文档**: `trendradar/crawler/eastmoney/README.md`
- **迁移说明**: `EASTMONEY_MIGRATION.md`
- **使用指南**: `EASTMONEY_USAGE.md`

---

## 📞 常见问题

### Q1: 如何添加新的股票监控？

直接使用 `--stock` 或 `--stocks` 参数指定股票代码即可：

```bash
python3 monitor_stock.py --stock 600519  # 贵州茅台
python3 monitor_stock.py --stocks "600519,000858,000001"
```

### Q2: 情绪分析不准确怎么办？

可以修改 `analyze_stock_sentiment.py` 中的关键词列表：

```python
BULLISH_KEYWORDS = ["看多", "看好", ...]  # 添加更多关键词
BEARISH_KEYWORDS = ["看空", "看衰", ...]
```

### Q3: 如何定时运行监控？

使用 crontab 或其他调度工具：

```bash
# 每小时运行一次
0 * * * * cd /path/to/TrendRadar && python3 monitor_stock.py --stock 000973
```

### Q4: 数据文件太大怎么办？

可以调整爬取参数：

```bash
# 减少页数和评论数
python3 monitor_stock.py --stock 000973 --pages 2 --comments 20
```

---

## 📈 性能指标

基于实际测试 (股票 000973):

- **爬取速度**: ~3页/分钟 (含评论)
- **数据量**: 216帖 + 251评 ≈ 185KB JSON
- **分析速度**: <1秒 (情绪分析)
- **内存占用**: <50MB

---

**最后更新**: 2026-04-26
**维护者**: TrendRadar Team
