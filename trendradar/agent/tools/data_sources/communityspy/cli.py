#!/usr/bin/env python3
"""
CommunitySpy CLI - 命令行工具

独立运行的脚本，可以直接调用爬虫功能
"""

import argparse
import json
from pathlib import Path
from spider import EastMoneyCommentSpider


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="CommunitySpy - 东方财富股吧评论爬虫"
    )

    parser.add_argument(
        "stock_code",
        help="股票代码，例如：301293"
    )

    parser.add_argument(
        "--max-pages",
        type=int,
        default=10,
        help="最大爬取页数（默认：10）"
    )

    parser.add_argument(
        "--max-posts",
        type=int,
        default=100,
        help="最大爬取帖子数（默认：100）"
    )

    parser.add_argument(
        "--no-comments",
        action="store_true",
        help="不爬取评论"
    )

    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="请求延迟（秒，默认：1.0）"
    )

    parser.add_argument(
        "--db-path",
        help="数据库文件路径（默认：eastmoney_{stock_code}.db）"
    )

    parser.add_argument(
        "--output",
        help="输出结果到JSON文件"
    )

    args = parser.parse_args()

    # 创建爬虫实例
    print(f"开始爬取股票 {args.stock_code} 的数据...")
    print(f"参数：max_pages={args.max_pages}, max_posts={args.max_posts}")

    with EastMoneyCommentSpider(args.stock_code, args.db_path) as spider:
        # 执行爬取
        stats = spider.crawl(
            max_pages=args.max_pages,
            max_posts=args.max_posts,
            include_comments=not args.no_comments,
            delay=args.delay
        )

        # 打印结果
        print("\n爬取完成！")
        print(f"- 帖子数量：{stats['posts_count']}")
        print(f"- 评论数量：{stats['comments_count']}")
        print(f"- 数据库路径：{spider.db_path}")

        if stats['errors']:
            print(f"- 错误数量：{len(stats['errors'])}")
            for error in stats['errors'][:5]:
                print(f"  * {error}")

        # 保存到JSON文件
        if args.output:
            output_path = Path(args.output)
            result = {
                "stock_code": args.stock_code,
                "stats": stats,
                "db_path": spider.db_path
            }

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            print(f"\n结果已保存到：{output_path}")


if __name__ == "__main__":
    main()
