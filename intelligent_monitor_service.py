#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能股票监控服务
用户输入自然语言描述 → AI理解 → 引导配置 → 多Agent协作 → 生成报告推送
"""

import asyncio
import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
from enum import Enum

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import httpx

# 添加项目路径
import sys
sys.path.insert(0, str(Path(__file__).parent))

from trendradar.crawler.eastmoney import crawl_eastmoney_stock


# ============================================================================
# 枚举定义
# ============================================================================

class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"           # 等待配置
    CONFIGURING = "configuring"   # 配置中
    ACTIVE = "active"             # 运行中
    PAUSED = "paused"             # 暂停
    COMPLETED = "completed"       # 完成
    FAILED = "failed"             # 失败


class AnalysisType(str, Enum):
    """分析类型"""
    SENTIMENT = "sentiment"           # 情绪统计
    BULL_BEAR = "bull_bear"          # 看多看空
    QUALITY_POSTS = "quality_posts"   # 有价值的评论
    ACTIVE_USERS = "active_users"    # 活跃用户
    HOT_TOPICS = "hot_topics"        # 热门话题


class Platform(str, Enum):
    """平台"""
    EASTMONEY = "eastmoney"  # 东方财富
    ZHIHU = "zhihu"          # 知乎
    WEIBO = "weibo"          # 微博
    XUEQIU = "xueqiu"        # 雪球


# ============================================================================
# 数据模型
# ============================================================================

class UserRequest(BaseModel):
    """用户请求"""
    user_id: str
    description: str
    webhook_url: str
    webhook_type: str = "generic"


class TaskConfiguration(BaseModel):
    """任务配置"""
    task_id: str
    stock_code: str
    analysis_types: List[AnalysisType]
    platforms: List[Platform]
    interval: int = 300


class TaskInfo(BaseModel):
    """任务信息"""
    task_id: str
    user_id: str
    stock_code: str
    description: str
    status: TaskStatus
    analysis_types: List[str]
    platforms: List[str]
    webhook_url: str
    created_at: str
    last_report_time: Optional[str] = None


# ============================================================================
# AI意图识别
# ============================================================================

class IntentRecognizer:
    """意图识别器 - 解析用户自然语言"""

    @staticmethod
    async def parse_user_intent(description: str) -> Dict:
        """
        解析用户意图

        实际应该调用LLM，这里简化处理
        """
        # TODO: 接入真实的LLM（如GPT/Claude）
        # 这里用简单规则模拟

        result = {
            "intent": "monitor_stock",
            "entities": {},
            "suggested_analysis": [],
            "suggested_platforms": []
        }

        # 提取股票代码（支持中文环境）
        import re
        stock_match = re.search(r'(\d{6})', description)
        if stock_match:
            result["entities"]["stock_code"] = stock_match.group(1)

        # 识别关注点
        keywords_map = {
            "情绪": AnalysisType.SENTIMENT,
            "看多": AnalysisType.BULL_BEAR,
            "看空": AnalysisType.BULL_BEAR,
            "评论": AnalysisType.QUALITY_POSTS,
            "有价值": AnalysisType.QUALITY_POSTS,
            "活跃": AnalysisType.ACTIVE_USERS,
            "话题": AnalysisType.HOT_TOPICS,
        }

        for keyword, analysis_type in keywords_map.items():
            if keyword in description:
                if analysis_type not in result["suggested_analysis"]:
                    result["suggested_analysis"].append(analysis_type)

        # 默认推荐
        if not result["suggested_analysis"]:
            result["suggested_analysis"] = [
                AnalysisType.SENTIMENT,
                AnalysisType.BULL_BEAR,
                AnalysisType.QUALITY_POSTS
            ]

        # 识别平台（暂时只支持东方财富）
        result["suggested_platforms"] = [Platform.EASTMONEY]

        return result


# ============================================================================
# 任务配置引导
# ============================================================================

class ConfigurationGuide:
    """配置引导 - 引导用户完成任务配置"""

    @staticmethod
    def generate_options(intent: Dict) -> Dict:
        """生成配置选项"""
        return {
            "stock_code": intent["entities"].get("stock_code", ""),
            "analysis_options": [
                {
                    "id": AnalysisType.SENTIMENT,
                    "name": "情绪统计",
                    "description": "分析讨论区的整体情绪（积极、消极、中性）",
                    "recommended": AnalysisType.SENTIMENT in intent["suggested_analysis"]
                },
                {
                    "id": AnalysisType.BULL_BEAR,
                    "name": "看多看空比例",
                    "description": "统计看多和看空的声音占比",
                    "recommended": AnalysisType.BULL_BEAR in intent["suggested_analysis"]
                },
                {
                    "id": AnalysisType.QUALITY_POSTS,
                    "name": "有价值的评论",
                    "description": "筛选出有理论、有依据、有结论的高质量分析",
                    "recommended": AnalysisType.QUALITY_POSTS in intent["suggested_analysis"]
                },
                {
                    "id": AnalysisType.ACTIVE_USERS,
                    "name": "活跃用户分析",
                    "description": "识别频繁发帖的用户，警惕可能的水军",
                    "recommended": False
                },
                {
                    "id": AnalysisType.HOT_TOPICS,
                    "name": "热门话题",
                    "description": "提取讨论最多的话题和关键词",
                    "recommended": False
                }
            ],
            "platform_options": [
                {
                    "id": Platform.EASTMONEY,
                    "name": "东方财富股吧",
                    "description": "散户聚集地，讨论活跃",
                    "available": True,
                    "recommended": True
                },
                {
                    "id": Platform.ZHIHU,
                    "name": "知乎",
                    "description": "专业分析较多",
                    "available": False,  # 暂未实现
                    "recommended": False
                },
                {
                    "id": Platform.WEIBO,
                    "name": "微博",
                    "description": "热点传播快",
                    "available": False,
                    "recommended": False
                }
            ]
        }


# ============================================================================
# 爬虫Agent
# ============================================================================

class CrawlerAgent:
    """爬虫Agent - 负责数据采集"""

    @staticmethod
    async def crawl_platform(platform: Platform, stock_code: str) -> Dict:
        """爬取指定平台的数据"""
        if platform == Platform.EASTMONEY:
            result = await crawl_eastmoney_stock(
                stock_code=stock_code,
                max_pages=3,
                enable_comments=True,
                max_comments_per_post=50
            )
            return {
                "platform": platform,
                "stock_code": stock_code,
                "success": True,
                "data": result
            }
        else:
            return {
                "platform": platform,
                "stock_code": stock_code,
                "success": False,
                "error": "平台暂未实现"
            }


# ============================================================================
# 分析Agent
# ============================================================================

class AnalysisAgent:
    """分析Agent - 负责数据分析"""

    @staticmethod
    def analyze_sentiment(posts: List, comments: List) -> Dict:
        """情绪分析"""
        # 简化的关键词匹配
        positive_keywords = ["好", "涨", "牛", "看好", "机会", "利好"]
        negative_keywords = ["跌", "空", "看空", "风险", "利空", "套牢"]

        positive_count = 0
        negative_count = 0
        neutral_count = 0

        all_texts = [p['title'] for p in posts] + [c['content'] for c in comments]

        for text in all_texts:
            pos_score = sum(1 for k in positive_keywords if k in text)
            neg_score = sum(1 for k in negative_keywords if k in text)

            if pos_score > neg_score:
                positive_count += 1
            elif neg_score > pos_score:
                negative_count += 1
            else:
                neutral_count += 1

        total = len(all_texts)

        return {
            "type": "sentiment",
            "total": total,
            "positive": {
                "count": positive_count,
                "percentage": round(positive_count / total * 100, 2) if total > 0 else 0
            },
            "negative": {
                "count": negative_count,
                "percentage": round(negative_count / total * 100, 2) if total > 0 else 0
            },
            "neutral": {
                "count": neutral_count,
                "percentage": round(neutral_count / total * 100, 2) if total > 0 else 0
            }
        }

    @staticmethod
    def analyze_bull_bear(posts: List, comments: List) -> Dict:
        """看多看空分析"""
        bullish_keywords = ["看多", "看好", "上涨", "涨", "买入", "持有"]
        bearish_keywords = ["看空", "看衰", "下跌", "跌", "卖出", "减仓"]

        bullish_count = 0
        bearish_count = 0

        all_texts = [p['title'] for p in posts] + [c['content'] for c in comments]

        for text in all_texts:
            if any(k in text for k in bullish_keywords):
                bullish_count += 1
            if any(k in text for k in bearish_keywords):
                bearish_count += 1

        total = bullish_count + bearish_count

        return {
            "type": "bull_bear",
            "bullish": {
                "count": bullish_count,
                "percentage": round(bullish_count / total * 100, 2) if total > 0 else 0
            },
            "bearish": {
                "count": bearish_count,
                "percentage": round(bearish_count / total * 100, 2) if total > 0 else 0
            },
            "sentiment": "看多占优" if bullish_count > bearish_count else "看空占优" if bearish_count > bullish_count else "多空均衡"
        }

    @staticmethod
    def analyze_quality_posts(posts: List) -> Dict:
        """高质量帖子分析"""
        quality_keywords = {
            "theory": ["原理", "逻辑", "原因", "理论"],
            "evidence": ["数据", "财报", "业绩", "营收"],
            "conclusion": ["因此", "所以", "综上", "预计"]
        }

        quality_posts = []

        for post in posts:
            title = post['title']
            score = 0
            features = []

            if any(k in title for k in quality_keywords['theory']):
                score += 1
                features.append("有理论")

            if any(k in title for k in quality_keywords['evidence']):
                score += 1
                features.append("有依据")

            if any(k in title for k in quality_keywords['conclusion']):
                score += 1
                features.append("有结论")

            if score >= 2:
                quality_posts.append({
                    "title": title,
                    "author": post['author_name'],
                    "comment_count": post['comment_count'],
                    "read_count": post['read_count'],
                    "score": score,
                    "features": features
                })

        quality_posts.sort(key=lambda x: x['score'], reverse=True)

        return {
            "type": "quality_posts",
            "total_posts": len(posts),
            "quality_count": len(quality_posts),
            "percentage": round(len(quality_posts) / len(posts) * 100, 2) if posts else 0,
            "top_posts": quality_posts[:5]
        }

    @staticmethod
    def analyze_active_users(posts: List, comments: List) -> Dict:
        """活跃用户分析"""
        from collections import Counter

        post_authors = [p['author_name'] for p in posts]
        comment_authors = [c['author_name'] for c in comments]

        all_authors = post_authors + comment_authors
        author_counts = Counter(all_authors)

        # 筛选活跃用户（发帖+评论 >= 3）
        active_users = [
            {"user": author, "count": count}
            for author, count in author_counts.most_common()
            if count >= 3
        ]

        return {
            "type": "active_users",
            "threshold": 3,
            "active_user_count": len(active_users),
            "top_users": active_users[:10]
        }

    @staticmethod
    async def run_analysis(data: Dict, analysis_types: List[AnalysisType]) -> List[Dict]:
        """运行指定的分析"""
        posts = data['posts']
        comments = data['comments']
        results = []

        for analysis_type in analysis_types:
            if analysis_type == AnalysisType.SENTIMENT:
                results.append(AnalysisAgent.analyze_sentiment(posts, comments))
            elif analysis_type == AnalysisType.BULL_BEAR:
                results.append(AnalysisAgent.analyze_bull_bear(posts, comments))
            elif analysis_type == AnalysisType.QUALITY_POSTS:
                results.append(AnalysisAgent.analyze_quality_posts(posts))
            elif analysis_type == AnalysisType.ACTIVE_USERS:
                results.append(AnalysisAgent.analyze_active_users(posts, comments))

        return results


# ============================================================================
# 报告生成
# ============================================================================

class ReportGenerator:
    """报告生成器"""

    @staticmethod
    def generate_report(stock_code: str, platform_data: List, analysis_results: List) -> str:
        """生成Markdown报告"""
        report = f"# 📊 股票 {stock_code} 智能监控报告\n\n"
        report += f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        report += "---\n\n"

        # 数据概况
        report += "## 📈 数据概况\n\n"
        for platform_result in platform_data:
            if platform_result['success']:
                data = platform_result['data']
                report += f"### {platform_result['platform'].upper()}\n"
                report += f"- 帖子数: {data['posts_count']}\n"
                report += f"- 评论数: {data['comments_count']}\n\n"

        # 分析结果
        report += "## 🔍 智能分析\n\n"

        for result in analysis_results:
            if result['type'] == 'sentiment':
                report += "### 😊 情绪统计\n\n"
                report += f"- 积极: {result['positive']['count']} ({result['positive']['percentage']}%)\n"
                report += f"- 消极: {result['negative']['count']} ({result['negative']['percentage']}%)\n"
                report += f"- 中性: {result['neutral']['count']} ({result['neutral']['percentage']}%)\n\n"

            elif result['type'] == 'bull_bear':
                report += "### 📊 看多看空\n\n"
                report += f"- 看多: {result['bullish']['count']} ({result['bullish']['percentage']}%)\n"
                report += f"- 看空: {result['bearish']['count']} ({result['bearish']['percentage']}%)\n"
                report += f"- **市场情绪**: {result['sentiment']}\n\n"

            elif result['type'] == 'quality_posts':
                report += "### ⭐ 有价值的评论\n\n"
                report += f"发现 {result['quality_count']} 条高质量帖子 ({result['percentage']}%)\n\n"
                for i, post in enumerate(result['top_posts'], 1):
                    report += f"{i}. **{post['title'][:60]}**\n"
                    report += f"   - 作者: {post['author']} | 特征: {', '.join(post['features'])}\n"
                    report += f"   - 评论: {post['comment_count']} | 阅读: {post['read_count']}\n\n"

            elif result['type'] == 'active_users':
                report += "### 👥 活跃用户\n\n"
                report += f"发现 {result['active_user_count']} 个活跃用户（发帖/评论 ≥ {result['threshold']}）\n\n"
                for i, user in enumerate(result['top_users'][:5], 1):
                    report += f"{i}. {user['user']}: {user['count']}条\n"
                report += "\n"

        report += "---\n\n"
        report += "*本报告由AI智能生成*\n"

        return report


# ============================================================================
# 任务管理
# ============================================================================

class TaskManager:
    """任务管理器"""

    def __init__(self, db_path: str = "tasks.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                stock_code TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'pending',
                analysis_types TEXT,
                platforms TEXT,
                webhook_url TEXT,
                webhook_type TEXT DEFAULT 'generic',
                interval INTEGER DEFAULT 300,
                last_report_time TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()

    def create_task(self, user_id: str, description: str, webhook_url: str, webhook_type: str = "generic") -> str:
        """创建任务"""
        import uuid
        task_id = f"task_{uuid.uuid4().hex[:12]}"

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO tasks (task_id, user_id, stock_code, description, webhook_url, webhook_type, status)
            VALUES (?, ?, ?, ?, ?, ?, 'pending')
        """, (task_id, user_id, "", description, webhook_url, webhook_type))

        conn.commit()
        conn.close()

        return task_id

    def configure_task(self, task_id: str, config: TaskConfiguration):
        """配置任务"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE tasks
            SET stock_code=?, analysis_types=?, platforms=?, interval=?, status='active'
            WHERE task_id=?
        """, (
            config.stock_code,
            json.dumps([a.value for a in config.analysis_types]),
            json.dumps([p.value for p in config.platforms]),
            config.interval,
            task_id
        ))

        conn.commit()
        conn.close()

    def get_task(self, task_id: str) -> Optional[Dict]:
        """获取任务"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM tasks WHERE task_id=?", (task_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return dict(row)
        return None

    def get_active_tasks(self) -> List[Dict]:
        """获取所有活跃任务"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM tasks WHERE status='active'")
        tasks = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return tasks

    def update_report_time(self, task_id: str):
        """更新报告时间"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE tasks SET last_report_time=? WHERE task_id=?
        """, (datetime.now().isoformat(), task_id))

        conn.commit()
        conn.close()


