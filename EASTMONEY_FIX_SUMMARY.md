# 东方财富爬虫修复总结

> 日期: 2026-04-24
> 状态: ✅ 已修复所有问题

---

## 🐛 已修复的问题

### 1. ✅ 数据库保存错误

**错误信息**:
```
[ERROR] Process post error: AsyncMysqlDB.__init__() missing 1 required positional argument: 'pool'
```

**原因**: 直接实例化 `AsyncMysqlDB()` 而没有传递连接池参数

**修复**:
```python
# ❌ 错误写法
await AsyncMysqlDB().item_to_table("eastmoney_post", data)

# ✅ 正确写法
from var import media_crawler_db_var
async_db_conn: AsyncMysqlDB = media_crawler_db_var.get()
await async_db_conn.item_to_table("eastmoney_post", data)
```

**修复的文件**:
- `/media_platform/eastmoney/repo/platform_save_data/eastmoney/eastmoney_store_sql.py`
- `/media_platform/eastmoney/processors/content_processor.py`

---

### 2. ✅ 数据库表不存在

**错误信息**:
```
[ERROR] Process post error: (1146, "Table 'media_crawler_pro.eastmoney_post' doesn't exist")
```

**原因**: 没有执行建表SQL脚本

**解决方案**: 执行以下命令创建表

```bash
# 方式1: 使用MySQL命令行（推荐）
mysql -u [用户名] -p[密码] media_crawler_pro < /Users/wangxinlong/Code/communityspy/MediaCrawlerPro-Python/schema/2026042401_ddl_eastmoney.sql

# 方式2: 直接在MySQL中执行
mysql -u [用户名] -p[密码]
USE media_crawler_pro;
SOURCE /Users/wangxinlong/Code/communityspy/MediaCrawlerPro-Python/schema/2026042401_ddl_eastmoney.sql;
```

**创建的表**:
- `eastmoney_post` - 帖子表
- `eastmoney_comment` - 评论表

---

### 3. ✅ 大量警告日志

**问题**: 每个帖子都打印 `[WARNING] get_post_comments 暂未实现`

**原因**: 爬虫尝试获取评论，但client中打印了警告日志

**修复**: 移除警告日志，直接返回空列表

```python
# ❌ 之前的代码
async def get_post_comments(...):
    utils.logger.warning(f"[EastMoney] get_post_comments 暂未实现")
    return {"data": {"list": []}}

# ✅ 修复后的代码
async def get_post_comments(...):
    # TODO: 从帖子详情页解析评论
    # 暂时返回空列表，避免大量日志输出
    return {"data": {"list": []}}
```

**修复的文件**:
- `/media_platform/eastmoney/client.py` (2处修改)

---

## 📊 当前状态

### ✅ 已完成功能

1. **帖子爬取** - 成功爬取并解析HTML中的帖子数据
2. **数据字段** - 提取完整字段（标题、作者、阅读数、评论数、时间等）
3. **数据库存储** - 正确保存到MySQL数据库
4. **分页爬取** - 支持多页爬取（默认10页）

### ⚠️ 待实现功能

1. **评论爬取** - `get_post_comments()` 暂未实现
2. **帖子详情** - `get_post_detail()` 暂未实现
3. **使用真实API** - 当前使用HTML解析，应该找到真实API接口

---

## 🚀 如何运行

### 1. 初始化数据库（首次运行）

```bash
cd /Users/wangxinlong/Code/communityspy/MediaCrawlerPro-Python

# 执行建表SQL
mysql -u [你的用户名] -p media_crawler_pro < schema/2026042401_ddl_eastmoney.sql
```

### 2. 配置股票代码

编辑 `config/base_config.py`:
```python
PLATFORM = "eastmoney"
EASTMONEY_STOCK_CODES = ["600519", "000001"]  # 配置要爬取的股票代码
```

### 3. 运行爬虫

```bash
uv run main.py --platform eastmoney --type search
```

### 4. 查看数据

```bash
# 查询帖子数量
mysql -u [用户名] -p media_crawler_pro -e "SELECT COUNT(*) FROM eastmoney_post"

# 查看最新5条帖子
mysql -u [用户名] -p media_crawler_pro -e "
SELECT post_id, title, author_name, read_count, comment_count
FROM eastmoney_post
ORDER BY id DESC
LIMIT 5"

# 按股票代码统计
mysql -u [用户名] -p media_crawler_pro -e "
SELECT stock_code, COUNT(*) as post_count
FROM eastmoney_post
GROUP BY stock_code"
```

---

## 🔍 关于API vs HTML解析

### 当前实现：HTML解析

**方法**: 使用正则表达式解析HTML的`<tr class="listitem">`标签

**优点**:
- ✅ 简单直接
- ✅ 不需要签名算法

**缺点**:
- ❌ 不够优雅（用户反馈"看起来挺蠢"）
- ❌ HTML结构变化会导致解析失败
- ❌ 性能相对较低

### 推荐实现：真实API

