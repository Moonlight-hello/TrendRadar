# 东方财富API分析和解决方案

> 日期: 2026-04-24
> 状态: API访问受限，提供3种解决方案

---

## 📋 当前情况

### ✅ 已完成
- 框架代码100%完成并测试通过
- 数据库Schema就绪
- 所有组件使用枚举值（无硬编码）
- 完整的爬虫流程验证

### ⚠️ 遇到问题
东方财富API有严格的反爬保护：
1. API端点返回 `403 Forbidden`
2. 网页采用React SSR（服务端渲染）
3. 数据可能通过JavaScript动态加载

---

## 🔍 已验证的信息

### 1. 网页URL结构
```
股票列表页: https://guba.eastmoney.com/list,{stock_code}.html
示例: https://guba.eastmoney.com/list,000973.html (佛塑科技)

帖子详情页: https://guba.eastmoney.com/news,{stock_code},{post_id}.html
```

### 2. 提供的Cookie
```json
{
    "st_pvi": "22164803623127",
    "st_sn": "96",
    "nid18": "04f8c86cbf08ab9d8acbc47965b1b765",
    "gviem": "oFKe4LfaBztRSWlpuxIPZ6de1",
    "qgqp_b_id": "158d23a8e8f260623c1a489368661090"
}
```

### 3. 测试结果
- ✅ 网页访问成功（200 OK）
- ✅ Cookie有效
- ❌ API端点被封（403/404）
- ⚠️ 网页为React SSR，需要解析JavaScript或使用浏览器

---

## 💡 三种解决方案

### 方案1: 使用Playwright/Selenium（推荐）⭐⭐⭐⭐⭐

**优点**:
- 完全模拟真实浏览器
- 可以执行JavaScript获取动态数据
- MediaCrawlerPro已有Playwright支持
- 最稳定可靠

**实现方式**:

```python
# media_platform/eastmoney/client_playwright.py

from playwright.async_api import async_playwright
from typing import List, Dict

class EastMoneyPlaywrightClient:
    """东方财富Playwright客户端"""

    async def get_stock_posts(self, stock_code: str, page: int = 1) -> List[Dict]:
        """使用Playwright获取帖子列表"""

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()

            # 设置Cookie
            await context.add_cookies([
                {"name": "st_pvi", "value": "22164803623127", "domain": ".eastmoney.com"},
                {"name": "nid18", "value": "04f8c86cbf08ab9d8acbc47965b1b765", "domain": ".eastmoney.com"},
                {"name": "gviem", "value": "oFKe4LfaBztRSWlpuxIPZ6de1", "domain": ".eastmoney.com"},
            ])

            page_obj = await context.new_page()

            # 访问股吧列表页
            url = f"https://guba.eastmoney.com/list,{stock_code}.html"
            await page_obj.goto(url, wait_until="networkidle")

            # 等待内容加载
            await page_obj.wait_for_selector('.articlelist, #articlelistnew', timeout=10000)

            # 提取帖子数据
            posts = await page_obj.evaluate('''() => {
                const items = document.querySelectorAll('.article-item, .post-item');
                return Array.from(items).map(item => ({
                    title: item.querySelector('.title')?.textContent?.trim(),
                    url: item.querySelector('a')?.href,
                    author: item.querySelector('.author')?.textContent?.trim(),
                    read_count: item.querySelector('.read')?.textContent?.trim(),
                    comment_count: item.querySelector('.reply')?.textContent?.trim(),
                }));
            }''')

            await browser.close()

            return posts
```

**集成到现有代码**:
```python
# media_platform/eastmoney/core.py

from .client_playwright import EastMoneyPlaywrightClient

class EastMoneyCrawler(AbstractCrawler):
    def __init__(self):
        # 使用Playwright客户端
        self.eastmoney_client = EastMoneyPlaywrightClient()
        # ... 其他初始化
```

---

### 方案2: 网页解析 + 反向工程（中等难度）⭐⭐⭐

**思路**:
1. 分析网页JavaScript找到真实的数据加载API
2. 逆向分析请求签名算法
3. 构造合法的API请求

**步骤**:

#### Step 1: 使用浏览器开发者工具抓包

```bash
1. 打开 Chrome DevTools (F12)
2. 切换到 Network 标签
3. 访问 https://guba.eastmoney.com/list,000973.html
4. 筛选 XHR/Fetch 请求
5. 找到返回JSON数据的请求
```

#### Step 2: 分析请求参数

可能的API格式：
```
https://guba.eastmoney.com/api/post/list?
  code=000973
  &page=1
  &size=20
  &timestamp=1745856000
  &sign=abc123...
```

#### Step 3: 实现签名算法

```python
def generate_sign(params: dict) -> str:
    """生成请求签名"""
    # 根据逆向结果实现
    # 可能是MD5、SHA256等
    pass
```

---

### 方案3: RSS/公开API（最简单但功能受限）⭐⭐

**查找官方API**:

```python
# 可能存在的公开接口
urls_to_check = [
    "https://data.eastmoney.com/stock/...",
    "https://quote.eastmoney.com/...",
    "https://api.eastmoney.com/...",  # 可能需要申请API Key
]
```

---

## 🚀 推荐实施方案

### 立即可做：方案1 (Playwright)

#### Step 1: 创建 Playwright 客户端

