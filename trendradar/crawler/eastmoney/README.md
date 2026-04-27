# 东方财富股吧爬虫模块

## 功能特性

✅ **帖子爬取** - 按股票代码获取帖子列表
✅ **评论爬取** - 获取帖子评论数据（支持分页）
✅ **多股票支持** - 批量爬取多个股票
✅ **异步设计** - 使用 asyncio 提高效率
✅ **简单易用** - 无复杂依赖，开箱即用

## 快速开始

### 基本使用

```python
import asyncio
from trendradar.crawler.eastmoney import crawl_eastmoney_stock

async def main():
    # 爬取贵州茅台（600519）的数据
    result = await crawl_eastmoney_stock(
        stock_code="600519",
        max_pages=2,              # 爬取2页帖子
        enable_comments=True,     # 启用评论爬取
        max_comments_per_post=100 # 每个帖子最多爬100条评论
    )

    print(f"获取到 {result['posts_count']} 条帖子")
    print(f"获取到 {result['comments_count']} 条评论")

    # 访问数据
    for post in result['posts']:
        print(f"- {post['title']}")

asyncio.run(main())
```

### 批量爬取多个股票

```python
import asyncio
from trendradar.crawler.eastmoney import crawl_eastmoney_stocks

async def main():
    # 爬取多个股票
    stock_codes = ["600519", "000001", "300750"]

    result = await crawl_eastmoney_stocks(
        stock_codes=stock_codes,
        max_pages=1,
        enable_comments=True,
        max_comments_per_post=50
    )

    print(f"共爬取 {result['total_stocks']} 个股票")
    print(f"总帖子数: {result['total_posts']}")
    print(f"总评论数: {result['total_comments']}")

    # 查看每个股票的结果
    for stock_code, data in result['results'].items():
        print(f"\n{stock_code}: {data['posts_count']} 条帖子, {data['comments_count']} 条评论")

asyncio.run(main())
```

### 使用爬虫类

```python
import asyncio
from trendradar.crawler.eastmoney import EastMoneyCrawler

async def main():
    # 使用上下文管理器
    async with EastMoneyCrawler() as crawler:
        result = await crawler.crawl_stock_posts(
            stock_code="600519",
            max_pages=1
        )

        # 数据保存在爬虫对象中
        print(f"帖子数据: {len(crawler.posts_data)}")
        print(f"评论数据: {len(crawler.comments_data)}")

asyncio.run(main())
```

## 数据格式

### 帖子数据格式

```python
{
    "post_id": "1699312175",
    "title": "贵州茅台新董事长...",
    "content": "",  # 列表页不包含正文
    "stock_code": "600519",
    "stock_name": "贵州茅台",
    "author_id": "123456",
    "author_name": "用户名",
    "publish_time": "2026-04-26 20:19:07",
    "read_count": 1234,
    "comment_count": 56,
    "like_count": 0,
    "post_type": 1,
    "post_url": "https://guba.eastmoney.com/news,600519,1699312175.html"
}
```

### 评论数据格式

```python
{
    "comment_id": "9879018906",
    "post_id": "1699312175",
    "content": "评论内容...",
    "author_id": "123456",
    "author_name": "用户名",
    "create_time": "2026-04-26 20:19:07",
    "like_count": 5,
    "reply_count": 2,
    "parent_id": ""  # 一级评论为空
}
```

## 常用股票代码

### 白酒板块
```python
["600519",  # 贵州茅台
 "000858",  # 五粮液
 "000568"]  # 泸州老窖
```

### 银行板块
```python
["601398",  # 工商银行
 "601939",  # 建设银行
 "600036"]  # 招商银行
```

### 科技板块
```python
["002415",  # 海康威视
 "000063",  # 中兴通讯
 "300750"]  # 宁德时代
```

### 股票代码规则

| 代码开头 | 市场 | 说明 |
|---------|------|------|
| 600xxx | 上交所主板 | 上海证券交易所 |
| 601xxx | 上交所主板 | 上海证券交易所 |
| 603xxx | 上交所主板 | 上海证券交易所 |
| 000xxx | 深交所主板 | 深圳证券交易所 |
| 001xxx | 深交所主板 | 深圳证券交易所 |
| 002xxx | 深交所中小板 | 深圳证券交易所 |
| 300xxx | 创业板 | 深圳证券交易所 |
| 688xxx | 科创板 | 上海证券交易所 |

## 配置选项

### 自定义Cookie（可选）

```python
cookies = {
    "qgqp_b_id": "your_cookie_value",
    "nid18": "your_cookie_value",
    # ... 其他Cookie
}

result = await crawl_eastmoney_stock(
    stock_code="600519",
    cookies=cookies
)
```

### 爬取参数

- `max_pages`: 最大爬取页数（每页约80条帖子）
- `enable_comments`: 是否启用评论爬取
- `max_comments_per_post`: 每个帖子最大评论数（0表示不限制）

## 注意事项

1. **请求频率**: 代码中已内置延迟（帖子1秒，评论0.5秒），请勿降低延迟
2. **Cookie有效期**: Cookie可能会过期，需要定期更新
3. **数据量控制**: 首次使用建议先测试小数据量（1-2页）
4. **遵守规则**: 仅用于学习研究，遵守网站使用条款

## API 参考

### EastMoneyCrawler

主爬虫类。

#### 方法

- `crawl_stock_posts(stock_code, max_pages, enable_comments, max_comments_per_post)`
  爬取单个股票的帖子和评论

- `crawl_multiple_stocks(stock_codes, max_pages, enable_comments, max_comments_per_post)`
  批量爬取多个股票

### EastMoneyClient

底层客户端类。

#### 方法

- `get_stock_posts(stock_code, page, page_size)`
  获取股票帖子列表

- `get_post_comments(post_id, stock_code, page, page_size)`
  获取帖子评论列表

## 故障排除

### 问题：获取不到数据

**原因**: Cookie可能过期
**解决**: 更新Cookie或使用默认Cookie

### 问题：爬取速度慢

**原因**: 内置延迟保护
**解决**: 正常现象，不建议降低延迟

### 问题：评论数为0

**原因**: 大部分帖子没有评论
**解决**: 正常现象，只有热门帖子有评论

## 完整示例

参见 `/examples/eastmoney_demo.py`

## 技术架构

```
EastMoneyCrawler (爬虫主类)
    ↓
EastMoneyClient (HTTP客户端)
    ↓
httpx (异步HTTP库)
```

## 许可

本代码基于 MediaCrawlerPro 项目改造，仅供学习研究使用。

---

**最后更新**: 2026-04-26