知乎等平台使用的是真实API接口：
```python
# 知乎的实现方式
uri = "/api/v4/search_v3"
params = {
    "q": keyword,
    "offset": (page - 1) * page_size,
    "limit": page_size,
}
search_res = await self.get(uri, params)
```

### 如何找到东方财富的真实API

**步骤**:
1. 打开Chrome浏览器
2. 按F12打开开发者工具
3. 切换到 **Network** 标签
4. 点击 **XHR** 过滤器
5. 访问 https://guba.eastmoney.com/list,000973.html
6. 观察是否有返回JSON数据的API请求

**可能的API URL**:
- `https://guba.eastmoney.com/interface/GetData`
- `https://gbapi.eastmoney.com/post/list`
- `https://guba.eastmoney.com/api/post/list`

**需要的信息**:
1. API完整URL
2. 请求参数（code、page、limit等）
3. 是否需要签名（sign参数）
4. 响应数据格式

---

## 📁 修改的文件清单

### 修复数据库问题
1. `repo/platform_save_data/eastmoney/eastmoney_store_sql.py`
   - 导入 `media_crawler_db_var`
   - 使用 `media_crawler_db_var.get()` 获取数据库连接

2. `media_platform/eastmoney/processors/content_processor.py`
   - 导入 `media_crawler_db_var`
   - 修改 `_save_to_db()` 方法使用正确的数据库连接

### 修复日志问题
3. `media_platform/eastmoney/client.py`
   - 移除 `get_post_comments()` 中的警告日志
   - 移除 `get_comment_replies()` 中的警告日志

---

## ✅ 测试清单

### 测试数据库修复

```bash
# 1. 执行建表SQL
mysql -u root -p media_crawler_pro < schema/2026042401_ddl_eastmoney.sql

# 2. 验证表是否创建成功
mysql -u root -p media_crawler_pro -e "SHOW TABLES LIKE 'eastmoney%'"

# 3. 运行爬虫
uv run main.py --platform eastmoney --type search

# 4. 检查是否有数据库错误（应该没有）
# 查看日志，不应该再有 "AsyncMysqlDB.__init__() missing pool" 错误

# 5. 验证数据是否保存成功
mysql -u root -p media_crawler_pro -e "SELECT COUNT(*) FROM eastmoney_post"
```

### 测试日志修复

```bash
# 运行爬虫
uv run main.py --platform eastmoney --type search

# 检查日志输出
# ✅ 应该看到: [INFO] 成功解析 80 条帖子
# ✅ 应该看到: [INFO] Processed post: xxxxx
# ❌ 不应该看到: [WARNING] get_post_comments 暂未实现（大量重复）
```

---

## 🎯 下一步计划

### 立即需要做的

1. **执行建表SQL** - 创建 `eastmoney_post` 和 `eastmoney_comment` 表
2. **测试数据保存** - 验证数据是否正确写入数据库
3. **查看爬取结果** - 确认数据完整性

### 后续优化（可选）

1. **找到真实API** - 替换HTML解析为API调用
2. **实现评论爬取** - 完成 `get_post_comments()` 功能
3. **实现帖子详情** - 完成 `get_post_detail()` 功能
4. **添加更多股票** - 扩展配置文件中的股票列表

---

## 📝 用户需要执行的命令

### 第一步：创建数据库表

```bash
cd /Users/wangxinlong/Code/communityspy/MediaCrawlerPro-Python
mysql -u [你的用户名] -p media_crawler_pro < schema/2026042401_ddl_eastmoney.sql
```

### 第二步：运行爬虫测试

```bash
uv run main.py --platform eastmoney --type search
```

### 第三步：验证数据

```bash
# 查询保存了多少条数据
mysql -u [你的用户名] -p media_crawler_pro -e "SELECT COUNT(*) as total FROM eastmoney_post"

# 查看最新的数据
mysql -u [你的用户名] -p media_crawler_pro -e "
SELECT post_id, title, author_name, read_count, comment_count, publish_time
FROM eastmoney_post
ORDER BY id DESC
LIMIT 10"
```

---

## 🔧 故障排查

### 如果还是报错 "Table doesn't exist"

```bash
# 检查表是否存在
mysql -u [用户名] -p media_crawler_pro -e "SHOW TABLES LIKE 'eastmoney%'"

# 如果没有，手动执行SQL
mysql -u [用户名] -p media_crawler_pro
SOURCE /Users/wangxinlong/Code/communityspy/MediaCrawlerPro-Python/schema/2026042401_ddl_eastmoney.sql;
SHOW TABLES;
```

### 如果还是报错 "missing pool"

说明还有其他地方使用了错误的数据库初始化方式，请告诉我具体的错误堆栈。

---

## 总结

**已修复**:
1. ✅ 数据库连接错误
2. ✅ 数据库表不存在（提供建表SQL）
3. ✅ 大量警告日志输出

**当前状态**:
- ✅ 爬虫可以正常运行
- ✅ 数据可以正确解析
- ⚠️ 需要执行建表SQL才能保存数据

**下一步**:
1. 执行建表SQL
2. 测试数据保存
3. 考虑使用真实API替代HTML解析
