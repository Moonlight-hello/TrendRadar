-- TrendRadar 简化数据库表设计
-- 使用兼容的SQL语法

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT UNIQUE NOT NULL,
    username TEXT,
    email TEXT,
    phone TEXT,
    membership_type TEXT DEFAULT 'free',
    membership_status TEXT DEFAULT 'active',
    membership_start_date TEXT,
    membership_end_date TEXT,
    token_balance INTEGER DEFAULT 0,
    token_total_purchased INTEGER DEFAULT 0,
    token_total_consumed INTEGER DEFAULT 0,
    max_subscriptions INTEGER DEFAULT 3,
    max_daily_requests INTEGER DEFAULT 10,
    status TEXT DEFAULT 'active',
    created_at TEXT,
    updated_at TEXT,
    last_login_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_users_user_id ON users(user_id);

CREATE TABLE IF NOT EXISTS subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    subscription_type TEXT NOT NULL,
    target TEXT NOT NULL,
    target_display_name TEXT,
    platforms TEXT NOT NULL,
    push_channels TEXT NOT NULL,
    push_frequency TEXT DEFAULT 'realtime',
    push_time TEXT,
    filters TEXT,
    status TEXT DEFAULT 'active',
    last_crawl_at TEXT,
    last_push_at TEXT,
    created_at TEXT,
    updated_at TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_subscriptions_user ON subscriptions(user_id, status);

CREATE TABLE IF NOT EXISTS token_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    subscription_id INTEGER,
    operation_type TEXT NOT NULL,
    model TEXT NOT NULL,
    prompt_tokens INTEGER DEFAULT 0,
    completion_tokens INTEGER DEFAULT 0,
    total_tokens INTEGER NOT NULL,
    cost_amount REAL DEFAULT 0,
    request_content TEXT,
    response_summary TEXT,
    created_at TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_token_usage_user ON token_usage(user_id);

CREATE TABLE IF NOT EXISTS token_purchases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    package_type TEXT NOT NULL,
    token_amount INTEGER NOT NULL,
    price REAL NOT NULL,
    payment_method TEXT,
    payment_status TEXT DEFAULT 'pending',
    transaction_id TEXT,
    created_at TEXT,
    paid_at TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS membership_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    membership_type TEXT NOT NULL,
    duration_months INTEGER NOT NULL,
    price REAL NOT NULL,
    payment_method TEXT,
    payment_status TEXT DEFAULT 'pending',
    transaction_id TEXT,
    start_date TEXT,
    end_date TEXT,
    is_active INTEGER DEFAULT 0,
    created_at TEXT,
    paid_at TEXT,
    activated_at TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);
