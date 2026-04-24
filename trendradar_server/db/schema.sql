-- TrendRadar 数据库表设计
-- 版本: 1.0
-- 日期: 2026-04-23
-- 数据库: SQLite

-- ============================================
-- 1. 用户账户表
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT UNIQUE NOT NULL,           -- 用户唯一标识(Telegram ID/微信OpenID/UUID)
    username TEXT,                          -- 用户昵称
    email TEXT,                             -- 邮箱（可选）
    phone TEXT,                             -- 手机号（可选）

    -- 会员信息
    membership_type TEXT DEFAULT 'free',    -- 会员类型(free/basic/pro/enterprise)
    membership_status TEXT DEFAULT 'active', -- 会员状态(active/expired/cancelled)
    membership_start_date TEXT,             -- 会员开始日期 (ISO 8601)
    membership_end_date TEXT,               -- 会员到期日期 (ISO 8601)

    -- Token额度管理
    token_balance INTEGER DEFAULT 0,        -- 当前Token余额
    token_total_purchased INTEGER DEFAULT 0, -- 累计购买Token数
    token_total_consumed INTEGER DEFAULT 0,  -- 累计消耗Token数

    -- 额度限制（根据会员等级）
    max_subscriptions INTEGER DEFAULT 3,    -- 最大订阅数(free:3, basic:10, pro:50)
    max_daily_requests INTEGER DEFAULT 10,  -- 每日最大请求数

    -- 账户状态
    status TEXT DEFAULT 'active',           -- 账户状态(active/suspended/banned)

    -- 时间戳
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    last_login_at TEXT
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_users_user_id ON users(user_id);
CREATE INDEX IF NOT EXISTS idx_users_membership ON users(membership_type, membership_status);

-- ============================================
-- 2. 用户订阅表
-- ============================================
CREATE TABLE IF NOT EXISTS subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,                  -- 关联用户

    -- 订阅内容
    subscription_type TEXT NOT NULL,        -- 订阅类型(stock/topic/keyword/hashtag)
    target TEXT NOT NULL,                   -- 目标内容(股票代码/话题名/关键词)
    target_display_name TEXT,               -- 显示名称(如：特斯拉/TSLA)

    -- 数据源配置
    platforms TEXT NOT NULL,                -- 数据源平台(JSON数组: ["eastmoney", "xueqiu"])

    -- 推送配置
    push_channels TEXT NOT NULL,            -- 推送渠道(JSON数组: ["telegram", "wechat"])
    push_frequency TEXT DEFAULT 'realtime', -- 推送频率(realtime/hourly/daily/weekly)
    push_time TEXT,                         -- 定时推送时间(如: "09:00,18:00")

    -- 过滤条件（可选）
    filters TEXT,                           -- 过滤规则(JSON)

    -- 订阅状态
    status TEXT DEFAULT 'active',           -- 状态(active/paused/cancelled)
    last_crawl_at TEXT,                     -- 最后爬取时间
    last_push_at TEXT,                      -- 最后推送时间

    -- 时间戳
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_subscriptions_user ON subscriptions(user_id, status);
CREATE INDEX IF NOT EXISTS idx_subscriptions_target ON subscriptions(target, status);
CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions(status, push_frequency);

