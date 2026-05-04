"""SQLite storage layer for distilled skills, content history, and preferences."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import aiosqlite

from core.config import DB_PATH

log = logging.getLogger(__name__)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS skills (
    id          TEXT PRIMARY KEY,
    blogger     TEXT NOT NULL,
    domain      TEXT NOT NULL DEFAULT '',
    skill_json  TEXT NOT NULL,
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS content_history (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    topic       TEXT NOT NULL,
    score       REAL,
    content     TEXT NOT NULL,
    platform    TEXT NOT NULL DEFAULT 'xiaohongshu',
    skill_id    TEXT,
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS user_prefs (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


async def _get_db() -> aiosqlite.Connection:
    db = await aiosqlite.connect(str(DB_PATH))
    db.row_factory = aiosqlite.Row
    await db.executescript(_SCHEMA)
    return db


async def save_skill(skill_id: str, blogger: str, domain: str, skill: dict) -> None:
    db = await _get_db()
    try:
        await db.execute(
            "INSERT OR REPLACE INTO skills (id, blogger, domain, skill_json, created_at) VALUES (?, ?, ?, ?, ?)",
            (skill_id, blogger, domain, json.dumps(skill, ensure_ascii=False), _now()),
        )
        await db.commit()
    finally:
        await db.close()


async def get_skill(skill_id: str) -> dict | None:
    db = await _get_db()
    try:
        cur = await db.execute("SELECT skill_json FROM skills WHERE id = ?", (skill_id,))
        row = await cur.fetchone()
        return json.loads(row["skill_json"]) if row else None
    finally:
        await db.close()


async def list_skills() -> list[dict]:
    db = await _get_db()
    try:
        cur = await db.execute("SELECT id, blogger, domain, created_at FROM skills ORDER BY created_at DESC")
        rows = await cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        await db.close()


async def save_content(topic: str, score: float | None, content: str, platform: str, skill_id: str | None) -> int:
    db = await _get_db()
    try:
        cur = await db.execute(
            "INSERT INTO content_history (topic, score, content, platform, skill_id, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (topic, score, content, platform, skill_id, _now()),
        )
        await db.commit()
        return cur.lastrowid  # type: ignore[return-value]
    finally:
        await db.close()


async def get_pref(key: str, default: str = "") -> str:
    db = await _get_db()
    try:
        cur = await db.execute("SELECT value FROM user_prefs WHERE key = ?", (key,))
        row = await cur.fetchone()
        return row["value"] if row else default
    finally:
        await db.close()


async def set_pref(key: str, value: str) -> None:
    db = await _get_db()
    try:
        await db.execute("INSERT OR REPLACE INTO user_prefs (key, value) VALUES (?, ?)", (key, value))
        await db.commit()
    finally:
        await db.close()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
