# CommunitySpy 爬虫修复说明

## 问题诊断

测试发现东方财富API返回错误："系统繁忙, 请稍后再试[00003]"

原因分析：
1. **API需要完整的浏览器请求头** - 包括 `sec-ch-ua` 等现代浏览器特征
2. **可能需要Cookies** - 原始实现包含了用户cookies
3. **API有反爬保护** - 需要模拟真实浏览器行为

## 已完成的改进

### 1. 完整的数据库Schema ✅

新实现包含完整的三表结构：
- `posts` 表：20个字段，包括 abstract, user_level, is_top, is_hot, is_essence, source_type, tags
- `comments` 表：16个字段，包括 parent_comment_id, user_level, floor_number, is_author, is_recommend, ip_address, device_type
- `replies` 表：15个字段，支持回复嵌套和@用户功能

### 2. 正确的API端点 ✅

- 帖子列表：`https://gbapi.eastmoney.com/webarticlelist/api/Article/Articlelist`
- 评论列表：`https://guba.eastmoney.com/api/getData`

### 3. JSONP响应解析 ✅

实现了完整的JSONP解析逻辑，支持：
- 标准JSONP格式：`jsonp_123456_abc(...)`
- 正则表达式fallback
- 纯JSON fallback

### 4. 完整的数据映射 ✅

所有API字段都正确映射到数据库字段：
- 帖子数据：`post_id`, `post_title`, `post_publish_time` 等
- 评论数据：`reply_id`, `reply_text`, `reply_time`, `reply_user` 等
- 设备类型映射：Android(31), iPhone(32), 网页端(46), iPad(42), PC客户端(112)

## 需要解决的问题

### 方案1：添加完整请求头和Cookies（推荐）

**步骤**：

1. 打开浏览器访问 https://guba.eastmoney.com/list,301293.html
2. 打开开发者工具（F12）→ Network 标签
3. 刷新页面，找到 `Articlelist` 请求
4. 复制完整的请求头和Cookies

**需要添加的请求头**：
```python
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
    'sec-ch-ua': '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'Accept': '*/*',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'Connection': 'keep-alive',
    'Referer': 'https://guba.eastmoney.com/',
    'Sec-Fetch-Dest': 'script',
    'Sec-Fetch-Mode': 'no-cors',
    'Sec-Fetch-Site': 'same-site',
}
```

**添加位置**：
- 文件：`trendradar/agent/tools/data_sources/communityspy/spider.py`
- 方法：`__init__()` 的 `self.headers` 字典

### 方案2：使用Selenium模拟真实浏览器

使用Selenium + undetected-chromedriver绕过反爬：

```python
import undetected_chromedriver as uc

class EastMoneyCommentSpider:
    def __init__(self, stock_code: str, use_selenium: bool = False):
        if use_selenium:
            options = uc.ChromeOptions()
            options.add_argument('--headless')
            self.driver = uc.Chrome(options=options)
```

**优点**：
- 完全模拟真实浏览器
- 自动处理Cookies和JS执行
- 绕过大多数反爬措施

**缺点**：
- 需要额外依赖：`undetected-chromedriver`
- 速度较慢
- 资源占用较大

### 方案3：添加代理和请求延迟

```python
# 增加延迟
time.sleep(random.uniform(2, 5))

# 使用代理池
proxies = {
    'http': 'http://proxy:port',
    'https': 'http://proxy:port'
}
```

### 方案4：使用原有communityspy项目的完整实现

直接使用 `/Users/wangxinlong/Code/communityspy/communityspy.py`，因为它：
- 已验证可工作
- 包含完整的Cookies
- 包含所有必要的请求头

## 快速修复方案

### Step 1: 更新请求头

编辑 `spider.py` 的第41-45行：

```python
self.headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
    'sec-ch-ua': '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'Accept': '*/*',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'Connection': 'keep-alive',
    'Referer': 'https://guba.eastmoney.com/',
    'Sec-Fetch-Dest': 'script',
    'Sec-Fetch-Mode': 'no-cors',
    'Sec-Fetch-Site': 'same-site',
}
```

### Step 2: 添加Cookies（可选但建议）

在 `__init__` 方法中添加：

```python
def __init__(self, stock_code: str, db_path: Optional[str] = None, cookies: Optional[str] = None):
    # ...existing code...

    # 如果提供了cookies，解析并设置
    if cookies:
        self.session.cookies.update(self._parse_cookies(cookies))

@staticmethod
def _parse_cookies(cookie_str: str) -> Dict[str, str]:
    """解析cookie字符串为字典"""
    cookies = {}
    for item in cookie_str.split(';'):
        item = item.strip()
        if '=' in item:
            key, value = item.split('=', 1)
            cookies[key] = value
    return cookies
```

### Step 3: 增加请求延迟

在 `crawl()` 方法中的延迟改为随机延迟：

```python
import random

# 在请求之间添加随机延迟
time.sleep(random.uniform(1.5, 3.0))
```

## 测试验证

修复后运行测试：

```bash
# 1. 测试API（不实际爬取）
python3 test_api.py

# 2. 测试爬取2条帖子（不含评论）
cd trendradar/agent/tools/data_sources/communityspy
python3 cli.py 301293 --max-posts 2 --no-comments

# 3. 测试完整爬取
python3 cli.py 301293 --max-posts 10

# 4. 查看数据
sqlite3 eastmoney_301293.db
SELECT COUNT(*) FROM posts;
SELECT COUNT(*) FROM comments;
SELECT COUNT(*) FROM replies;
```

## 当前状态

- ✅ 代码结构正确
- ✅ 数据库Schema完整
- ✅ API端点正确
- ✅ JSONP解析正确
- ✅ 数据映射完整
- ⚠️  需要添加完整请求头和Cookies才能实际爬取数据

## 建议

1. **优先尝试方案1**（添加请求头），这是最简单和直接的方式
2. 如果方案1不行，可以使用方案4（复制原有项目的完整实现）
3. 生产环境建议使用方案2（Selenium）以获得最好的稳定性

## 参考文件

- 原始实现：`/Users/wangxinlong/Code/communityspy/communityspy.py`
- 新实现：`/Users/wangxinlong/Code/TrendRadar/trendradar/agent/tools/data_sources/communityspy/spider.py`
- 测试脚本：`/Users/wangxinlong/Code/TrendRadar/test_api.py`
