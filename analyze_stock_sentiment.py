#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票情绪分析脚本
分析东方财富股吧的评论和帖子，提供：
1. 多账号发帖检测
2. 看多/看空情绪占比
3. 有质量的分析帖子识别（有理论、有依据、有结论）
"""

import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Tuple


class StockSentimentAnalyzer:
    """股票情绪分析器"""

    # 看多关键词
    BULLISH_KEYWORDS = [
        "看多", "看好", "上涨", "涨", "牛", "买入", "加仓", "持有", "坚定",
        "突破", "拉升", "利好", "机会", "潜力", "业绩", "增长", "盈利",
        "翻倍", "暴涨", "大涨", "反弹", "起飞", "火箭", "冲"
    ]

    # 看空关键词
    BEARISH_KEYWORDS = [
        "看空", "看衰", "下跌", "跌", "熊", "卖出", "减仓", "空仓", "观望",
        "破位", "跳水", "利空", "风险", "亏损", "下行", "暴跌", "大跌",
        "割肉", "套牢", "被套", "跑路", "撤"
    ]

    # 质量分析帖子的特征词
    QUALITY_KEYWORDS = {
        "theory": ["原理", "逻辑", "原因", "因为", "理论", "机制", "模式", "根本"],
        "evidence": ["数据", "财报", "业绩", "营收", "利润", "增长率", "市盈率", "PE", "ROE", "毛利率"],
        "conclusion": ["因此", "所以", "综上", "总结", "预计", "预期", "判断", "建议"]
    }

    def __init__(self, data_file: str):
        """
        初始化分析器

        Args:
            data_file: JSON数据文件路径
        """
        self.data_file = Path(data_file)
        self.data = self._load_data()

    def _load_data(self) -> Dict:
        """加载数据"""
        with open(self.data_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def detect_multiple_accounts(self, threshold: int = 3) -> Dict:
        """
        检测多账号发帖

        Args:
            threshold: 发帖数阈值，超过此数量的用户会被标记

        Returns:
            多账号检测结果
        """
        # 统计帖子作者
        post_authors = Counter([post['author_name'] for post in self.data['posts']])

        # 统计评论作者
        comment_authors = Counter([comment['author_name'] for comment in self.data['comments']])

        # 合并统计
        all_authors = post_authors + comment_authors

        # 找出活跃用户
        active_users = {
            author: count
            for author, count in all_authors.items()
            if count >= threshold
        }

        # 详细分析活跃用户
        user_details = {}
        for author in active_users:
            posts = [p for p in self.data['posts'] if p['author_name'] == author]
            comments = [c for c in self.data['comments'] if c['author_name'] == author]

            user_details[author] = {
                "total_count": active_users[author],
                "post_count": len(posts),
                "comment_count": len(comments),
                "posts": [p['title'] for p in posts[:5]],  # 最多展示5条
                "comments": [c['content'][:50] + "..." if len(c['content']) > 50 else c['content']
                           for c in comments[:5]]
            }

        return {
            "threshold": threshold,
            "active_user_count": len(active_users),
            "active_users": dict(sorted(user_details.items(),
                                       key=lambda x: x[1]['total_count'],
                                       reverse=True))
        }

    def _calculate_sentiment_score(self, text: str) -> Tuple[int, int]:
        """
        计算文本的情绪得分

        Args:
            text: 文本内容

        Returns:
            (看多得分, 看空得分)
        """
        bullish_score = sum(1 for keyword in self.BULLISH_KEYWORDS if keyword in text)
        bearish_score = sum(1 for keyword in self.BEARISH_KEYWORDS if keyword in text)
        return bullish_score, bearish_score

    def analyze_sentiment(self) -> Dict:
        """
        分析看多/看空情绪占比

        Returns:
            情绪分析结果
        """
        total_bullish = 0
        total_bearish = 0
        neutral = 0

        bullish_items = []
        bearish_items = []

        # 分析帖子
        for post in self.data['posts']:
            text = post['title']
            bullish_score, bearish_score = self._calculate_sentiment_score(text)

            if bullish_score > bearish_score:
                total_bullish += 1
                bullish_items.append({
                    "type": "post",
                    "author": post['author_name'],
                    "content": text,
                    "score": bullish_score - bearish_score
                })
            elif bearish_score > bullish_score:
                total_bearish += 1
                bearish_items.append({
                    "type": "post",
                    "author": post['author_name'],
                    "content": text,
                    "score": bearish_score - bullish_score
                })
            else:
                neutral += 1

        # 分析评论
        for comment in self.data['comments']:
            text = comment['content']
            bullish_score, bearish_score = self._calculate_sentiment_score(text)

            if bullish_score > bearish_score:
                total_bullish += 1
                bullish_items.append({
                    "type": "comment",
                    "author": comment['author_name'],
                    "content": text[:100] + "..." if len(text) > 100 else text,
                    "score": bullish_score - bearish_score
                })
            elif bearish_score > bullish_score:
                total_bearish += 1
                bearish_items.append({
                    "type": "comment",
                    "author": comment['author_name'],
                    "content": text[:100] + "..." if len(text) > 100 else text,
                    "score": bearish_score - bullish_score
                })
            else:
                neutral += 1

        total = total_bullish + total_bearish + neutral

        return {
            "total": total,
            "bullish": {
                "count": total_bullish,
                "percentage": round(total_bullish / total * 100, 2) if total > 0 else 0,
                "top_items": sorted(bullish_items, key=lambda x: x['score'], reverse=True)[:10]
            },
            "bearish": {
                "count": total_bearish,
                "percentage": round(total_bearish / total * 100, 2) if total > 0 else 0,
                "top_items": sorted(bearish_items, key=lambda x: x['score'], reverse=True)[:10]
            },
            "neutral": {
                "count": neutral,
                "percentage": round(neutral / total * 100, 2) if total > 0 else 0
            }
        }

    def _check_quality(self, text: str) -> Dict:
        """
        检查文本是否包含高质量分析的特征

        Args:
            text: 文本内容

        Returns:
            质量检查结果
        """
        has_theory = any(keyword in text for keyword in self.QUALITY_KEYWORDS['theory'])
        has_evidence = any(keyword in text for keyword in self.QUALITY_KEYWORDS['evidence'])
        has_conclusion = any(keyword in text for keyword in self.QUALITY_KEYWORDS['conclusion'])

        score = sum([has_theory, has_evidence, has_conclusion])

        return {
            "has_theory": has_theory,
            "has_evidence": has_evidence,
            "has_conclusion": has_conclusion,
            "score": score,
            "is_quality": score >= 2  # 至少包含两个要素
        }

    def identify_quality_posts(self, min_length: int = 50) -> Dict:
        """
        识别有质量的分析帖子

        Args:
            min_length: 最小文本长度

        Returns:
            质量帖子识别结果
        """
        quality_posts = []

        for post in self.data['posts']:
            text = post['title']

            # 过滤太短的帖子
            if len(text) < min_length:
                continue

            quality = self._check_quality(text)

            if quality['is_quality']:
                quality_posts.append({
                    "title": text,
                    "author": post['author_name'],
                    "comment_count": post['comment_count'],
                    "read_count": post['read_count'],
                    "publish_time": post['publish_time'],
                    "quality_score": quality['score'],
                    "has_theory": quality['has_theory'],
                    "has_evidence": quality['has_evidence'],
                    "has_conclusion": quality['has_conclusion']
                })

        # 按质量分数和评论数排序
        quality_posts.sort(key=lambda x: (x['quality_score'], x['comment_count']), reverse=True)

        return {
            "total_posts": len(self.data['posts']),
            "quality_post_count": len(quality_posts),
            "percentage": round(len(quality_posts) / len(self.data['posts']) * 100, 2) if self.data['posts'] else 0,
            "quality_posts": quality_posts
        }

    def generate_report(self) -> Dict:
        """
        生成完整的分析报告

        Returns:
            完整分析报告
        """
        return {
            "stock_code": self.data['stock_code'],
            "data_summary": {
                "posts_count": self.data['posts_count'],
                "comments_count": self.data['comments_count']
            },
            "multiple_accounts": self.detect_multiple_accounts(threshold=3),
            "sentiment_analysis": self.analyze_sentiment(),
            "quality_posts": self.identify_quality_posts(min_length=30)
        }

    def print_report(self):
        """打印分析报告"""
        report = self.generate_report()

        print("\n" + "=" * 80)
        print(f"📊 股票情绪分析报告 - {report['stock_code']}")
        print("=" * 80)

        # 数据概况
        print(f"\n📈 数据概况:")
        print(f"   - 帖子数: {report['data_summary']['posts_count']}")
        print(f"   - 评论数: {report['data_summary']['comments_count']}")

        # 多账号检测
        print(f"\n👥 多账号检测 (阈值: {report['multiple_accounts']['threshold']}条):")
        print(f"   - 活跃用户数: {report['multiple_accounts']['active_user_count']}")

        if report['multiple_accounts']['active_users']:
            print(f"\n   Top 10 活跃用户:")
            for i, (author, details) in enumerate(list(report['multiple_accounts']['active_users'].items())[:10], 1):
                print(f"   {i}. {author}: {details['total_count']}条 (帖子:{details['post_count']}, 评论:{details['comment_count']})")

        # 情绪分析
        sentiment = report['sentiment_analysis']
        print(f"\n💭 情绪分析:")
        print(f"   - 看多: {sentiment['bullish']['count']}条 ({sentiment['bullish']['percentage']}%)")
        print(f"   - 看空: {sentiment['bearish']['count']}条 ({sentiment['bearish']['percentage']}%)")
        print(f"   - 中性: {sentiment['neutral']['count']}条 ({sentiment['neutral']['percentage']}%)")

        # 情绪倾向
        if sentiment['bullish']['percentage'] > sentiment['bearish']['percentage']:
            sentiment_tendency = f"看多占优 (高出 {sentiment['bullish']['percentage'] - sentiment['bearish']['percentage']:.2f}%)"
        elif sentiment['bearish']['percentage'] > sentiment['bullish']['percentage']:
            sentiment_tendency = f"看空占优 (高出 {sentiment['bearish']['percentage'] - sentiment['bullish']['percentage']:.2f}%)"
        else:
            sentiment_tendency = "多空均衡"
        print(f"   - 情绪倾向: {sentiment_tendency}")

        # 最强看多
        if sentiment['bullish']['top_items']:
            print(f"\n   🔥 最强看多 (Top 5):")
            for i, item in enumerate(sentiment['bullish']['top_items'][:5], 1):
                print(f"   {i}. [{item['type']}] {item['author']}: {item['content'][:60]}...")

        # 最强看空
        if sentiment['bearish']['top_items']:
            print(f"\n   ❄️  最强看空 (Top 5):")
            for i, item in enumerate(sentiment['bearish']['top_items'][:5], 1):
                print(f"   {i}. [{item['type']}] {item['author']}: {item['content'][:60]}...")

        # 质量帖子
        quality = report['quality_posts']
        print(f"\n⭐ 质量分析帖子:")
        print(f"   - 质量帖子数: {quality['quality_post_count']}/{quality['total_posts']} ({quality['percentage']}%)")

        if quality['quality_posts']:
            print(f"\n   Top 10 质量帖子 (有理论、有依据、有结论):")
            for i, post in enumerate(quality['quality_posts'][:10], 1):
                indicators = []
                if post['has_theory']:
                    indicators.append("理论")
                if post['has_evidence']:
                    indicators.append("依据")
                if post['has_conclusion']:
                    indicators.append("结论")

                print(f"   {i}. [{'/'.join(indicators)}] {post['title'][:60]}...")
                print(f"      作者:{post['author']} | 评论:{post['comment_count']} | 阅读:{post['read_count']}")

        print("\n" + "=" * 80)


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="股票情绪分析工具")
    parser.add_argument("--file", "-f", type=str, required=True, help="数据文件路径")
    parser.add_argument("--save", "-s", type=str, help="保存分析报告到文件")

    args = parser.parse_args()

    # 分析
    analyzer = StockSentimentAnalyzer(args.file)

    # 打印报告
    analyzer.print_report()

    # 保存报告
    if args.save:
        report = analyzer.generate_report()
        with open(args.save, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\n✅ 分析报告已保存到: {args.save}")


if __name__ == "__main__":
    main()
