-- Ripple 数据库初始化脚本
-- 创建 pgvector 扩展和基础表

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 租户表
CREATE TABLE IF NOT EXISTS tenants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    plan TEXT NOT NULL DEFAULT 'free',
    daily_token_budget BIGINT NOT NULL DEFAULT 100000,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    email TEXT UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'koc',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- KOC 灵感库
CREATE TABLE IF NOT EXISTS inspirations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    source TEXT,  -- web/mobile/desktop/miniprogram
    media_url TEXT,
    embedding vector(1536),
    tags TEXT[],
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_inspirations_tenant_user ON inspirations(tenant_id, user_id);
CREATE INDEX IF NOT EXISTS idx_inspirations_embedding ON inspirations
    USING hnsw (embedding vector_cosine_ops);

-- KOC 历史作品库
CREATE TABLE IF NOT EXISTS koc_works (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    content TEXT,
    platform TEXT NOT NULL,  -- channels/wechat/xhs/douyin/bilibili/weibo
    metrics JSONB,  -- {views, likes, comments, shares, saves}
    embedding vector(1536),
    published_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_koc_works_tenant_user ON koc_works(tenant_id, user_id);

-- 早期信号快照(Oracle Agent 输出)
CREATE TABLE IF NOT EXISTS signal_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    topic TEXT NOT NULL,
    sources JSONB NOT NULL,  -- {polymarket: 0.7, weibo: 0.5, ...}
    confidence REAL NOT NULL,
    horizon_days INTEGER NOT NULL DEFAULT 7,
    explanation TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_signals_tenant_time ON signal_snapshots(tenant_id, created_at DESC);

-- Agent 运行历史
CREATE TABLE IF NOT EXISTS agent_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    thread_id TEXT NOT NULL,
    agent_name TEXT NOT NULL,
    state JSONB NOT NULL,
    terminal_reason TEXT,
    tokens_used BIGINT NOT NULL DEFAULT 0,
    cost_usd NUMERIC(10, 6) NOT NULL DEFAULT 0,
    duration_ms INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agent_runs_tenant_thread ON agent_runs(tenant_id, thread_id);

-- BYOK API Keys (加密存储)
CREATE TABLE IF NOT EXISTS user_api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider TEXT NOT NULL,  -- minimax/hunyuan/deepseek/openai/...
    encrypted_key BYTEA NOT NULL,
    api_base TEXT,
    default_model TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 启用 Row-Level Security
ALTER TABLE inspirations ENABLE ROW LEVEL SECURITY;
ALTER TABLE koc_works ENABLE ROW LEVEL SECURITY;
ALTER TABLE signal_snapshots ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_api_keys ENABLE ROW LEVEL SECURITY;

-- 租户隔离策略
CREATE POLICY tenant_isolation_inspirations ON inspirations
    USING (tenant_id = current_setting('app.tenant_id', TRUE)::uuid);
CREATE POLICY tenant_isolation_koc_works ON koc_works
    USING (tenant_id = current_setting('app.tenant_id', TRUE)::uuid);
CREATE POLICY tenant_isolation_signals ON signal_snapshots
    USING (tenant_id = current_setting('app.tenant_id', TRUE)::uuid);
CREATE POLICY tenant_isolation_agent_runs ON agent_runs
    USING (tenant_id = current_setting('app.tenant_id', TRUE)::uuid);
CREATE POLICY tenant_isolation_api_keys ON user_api_keys
    USING (tenant_id = current_setting('app.tenant_id', TRUE)::uuid);

-- 默认开发租户和用户
INSERT INTO tenants (id, name, plan)
VALUES ('00000000-0000-0000-0000-000000000001', 'Default Dev Tenant', 'pro')
ON CONFLICT DO NOTHING;
