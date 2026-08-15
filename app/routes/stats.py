"""
routes/stats.py
────────────────
GET /stats — live metrics from the dm_jobs table.

Counts are sourced directly from SQLite so they survive restarts
and are accurate even under concurrent load.
"""
import logging
from fastapi import APIRouter
from app.db.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/stats")
async def get_stats():
    """
    Returns:
      sent              — DMs confirmed delivered by the mock API
      failed            — DMs where we gave up after max retries
      queued            — DMs waiting to send or waiting on retry
      duplicates_blocked — DMs we correctly chose NOT to send
                           (same user + same rule seen more than once)
    """
    db = await get_db()

    async with db.execute("""
        SELECT
            SUM(CASE WHEN status = 'delivered'  THEN 1 ELSE 0 END) AS sent,
            SUM(CASE WHEN status = 'failed'     THEN 1 ELSE 0 END) AS failed,
            SUM(CASE WHEN status IN ('queued', 'sending') THEN 1 ELSE 0 END) AS queued,
            SUM(CASE WHEN status = 'cancelled'  THEN 1 ELSE 0 END) AS cancelled
        FROM dm_jobs
    """) as cur:
        row = dict(await cur.fetchone())

    async with db.execute("SELECT COUNT(*) AS cnt FROM duplicate_blocks") as cur:
        dup_row = dict(await cur.fetchone())

    return {
        "sent": row["sent"] or 0,
        "failed": row["failed"] or 0,
        "queued": row["queued"] or 0,
        "duplicates_blocked": dup_row["cnt"] or 0,
    }
