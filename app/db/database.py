"""
db/database.py — aiosqlite connection with autocommit + schema init
"""
import aiosqlite
import asyncio
import sqlite3
from datetime import datetime, timezone
from app.config import DB_PATH

_db: aiosqlite.Connection | None = None
_lock = asyncio.Lock()


async def get_db() -> aiosqlite.Connection:
    global _db
    if _db is None:
        async with _lock:
            if _db is None:
                # isolation_level=None → autocommit mode
                # Every DML is immediately committed — no cross-coroutine
                # transaction interference, no lost commits on hot-reload.
                _db = await aiosqlite.connect(DB_PATH, isolation_level=None)
                _db.row_factory = sqlite3.Row
                await _db.execute("PRAGMA journal_mode=WAL")
                await _db.execute("PRAGMA synchronous=NORMAL")
                await init_schema(_db)
    return _db


async def close_db():
    global _db
    if _db:
        await _db.close()
        _db = None


async def init_schema(db: aiosqlite.Connection):
    """Create all tables if they don't exist."""
    statements = [
        """CREATE TABLE IF NOT EXISTS seen_events (
            event_id    TEXT PRIMARY KEY,
            received_at TEXT NOT NULL
        )""",
        """CREATE TABLE IF NOT EXISTS rules (
            rule_id     TEXT PRIMARY KEY,
            keyword     TEXT NOT NULL,
            dm_message  TEXT NOT NULL,
            created_at  TEXT NOT NULL
        )""",
        """CREATE TABLE IF NOT EXISTS dm_jobs (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            rule_id        TEXT NOT NULL,
            user_id        TEXT NOT NULL,
            username       TEXT,
            comment_id     TEXT NOT NULL,
            dm_id          TEXT,
            status         TEXT NOT NULL DEFAULT 'queued',
            attempts       INTEGER NOT NULL DEFAULT 0,
            next_retry_at  TEXT,
            created_at     TEXT NOT NULL,
            updated_at     TEXT NOT NULL,
            UNIQUE(rule_id, user_id)
        )""",
        """CREATE INDEX IF NOT EXISTS idx_dm_jobs_status
            ON dm_jobs(status, next_retry_at)""",
        """CREATE TABLE IF NOT EXISTS deleted_comments (
            comment_id TEXT PRIMARY KEY,
            deleted_at TEXT NOT NULL
        )""",
        """CREATE TABLE IF NOT EXISTS duplicate_blocks (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            rule_id    TEXT NOT NULL,
            user_id    TEXT NOT NULL,
            comment_id TEXT NOT NULL,
            blocked_at TEXT NOT NULL
        )""",
    ]
    for stmt in statements:
        await db.execute(stmt)
    # No commit needed — autocommit mode


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
