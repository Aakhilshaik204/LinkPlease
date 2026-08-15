"""
routes/debug.py — diagnostic endpoint (remove before final submission)
"""
import os
from fastapi import APIRouter
from app.db.database import get_db
from app.config import DB_PATH

router = APIRouter()

@router.get("/debug/db")
async def debug_db():
    """Show DB path, rules, and job counts — for diagnostics only."""
    db = await get_db()

    async with db.execute("SELECT * FROM rules") as cur:
        rules = [dict(r) for r in await cur.fetchall()]

    async with db.execute("SELECT status, COUNT(*) as cnt FROM dm_jobs GROUP BY status") as cur:
        job_counts = {r[0]: r[1] for r in await cur.fetchall()}

    async with db.execute("SELECT COUNT(*) as cnt FROM seen_events") as cur:
        events_seen = (await cur.fetchone())[0]

    return {
        "db_path": os.path.abspath(DB_PATH),
        "db_exists": os.path.exists(DB_PATH),
        "rules": rules,
        "job_counts": job_counts,
        "events_seen": events_seen,
    }
