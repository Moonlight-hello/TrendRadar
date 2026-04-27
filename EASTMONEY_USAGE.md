# 东方财富爬虫使用指南

## 🚀 快速开始

### 方法 1: 直接运行示例脚本

```bash
# 在项目根目录运行
cd /Users/wangxinlong/Code/TrendRadarRepository/TrendRadar

# 运行示例（已自动设置 Python 路径）
python3 examples/eastmoney_demo.py
```

### 方法 2: 运行测试脚本

```bash
# 快速测试爬虫功能
python3 test_eastmoney.py
```

### 方法 3: 在代码中使用

```python
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent  # 根据你的位置调整
sys.path.insert(0, str(project_root))

# 导入模块
from trendradar.crawler.eastmoney import crawl_eastmoney_stock

# 使用
import asyncio

async def main():
    result = await crawl_eastmoney_stock(
        stock_code="600519",
        max_pages=1,
        enable_comments=True
    )
    print(f"获取到 {result['posts_count']} 条帖子")
    print(f"获取到 {result['comments_count']} 条评论")

asyncio.run(main())
```

## 📝 安装依赖

如果遇到 `ModuleNotFoundError`，确保安装了依赖：

```bash
# 安装 httpx（必需）
pip3 install httpx

# 或安装所有项目依赖
pip3 install -e .
```

## 🎯 使用示例

### 示例 1: 爬取单个股票

```python
import asyncio
import sys
from pathlib import Path

# 设置 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from trendradar.crawler.eastmoney import crawl_eastmoney_stock

async def main():
    result = await crawl_eastmoney_stock(
        stock_code="600519",      # 贵州茅台
        max_pages=2,              # 爬取2页
        enable_comments=True,     # 启用评论
        max_comments_per_post=50  # 每个帖子最多50条评论
    )

    print(f"\n✅ 爬取完成!")
    print(f"📊 帖子数: {result['posts_count']}")
    print(f"💬 评论数: {result['comments_count']}")

    # 显示前3条帖子
    for i, post in enumerate(result['posts'][:3], 1):
        print(f"\n{i}. {post['title'][:50]}...")
        print(f"   作者: {post['author_name']}")
        print(f"   评论: {post['comment_count']}")

asyncio.run(main())
```

### 示例 2: 批量爬取多个股票

```python
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from trendradar.crawler.eastmoney import crawl_eastmoney_stocks

async def main():
    result = await crawl_eastmoney_stocks(
        stock_codes=["600519", "000001", "300750"],
        max_pages=1,
        enable_comments=True
    )

    print(f"\n✅ 批量爬取完成!")
    print(f"📈 股票数: {result['total_stocks']}")
    print(f"📊 总帖子: {result['total_posts']}")
    print(f"💬 总评论: {result['total_comments']}")

    # 显示每个股票的统计
    for stock_code, data in result['results'].items():
        print(f"\n{stock_code}:")
        print(f"  - 帖子: {data['posts_count']}")
        print(f"  - 评论: {data['comments_count']}")

asyncio.run(main())
```

### 示例 3: 保存数据到 JSON

```python
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from trendradar.crawler.eastmoney import crawl_eastmoney_stock

async def main():
    result = await crawl_eastmoney_stock(
        stock_code="600519",
        max_pages=1
    )

    # 保存到 JSON 文件
    with open("eastmoney_data.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"✅ 数据已保存到 eastmoney_data.json")
    print(f"📊 帖子: {result['posts_count']}")
    print(f"💬 评论: {result['comments_count']}")

asyncio.run(main())
```

## 🔧 常见问题

### Q1: ModuleNotFoundError: No module named 'trendradar'

**解决方法**：

1. **方法 A（推荐）**: 使用已修复的示例脚本
   ```bash
   python3 examples/eastmoney_demo.py  # 已自动设置路径
   python3 test_eastmoney.py           # 已自动设置路径
   ```

2. **方法 B**: 在你的脚本开头添加路径设置
   ```python
   import sys
   from pathlib import Path

   project_root = Path(__file__).parent.parent
   sys.path.insert(0, str(project_root))
   ```

3. **方法 C**: 安装项目包
   ```bash
   cd /Users/wangxinlong/Code/TrendRadarRepository/TrendRadar
   pip3 install -e .
   ```

### Q2: ModuleNotFoundError: No module named 'httpx'

**解决方法**：
```bash
pip3 install httpx
```

### Q3: 爬取失败或数据为空

**可能原因**：
- Cookie 过期
- 网络连接问题
- 股票代码错误

**解决方法**：
- 检查网络连接
- 更新 `trendradar/crawler/eastmoney/client.py` 中的 cookies
- 确认股票代码正确

## 📂 项目结构

```
/Users/wangxinlong/Code/TrendRadarRepository/TrendRadar/
├── trendradar/
│   └── crawler/
│       └── eastmoney/
│           ├── __init__.py      - 模块导出
│           ├── client.py        - HTTP 客户端
│           ├── crawler.py       - 爬虫核心
│           ├── field.py         - 字段定义
│           └── README.md        - 详细文档
├── examples/
│   └── eastmoney_demo.py        - 示例脚本（已修复）
├── test_eastmoney.py            - 测试脚本（已修复）
├── EASTMONEY_MIGRATION.md       - 迁移文档
└── EASTMONEY_USAGE.md           - 本文档
```

## 📚 相关文档

- **详细 API 文档**: `trendradar/crawler/eastmoney/README.md`
- **迁移说明**: `EASTMONEY_MIGRATION.md`
- **示例代码**: `examples/eastmoney_demo.py`

## 🎯 常用股票代码

### 白酒板块
```python
["600519",  # 贵州茅台
 "000858",  # 五粮液
 "000568"]  # 泸州老窖
```

### 银行板块
```python
["601398",  # 工商银行
 "600036",  # 招商银行
 "000001"]  # 平安银行
```

### 科技板块
```python
["002415",  # 海康威视
 "300750",  # 宁德时代
 "000063"]  # 中兴通讯
```

## ⚠️ 注意事项

1. **请求频率**: 代码已内置延迟（帖子1秒，评论0.5秒），请勿降低
2. **Cookie 有效期**: Cookie 可能会过期，需要定期更新
3. **数据量控制**: 首次使用建议先测试小数据量（1-2页）
4. **遵守规则**: 仅用于学习研究，遵守网站使用条款

## 💡 提示

- 所有示例脚本（`examples/eastmoney_demo.py` 和 `test_eastmoney.py`）已自动设置 Python 路径，可直接运行
- 如果在其他位置编写脚本，记得添加路径设置代码
- 推荐使用 `asyncio` 异步方式，性能更好

---

**最后更新**: 2026-04-26
**维护者**: TrendRadar Team
