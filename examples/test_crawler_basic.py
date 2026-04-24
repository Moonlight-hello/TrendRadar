# coding=utf-8
"""
爬虫系统基础测试

演示如何使用新的爬虫系统
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from trendradar.crawler import (
    # 服务层
    CrawlerService,

    # 基础设施层
    DataRepository,
    CrawlExecutor,
    TaskManager,

    # 适配器层
    NewsNowAdapter,

    # 类型
    QueryParams,
    Platform,
    QueryType,
    TimeRange,
    CacheStrategy,
)


def create_crawler_service(db_path: str = "./data/crawler_test.db") -> CrawlerService:
    """
    创建爬虫服务

    Args:
        db_path: 数据库路径

    Returns:
        配置好的爬虫服务
    """
    # 1. 创建数据仓库
    repository = DataRepository(db_path)

    # 2. 创建爬虫执行器
    executor = CrawlExecutor()

    # 3. 注册适配器
    newsnow_adapter = NewsNowAdapter()
    executor.register_adapter(newsnow_adapter)

    # 4. 创建任务管理器
    task_manager = TaskManager(
        repository=repository,
        executor=executor,
        max_workers=3
    )

    # 5. 创建爬虫服务
    service = CrawlerService(
        repository=repository,
        executor=executor,
        task_manager=task_manager
    )

    return service


def test_sync_query():
    """测试同步查询"""
    print("\n" + "="*60)
    print("测试1: 同步查询知乎热榜")
    print("="*60)

    service = create_crawler_service()

    # 构造查询参数
    params = QueryParams(
        platform=Platform.ZHIHU,
        query_type=QueryType.TRENDING,
        limit=10,
        time_range=TimeRange.LAST_24H,
        cache_strategy=CacheStrategy.AUTO,
    )

    print(f"\n查询参数:")
    print(f"  平台: {params.platform}")
    print(f"  类型: {params.query_type}")
    print(f"  数量: {params.limit}")
    print(f"  时间范围: {params.time_range}")
    print(f"  缓存策略: {params.cache_strategy}")

    # 执行查询
    result = service.query(params)

    # 输出结果
    print(f"\n查询结果:")
    print(f"  成功: {result.success}")
    print(f"  来源: {'缓存' if result.from_cache else '实时爬取'}")
    print(f"  数量: {result.count}")
    print(f"  消息: {result.message}")

    if result.success and result.items:
        print(f"\n前5条数据:")
        for item in result.items[:5]:
            rank = item.extra.get('rank', '?')
            print(f"  {rank}. {item.title[:50]}")

    return result


def test_cache_hit():
    """测试缓存命中"""
    print("\n" + "="*60)
    print("测试2: 缓存命中")
    print("="*60)

    service = create_crawler_service()

    params = QueryParams(
        platform=Platform.WEIBO,
        query_type=QueryType.TRENDING,
        limit=5,
    )

    # 第一次查询（应该爬取）
    print("\n第一次查询（预期：实时爬取）")
    result1 = service.query(params)
    print(f"  来源: {'缓存' if result1.from_cache else '实时爬取'}")
    print(f"  数量: {result1.count}")

    # 第二次查询（应该命中缓存）
    print("\n第二次查询（预期：缓存命中）")
    result2 = service.query(params)
    print(f"  来源: {'缓存' if result2.from_cache else '实时爬取'}")
    print(f"  数量: {result2.count}")

    # 验证
    assert result2.from_cache, "第二次查询应该命中缓存"
    print("\n✅ 缓存功能正常")


def test_force_refresh():
    """测试强制刷新"""
    print("\n" + "="*60)
    print("测试3: 强制刷新（忽略缓存）")
    print("="*60)

    service = create_crawler_service()

    params = QueryParams(
        platform=Platform.BILIBILI,
        query_type=QueryType.TRENDING,
        limit=5,
        cache_strategy=CacheStrategy.FORCE_REFRESH,
    )

    print("\n使用 FORCE_REFRESH 策略")
    result = service.query(params)
    print(f"  来源: {'缓存' if result.from_cache else '实时爬取'}")
    print(f"  数量: {result.count}")

    assert not result.from_cache, "FORCE_REFRESH 不应该使用缓存"
    print("\n✅ 强制刷新功能正常")


def test_supported_platforms():
    """测试支持的平台"""
    print("\n" + "="*60)
    print("测试4: 查看支持的平台")
    print("="*60)

    service = create_crawler_service()

    platforms = service.executor.get_supported_platforms()
    print(f"\n支持的平台 ({len(platforms)}):")
    for platform in platforms:
        query_types = service.executor.get_supported_query_types(platform)
        print(f"  - {platform}: {[str(qt) for qt in query_types]}")


def test_stats():
    """测试统计信息"""
    print("\n" + "="*60)
    print("测试5: 统计信息")
    print("="*60)

    service = create_crawler_service()

    stats = service.get_stats()
    print(f"\n统计数据:")
    print(f"  缓存:")
    print(f"    总数: {stats['cache']['total']}")
    print(f"    有效: {stats['cache']['valid']}")
    print(f"    过期: {stats['cache']['expired']}")
    print(f"  任务: {stats['tasks']}")


def main():
    """运行所有测试"""
    print("开始测试爬虫系统...")

    try:
        # 基础测试
        test_sync_query()

        # 缓存测试
        test_cache_hit()

        # 强制刷新测试
        test_force_refresh()

        # 支持的平台
        test_supported_platforms()

        # 统计信息
        test_stats()

        print("\n" + "="*60)
        print("✅ 所有测试通过")
        print("="*60)

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
