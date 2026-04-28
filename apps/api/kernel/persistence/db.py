"""SQLite 持久化基础设施 - 异步 + 连接池"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional


_SCHEMA_V2 = """
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    email TEXT,
    nickname TEXT,
    persona_branch TEXT DEFAULT 'main',
    created_at TEXT NOT NULL,
    metadata TEXT
);

CREATE TABLE IF NOT EXISTS user_api_keys (
    key_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    provider TEXT NOT NULL,
    encrypted_key BLOB NOT NULL,
    encrypted_at TEXT NOT NULL,
    revoked INTEGER DEFAULT 0,
    FOREIGN KEY(user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    project_id TEXT,
    started_at TEXT NOT NULL,
    ended_at TEXT,
    summary TEXT,
    FOREIGN KEY(user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS audit_log (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    trace_id TEXT,
    action TEXT NOT NULL,
    resource TEXT,
    timestamp TEXT NOT NULL,
    metadata TEXT
);

CREATE TABLE IF NOT EXISTS persona_vectors (
    vector_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    branch TEXT DEFAULT 'main',
    parent_branch TEXT,
    version INTEGER DEFAULT 1,
    embedding TEXT NOT NULL,
    dimensions TEXT NOT NULL,
    sample_count INTEGER DEFAULT 0,
    drift_score REAL DEFAULT 0.0,
    locked INTEGER DEFAULT 0,
    notes TEXT,
    last_updated TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_persona_user_branch ON persona_vectors(user_id, branch);

CREATE TABLE IF NOT EXISTS persona_samples (
    sample_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    content TEXT NOT NULL,
    platform TEXT,
    metrics TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS projects (
    project_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    created_at TEXT NOT NULL,
    metadata TEXT,
    FOREIGN KEY(user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS memory_entries (
    memory_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    project_id TEXT,
    session_id TEXT,
    layer TEXT NOT NULL CHECK(layer IN ('user', 'project', 'session', 'long_term', 'persona')),
    key TEXT NOT NULL,
    content TEXT NOT NULL,
    embedding TEXT,
    importance REAL DEFAULT 0.5,
    access_count INTEGER DEFAULT 0,
    last_accessed TEXT,
    created_at TEXT NOT NULL,
    expires_at TEXT,
    metadata TEXT,
    FOREIGN KEY(user_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_memory_user_layer ON memory_entries(user_id, layer);
CREATE INDEX IF NOT EXISTS idx_memory_session ON memory_entries(session_id);
CREATE INDEX IF NOT EXISTS idx_memory_project ON memory_entries(project_id);

CREATE TABLE IF NOT EXISTS event_log (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    aggregate_id TEXT NOT NULL,
    aggregate_type TEXT NOT NULL,
    event_type TEXT NOT NULL,
    payload TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    user_id TEXT,
    trace_id TEXT
);

CREATE INDEX IF NOT EXISTS idx_event_agg ON event_log(aggregate_type, aggregate_id);
CREATE INDEX IF NOT EXISTS idx_event_trace ON event_log(trace_id);

CREATE TABLE IF NOT EXISTS campaigns (
    campaign_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    project_id TEXT,
    theme TEXT NOT NULL,
    plan TEXT NOT NULL,
    flow_structure TEXT,
    created_at TEXT NOT NULL,
    status TEXT DEFAULT 'draft',
    FOREIGN KEY(user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS topics (
    topic_id TEXT PRIMARY KEY,
    user_id TEXT,
    title TEXT NOT NULL,
    category TEXT,
    confidence REAL DEFAULT 0.5,
    horizon_days INTEGER DEFAULT 7,
    risk_score REAL,
    potential_score REAL,
    metadata TEXT,
    created_at TEXT NOT NULL
);
"""


def get_db_path() -> Path:
    """获取主数据库路径 - 默认在 ~/.ripple/ripple.db"""
    p = Path.home() / ".ripple" / "ripple.db"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def init_db(db_path: Optional[Path] = None) -> Path:
    """初始化数据库 schema"""
    path = db_path or get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.executescript(_SCHEMA_V2)
        conn.commit()
    return path


def get_conn(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """获取连接 - 调用方负责 close 或用 with"""
    path = db_path or get_db_path()
    if not path.exists():
        init_db(path)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn
