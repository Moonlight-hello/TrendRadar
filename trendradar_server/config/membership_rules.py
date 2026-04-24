"""
会员等级规则配置
"""

# 会员等级配置
MEMBERSHIP_TIERS = {
    'free': {
        'name': '免费版',
        'price_monthly': 0,
        'price_yearly': 0,
        'initial_tokens': 10000,            # 注册赠送
        'monthly_tokens': 0,                # 每月续送
        'max_subscriptions': 3,             # 最多3个订阅
        'max_daily_requests': 10,           # 每天10次分析
        'platforms': ['eastmoney'],         # 仅支持东方财富
        'push_channels': ['telegram'],      # 仅Telegram推送
        'features': [
            '基础数据爬取',
            '简单AI摘要',
            'Telegram推送'
        ]
    },
    'basic': {
        'name': '基础会员',
        'price_monthly': 29.9,
        'price_yearly': 299,                # 年付优惠
        'initial_tokens': 0,
        'monthly_tokens': 100000,           # 每月100k tokens
        'max_subscriptions': 10,
        'max_daily_requests': 100,
        'platforms': ['eastmoney', 'xueqiu', 'zhihu'],
        'push_channels': ['telegram', 'wechat', 'feishu'],
        'features': [
            '多平台爬取(东财/雪球/知乎)',
            '深度AI分析',
            '情感分析',
            '历史数据查询(7天)',
            '多渠道推送'
        ]
    },
    'pro': {
        'name': '专业会员',
        'price_monthly': 99.9,
        'price_yearly': 999,
        'initial_tokens': 0,
        'monthly_tokens': 500000,           # 每月500k tokens
        'max_subscriptions': 50,
        'max_daily_requests': 1000,
        'platforms': ['all'],               # 支持所有平台
        'push_channels': ['all'],
        'features': [
            '全平台支持',
            'AI对话功能',
            '数据导出(CSV/Excel)',
            'API接口访问',
            '历史数据查询(90天)',
            '优先级爬取',
            '自定义过滤规则'
        ]
    },
    'enterprise': {
        'name': '企业版',
        'price_monthly': 999,
        'price_yearly': 9999,
        'initial_tokens': 0,
        'monthly_tokens': 9999999,
        'max_subscriptions': 999,
        'max_daily_requests': 9999,
        'platforms': ['all'],
        'push_channels': ['all'],
        'features': [
            '私有化部署',
            '定制爬虫开发',
            '专属AI模型',
            '无限订阅数',
            '技术支持',
            '数据定制分析',
            'SLA保障'
        ]
    }
}

# Token成本配置（每1k tokens的价格，人民币元）
TOKEN_COSTS = {
    'deepseek-chat': 0.001,         # DeepSeek: 0.001元/1k tokens
    'gpt-3.5-turbo': 0.014,         # GPT-3.5: 0.014元/1k tokens
    'gpt-4': 0.21,                  # GPT-4: 0.21元/1k tokens
    'gpt-4-turbo': 0.07,            # GPT-4 Turbo: 0.07元/1k tokens
    'claude-3-sonnet': 0.021,       # Claude 3 Sonnet
    'claude-3-opus': 0.105,         # Claude 3 Opus
}

# Token充值套餐
TOKEN_PACKAGES = {
    'token_10k': {
        'name': '1万Token',
        'amount': 10000,
        'price': 2,
        'discount': 0
    },
    'token_50k': {
        'name': '5万Token',
        'amount': 50000,
        'price': 8,
        'discount': 0.2          # 8折
    },
    'token_100k': {
        'name': '10万Token',
        'amount': 100000,
        'price': 15,
        'discount': 0.25         # 75折
    },
    'token_500k': {
        'name': '50万Token',
        'amount': 500000,
        'price': 60,
        'discount': 0.4          # 6折
    },
}

def get_membership_config(membership_type: str) -> dict:
    """获取会员配置"""
    return MEMBERSHIP_TIERS.get(membership_type, MEMBERSHIP_TIERS['free'])

def calculate_token_cost(model: str, total_tokens: int) -> float:
    """计算Token成本"""
    cost_per_1k = TOKEN_COSTS.get(model, 0.01)  # 默认0.01元/1k tokens
    return (total_tokens / 1000) * cost_per_1k

def check_membership_limit(user_info: dict, action: str) -> tuple[bool, str]:
    """
    检查用户是否超过会员限制

    Args:
        user_info: 用户信息字典
        action: 操作类型(add_subscription/daily_request)

    Returns:
        (是否允许, 错误信息)
    """
    membership_type = user_info.get('membership_type', 'free')
    config = get_membership_config(membership_type)

    if action == 'add_subscription':
        current_count = user_info.get('subscription_count', 0)
        if current_count >= config['max_subscriptions']:
            return False, f"已达到{config['name']}最大订阅数限制({config['max_subscriptions']})"

    elif action == 'daily_request':
        daily_count = user_info.get('daily_request_count', 0)
        if daily_count >= config['max_daily_requests']:
            return False, f"今日请求已达上限({config['max_daily_requests']})"

    return True, ""