-- ============================================
-- 3. Token消耗记录表
-- ============================================
CREATE TABLE IF NOT EXISTS token_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,                  -- 关联用户
    subscription_id INTEGER,                -- 关联订阅（可选）

    -- 调用信息
    operation_type TEXT NOT NULL,           -- 操作类型(analyze/summarize/verify/chat)
    model TEXT NOT NULL,                    -- 使用模型(deepseek-chat/gpt-4等)

    -- Token统计
    prompt_tokens INTEGER NOT NULL DEFAULT 0,       -- 输入Token数
    completion_tokens INTEGER NOT NULL DEFAULT 0,   -- 输出Token数
    total_tokens INTEGER NOT NULL,                  -- 总Token数

    -- 成本计算
    cost_amount REAL DEFAULT 0,             -- 成本金额(元)

    -- 请求详情（可选）
    request_content TEXT,                   -- 请求内容摘要
    response_summary TEXT,                  -- 响应摘要

    -- 时间戳
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (subscription_id) REFERENCES subscriptions(id) ON DELETE SET NULL
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_token_usage_user ON token_usage(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_token_usage_date ON token_usage(created_at);

-- ============================================
-- 4. Token充值记录表
-- ============================================
CREATE TABLE IF NOT EXISTS token_purchases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,                  -- 关联用户

    -- 购买信息
    package_type TEXT NOT NULL,             -- 套餐类型(token_10k/token_100k/monthly_sub)
    token_amount INTEGER NOT NULL,          -- 购买Token数量
    price REAL NOT NULL,                    -- 支付金额(元)

    -- 支付信息
    payment_method TEXT,                    -- 支付方式(alipay/wechat/stripe)
    payment_status TEXT DEFAULT 'pending',  -- 支付状态(pending/completed/failed/refunded)
    transaction_id TEXT,                    -- 支付平台交易号

    -- 时间戳
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    paid_at TEXT,                           -- 支付完成时间

    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_token_purchases_user ON token_purchases(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_token_purchases_status ON token_purchases(payment_status);

-- ============================================
-- 5. 会员订单表
-- ============================================
CREATE TABLE IF NOT EXISTS membership_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,                  -- 关联用户

    -- 订单信息
    membership_type TEXT NOT NULL,          -- 会员类型(basic/pro/enterprise)
    duration_months INTEGER NOT NULL,       -- 购买时长(月)
    price REAL NOT NULL,                    -- 支付金额(元)

    -- 支付信息
    payment_method TEXT,                    -- 支付方式
    payment_status TEXT DEFAULT 'pending',  -- 支付状态
    transaction_id TEXT,                    -- 交易号

    -- 生效信息
    start_date TEXT,                        -- 生效日期
    end_date TEXT,                          -- 到期日期
    is_active INTEGER DEFAULT 0,            -- 是否当前生效(0/1)

    -- 时间戳
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    paid_at TEXT,
    activated_at TEXT,

    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_membership_orders_user ON membership_orders(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_membership_orders_active ON membership_orders(is_active, end_date);

-- ============================================
-- 6. 任务队列表
-- ============================================
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_type TEXT NOT NULL,                -- 任务类型(crawl/analyze/push)
    platform TEXT NOT NULL,                 -- 平台名称
    target TEXT NOT NULL,                   -- 爬取目标
    priority INTEGER DEFAULT 5,             -- 优先级(1-10)
    status TEXT DEFAULT 'pending',          -- 状态(pending/running/completed/failed)
    progress INTEGER DEFAULT 0,             -- 进度(0-100)
    result TEXT,                            -- 结果(JSON)
    error TEXT,                             -- 错误信息
    retry_count INTEGER DEFAULT 0,          -- 重试次数
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    started_at TEXT,
    completed_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status, priority DESC);

-- ============================================
-- 7. 原始数据表（通用设计）
-- ============================================
CREATE TABLE IF NOT EXISTS raw_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT NOT NULL,                 -- 平台(eastmoney/xueqiu/zhihu...)
    data_type TEXT NOT NULL,                -- 数据类型(post/comment/reply/article)
    target TEXT NOT NULL,                   -- 关联目标(股票代码/话题ID)
    content_id TEXT NOT NULL,               -- 原始内容ID
    parent_id TEXT,                         -- 父内容ID
    author_id TEXT,                         -- 作者ID
    author_name TEXT,                       -- 作者昵称
    content TEXT NOT NULL,                  -- 内容
    publish_time TEXT,                      -- 发布时间
    metrics TEXT,                           -- 指标(JSON)
    raw_json TEXT,                          -- 原始JSON数据
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(platform, content_id)
);

CREATE INDEX IF NOT EXISTS idx_raw_data_target ON raw_data(target, publish_time DESC);
CREATE INDEX IF NOT EXISTS idx_raw_data_platform ON raw_data(platform, data_type);

-- ============================================
-- 8. AI分析结果表
-- ============================================
CREATE TABLE IF NOT EXISTS analysis_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subscription_id INTEGER,                -- 关联订阅
    target TEXT NOT NULL,                   -- 分析目标
    analysis_type TEXT NOT NULL,            -- 分析类型(sentiment/summary/verification)
    data_range TEXT NOT NULL,               -- 数据范围(last_1h/last_24h/custom)
    summary TEXT,                           -- AI摘要
    sentiment TEXT,                         -- 情感分析(positive/negative/neutral)
    keywords TEXT,                          -- 关键词(JSON数组)
    insights TEXT,                          -- 核心洞察(JSON数组)
    token_usage INTEGER,                    -- Token消耗
    model TEXT,                             -- 使用模型
    confidence REAL,                        -- 置信度(0-1)
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (subscription_id) REFERENCES subscriptions(id)
);

CREATE INDEX IF NOT EXISTS idx_analysis_target ON analysis_results(target, created_at DESC);

-- ============================================
-- 9. 推送记录表
-- ============================================
CREATE TABLE IF NOT EXISTS push_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subscription_id INTEGER NOT NULL,
    channel TEXT NOT NULL,                  -- 推送渠道
    content TEXT NOT NULL,                  -- 推送内容
    status TEXT DEFAULT 'pending',          -- 状态(pending/sent/failed)
    sent_at TEXT,
    error TEXT,

    FOREIGN KEY (subscription_id) REFERENCES subscriptions(id)
);

CREATE INDEX IF NOT EXISTS idx_push_history_subscription ON push_history(subscription_id, created_at DESC);