# ============================================================================
# FastAPI应用
# ============================================================================

app = FastAPI(title="智能股票监控服务", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局对象
task_manager = TaskManager()
intent_recognizer = IntentRecognizer()
crawler_agent = CrawlerAgent()
analysis_agent = AnalysisAgent()


# ============================================================================
# API路由
# ============================================================================

@app.post("/api/v2/create_task")
async def create_monitoring_task(request: UserRequest):
    """
    步骤1: 用户输入自然语言，创建监控任务
    """
    # 解析意图
    intent = await intent_recognizer.parse_user_intent(request.description)

    # 创建任务
    task_id = task_manager.create_task(
        user_id=request.user_id,
        description=request.description,
        webhook_url=request.webhook_url,
        webhook_type=request.webhook_type
    )

    # 生成配置选项
    options = ConfigurationGuide.generate_options(intent)

    return {
        "task_id": task_id,
        "intent": intent,
        "configuration_options": options,
        "next_step": "请调用 /api/v2/configure_task 完成配置"
    }


@app.post("/api/v2/configure_task")
async def configure_task(config: TaskConfiguration, background_tasks: BackgroundTasks):
    """
    步骤2: 用户选择分析维度和平台，完成任务配置
    """
    # 保存配置
    task_manager.configure_task(config.task_id, config)

    # 立即执行一次
    background_tasks.add_task(execute_monitoring_task, config.task_id)

    return {
        "success": True,
        "message": "任务已激活，正在进行首次采集分析...",
        "task_id": config.task_id
    }


@app.get("/api/v2/task/{task_id}")
async def get_task_info(task_id: str):
    """查询任务信息"""
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task


@app.post("/api/v2/trigger/{task_id}")
async def trigger_task(task_id: str, background_tasks: BackgroundTasks):
    """手动触发任务执行"""
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    background_tasks.add_task(execute_monitoring_task, task_id)
    return {"message": "任务已触发"}


# ============================================================================
# 核心执行逻辑
# ============================================================================

async def execute_monitoring_task(task_id: str):
    """执行监控任务 - 完整流程"""
    print(f"🚀 开始执行任务: {task_id}")

    # 1. 获取任务配置
    task = task_manager.get_task(task_id)
    if not task:
        print(f"❌ 任务不存在: {task_id}")
        return

    stock_code = task['stock_code']
    analysis_types = [AnalysisType(a) for a in json.loads(task['analysis_types'])]
    platforms = [Platform(p) for p in json.loads(task['platforms'])]

    print(f"📊 股票: {stock_code}")
    print(f"📝 分析类型: {[a.value for a in analysis_types]}")
    print(f"🌐 平台: {[p.value for p in platforms]}")

    # 2. 爬虫Agent采集数据
    print("\n🕷️ 爬虫Agent开始采集...")
    platform_data = []
    for platform in platforms:
        result = await crawler_agent.crawl_platform(platform, stock_code)
        platform_data.append(result)
        print(f"  ✅ {platform.value}: {result['data']['posts_count']}帖 + {result['data']['comments_count']}评")

    # 3. 分析Agent进行分析
    print("\n🔍 分析Agent开始分析...")
    all_analysis_results = []
    for platform_result in platform_data:
        if platform_result['success']:
            analysis_results = await analysis_agent.run_analysis(
                platform_result['data'],
                analysis_types
            )
            all_analysis_results.extend(analysis_results)
            print(f"  ✅ 完成 {len(analysis_results)} 项分析")

    # 4. 生成报告
    print("\n📄 生成报告...")
    report = ReportGenerator.generate_report(stock_code, platform_data, all_analysis_results)

    # 5. 推送
    print("\n📬 推送报告...")
    await send_webhook_notification(
        webhook_url=task['webhook_url'],
        webhook_type=task['webhook_type'],
        content=report,
        title=f"股票 {stock_code} 智能监控报告"
    )

    # 6. 更新任务
    task_manager.update_report_time(task_id)

    print(f"✅ 任务执行完成: {task_id}\n")


async def send_webhook_notification(webhook_url: str, webhook_type: str, content: str, title: str):
    """发送Webhook通知"""
    async with httpx.AsyncClient() as client:
        try:
            if webhook_type == "feishu":
                data = {
                    "msg_type": "interactive",
                    "card": {
                        "header": {"title": {"tag": "plain_text", "content": title}},
                        "elements": [{"tag": "markdown", "content": content}]
                    }
                }
            else:
                data = {"title": title, "content": content}

            await client.post(webhook_url, json=data, timeout=10)
            print(f"  ✅ 推送成功")
        except Exception as e:
            print(f"  ❌ 推送失败: {e}")


# ============================================================================
# 监控循环
# ============================================================================

async def monitoring_loop():
    """监控循环"""
    print("⏰ 智能监控循环已启动")

    while True:
        try:
            tasks = task_manager.get_active_tasks()
            now = datetime.now()

            for task in tasks:
                last_report = task['last_report_time']
                interval = task['interval']

                should_execute = False
                if not last_report:
                    should_execute = True
                else:
                    last_time = datetime.fromisoformat(last_report)
                    if (now - last_time).total_seconds() >= interval:
                        should_execute = True

                if should_execute:
                    print(f"\n⏰ 定时触发任务: {task['task_id']}")
                    await execute_monitoring_task(task['task_id'])

        except Exception as e:
            print(f"❌ 监控循环出错: {e}")

        await asyncio.sleep(60)


@app.on_event("startup")
async def startup_event():
    """启动监控循环"""
    asyncio.create_task(monitoring_loop())


# ============================================================================
# 启动服务
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("🤖 智能股票监控服务 v2.0")
    print("=" * 80)
    print("工作流程:")
    print("  1️⃣  用户输入自然语言描述")
    print("  2️⃣  AI理解意图并生成配置选项")
    print("  3️⃣  用户选择分析维度和平台")
    print("  4️⃣  爬虫Agent多平台采集数据")
    print("  5️⃣  分析Agent智能分析")
    print("  6️⃣  生成结构化报告")
    print("  7️⃣  Webhook推送给用户")
    print("=" * 80)
    print("API地址: http://localhost:8000")
    print("API文档: http://localhost:8000/docs")
    print("=" * 80)

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
