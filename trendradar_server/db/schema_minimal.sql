-- TrendRadar 极简版数据库设计
-- 仅保留核心功能：用户身份识别 + 个性化订阅

-- ============================================
-- 1. 用户表（极简版）
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT UNIQUE NOT NULL,           -- 用户唯一标识
    username TEXT,                          -- 昵称（可选）
    channel TEXT NOT NULL,                  -- 注册渠道(telegram/wechat/web/anonymous)

    -- 渠道特定信息
    telegram_id TEXT,                       -- Telegram ID
    telegram_username TEXT,                 -- Telegram用户名
    wechat_openid TEXT,                     -- 微信OpenID

    -- 状态
    status TEXT DEFAULT 'active',           -- 账户状态(active/inactive)

    -- 时间戳
    created_at TEXT,
    last_active_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_users_user_id ON users(user_id);
CREATE INDEX IF NOT EXISTS idx_users_telegram ON users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_users_wechat ON users(wechat_openid);

-- ============================================
-- 2. 订阅表（个性化内容）
-- ============================================
CREATE TABLE IF NOT EXISTS subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,                  -- 关联用户

    -- 订阅内容
    subscription_type TEXT NOT NULL,        -- 订阅类型(stock/keyword/topic/hashtag)
    target TEXT NOT NULL,                   -- 目标内容(股票代码/关键词)
    target_display_name TEXT,               -- 显示名称

    -- 数据源
    platforms TEXT NOT NULL,                -- 数据源平台(JSON: ["eastmoney", "xueqiu"])

    -- 推送设置
    push_enabled INTEGER DEFAULT 1,         -- 是否推送(0/1)
    push_channels TEXT NOT NULL,            -- 推送渠道(JSON: ["telegram"])
    push_frequency TEXT DEFAULT 'realtime', -- 推送频率(realtime/daily)

    -- 状态
    status TEXT DEFAULT 'active',           -- 订阅状态(active/paused)
    last_push_at TEXT,                      -- 最后推送时间

    -- 时间戳
    created_at TEXT,
    updated_at TEXT,

    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_subscriptions_user ON subscriptions(user_id, status);
CREATE INDEX IF NOT EXISTS idx_subscriptions_target ON subscriptions(target);

-- ============================================
-- 3. 推送历史表
-- ============================================
CREATE TABLE IF NOT EXISTS push_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subscription_id INTEGER NOT NULL,
    user_id TEXT NOT NULL,

    -- 推送内容
    channel TEXT NOT NULL,                  -- 推送渠道(telegram/wechat)
    title TEXT,                             -- 标题
    content TEXT NOT NULL,                  -- 内容

    -- 状态
    status TEXT DEFAULT 'pending',          -- 状态(pending/sent/failed)
    sent_at TEXT,
    error TEXT,

    FOREIGN KEY (subscription_id) REFERENCES subscriptions(id),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_push_history_user ON push_history(user_id, sent_at DESC);

-- ============================================
-- 4. 原始数据表（通用）
-- ============================================
CREATE TABLE IF NOT EXISTS raw_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT NOT NULL,                 -- 平台(eastmoney/xueqiu)
    data_type TEXT NOT NULL,                -- 数据类型(post/comment)
    target TEXT NOT NULL,                   -- 关联目标(股票代码)
    content_id TEXT NOT NULL,               -- 内容ID

    -- 内容
    author_name TEXT,
    content TEXT NOT NULL,
    publish_time TEXT,

    -- 指标
    metrics TEXT,                           -- JSON格式

    -- 原始数据
    raw_json TEXT,

    created_at TEXT,

    UNIQUE(platform, content_id)
);

CREATE INDEX IF NOT EXISTS idx_raw_data_target ON raw_data(target, publish_time DESC);
CREATE INDEX IF NOT EXISTS idx_raw_data_platform ON raw_data(platform, data_type);

-- ============================================
-- 5. AI分析结果表
-- ============================================
CREATE TABLE IF NOT EXISTS analysis_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subscription_id INTEGER,
    target TEXT NOT NULL,

    -- 分析内容
    summary TEXT,                           -- AI摘要
    sentiment TEXT,                         -- 情感(positive/negative/neutral)
    keywords TEXT,                          -- 关键词(JSON数组)

    -- 时间
    data_range TEXT NOT NULL,               -- 数据范围(last_1h/last_24h)
    created_at TEXT,

    FOREIGN KEY (subscription_id) REFERENCES subscriptions(id)
);

CREATE INDEX IF NOT EXISTS idx_analysis_target ON analysis_results(target, created_at DESC);
