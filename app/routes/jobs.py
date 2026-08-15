"""
routes/jobs.py
───────────────
GET /jobs — paginated DM job listing for the admin dashboard
"""
from fastapi import APIRouter, Query
from app.db.database import get_db

router = APIRouter()


@router.get("/jobs")
async def list_jobs(limit: int = Query(50, le=200), offset: int = Query(0, ge=0)):
    """Return recent DM jobs for the admin dashboard."""
    db = await get_db()

    async with db.execute("SELECT COUNT(*) AS cnt FROM dm_jobs") as cur:
        total = (await cur.fetchone())["cnt"]

    async with db.execute(
        """SELECT id, rule_id, user_id, username, comment_id, dm_id,
                  status, attempts, created_at, updated_at
           FROM dm_jobs
           ORDER BY updated_at DESC
           LIMIT ? OFFSET ?""",
        (limit, offset),
    ) as cur:
        items = [dict(r) for r in await cur.fetchall()]

    return {"total": total, "items": items}