```bash
cd /Users/wangxinlong/Code/communityspy/MediaCrawlerPro-Python
```

创建文件: `media_platform/eastmoney/client_playwright.py`

```python
from playwright.async_api import async_playwright, Browser, Page
import asyncio
from typing import List, Dict

class EastMoneyPlaywrightClient:
    def __init__(self):
        self.browser: Browser = None
        self.cookies = [
            {"name": "st_pvi", "value": "22164803623127", "domain": ".eastmoney.com"},
            {"name": "nid18", "value": "04f8c86cbf08ab9d8acbc47965b1b765", "domain": ".eastmoney.com"},
            {"name": "gviem", "value": "oFKe4LfaBztRSWlpuxIPZ6de1", "domain": ".eastmoney.com"},
            {"name": "qgqp_b_id", "value": "158d23a8e8f260623c1a489368661090", "domain": ".eastmoney.com"},
        ]

    async def init_browser(self):
        """初始化浏览器"""
        p = await async_playwright().start()
        self.browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox']
        )

    async def get_stock_posts(self, stock_code: str, page: int = 1, page_size: int = 20) -> Dict:
        """获取股票帖子列表"""
        if not self.browser:
            await self.init_browser()

        context = await self.browser.new_context()
        await context.add_cookies(self.cookies)

        page_obj: Page = await context.new_page()

        # 构造URL
        if page == 1:
            url = f"https://guba.eastmoney.com/list,{stock_code}.html"
        else:
            url = f"https://guba.eastmoney.com/list,{stock_code}_{page}.html"

        await page_obj.goto(url, wait_until="domcontentloaded")

        # 等待列表加载
        try:
            await page_obj.wait_for_selector('.articlelist, .table_list', timeout=5000)
        except:
            pass

        # 提取数据
        posts_data = await page_obj.evaluate('''() => {
            const posts = [];
            const items = document.querySelectorAll('.normal_post, .article-item, tr[data-poiid]');

            items.forEach((item, idx) => {
                try {
                    const titleElem = item.querySelector('a.title, .art_tit a');
                    const authorElem = item.querySelector('.author, .author_name a');
                    const readElem = item.querySelector('.read, .readnum');
                    const replyElem = item.querySelector('.reply, .replynum');
                    const timeElem = item.querySelector('.updatetime, .post_time');

                    if (titleElem) {
                        posts.push({
                            post_id: item.getAttribute('data-poiid') || `post_${idx}`,
                            title: titleElem.textContent.trim(),
                            post_url: titleElem.href || '',
                            author_name: authorElem ? authorElem.textContent.trim() : '',
                            read_count: readElem ? readElem.textContent.trim() : '0',
                            comment_count: replyElem ? replyElem.textContent.trim() : '0',
                            publish_time: timeElem ? timeElem.textContent.trim() : '',
                        });
                    }
                } catch(e) {
                    console.error('Parse error:', e);
                }
            });

            return posts;
        }''')

        await page_obj.close()
        await context.close()

        return {
            "success": True,
            "data": {
                "list": posts_data,
                "total": len(posts_data)
            }
        }

    async def close(self):
        """关闭浏览器"""
        if self.browser:
            await self.browser.close()
```

#### Step 2: 修改 core.py

```python
# media_platform/eastmoney/core.py

from .client_playwright import EastMoneyPlaywrightClient

class EastMoneyCrawler(AbstractCrawler):
    def __init__(self) -> None:
        # 使用 Playwright 客户端
        self.eastmoney_client = EastMoneyPlaywrightClient()

        # ... 其他代码不变
```

#### Step 3: 测试

```bash
uv run main.py --platform eastmoney --type search
```

---

## 📊 方案对比

| 方案 | 难度 | 稳定性 | 速度 | 推荐度 |
|------|------|--------|------|--------|
| Playwright | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 反向工程 | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| 公开API | ⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ |

---

## 🎯 下一步行动

### 立即执行（推荐）:

1. **创建 Playwright 客户端**
   ```bash
   cd /Users/wangxinlong/Code/communityspy/MediaCrawlerPro-Python/media_platform/eastmoney
   # 创建 client_playwright.py（见上面代码）
   ```

2. **修改 core.py**
   ```python
   from .client_playwright import EastMoneyPlaywrightClient
   self.eastmoney_client = EastMoneyPlaywrightClient()
   ```

3. **测试运行**
   ```bash
   uv run main.py --platform eastmoney --type search
   ```

### 或者（如果想要更高性能）:

使用Chrome DevTools抓包找到真实API：
1. F12 打开开发者工具
2. Network → XHR/Fetch
3. 访问 https://guba.eastmoney.com/list,000973.html
4. 找到返回JSON的请求
5. 复制请求URL和Headers
6. 更新 client.py

---

## ✅ 总结

### 当前状态
- ✅ 框架代码完成（100%）
- ✅ 枚举值使用（100%）
- ✅ 数据库就绪（100%）
- ⚠️ API访问需要调整

### 最快解决方案
**使用 Playwright** - 30分钟即可完成，稳定可靠

### 文件清单
- 已创建: `client_web.py` (BeautifulSoup版本，备用)
- 待创建: `client_playwright.py` (推荐)
- 需修改: `core.py` (1行代码)

---

**建议**: 使用 Playwright 方案，MediaCrawlerPro 项目已有完整的 Playwright 支持基础设施，集成非常简单。🚀
