"""
routes/rules.py — POST /rules, GET /rules, DELETE /rules/{id}
"""
import uuid
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator
from app.db.database import get_db, now_iso

logger = logging.getLogger(__name__)
router = APIRouter()


class RuleCreate(BaseModel):
    keyword: str
    dm_message: str

    @field_validator("keyword")
    @classmethod
    def keyword_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("keyword must not be empty")
        return v.lower()

    @field_validator("dm_message")
    @classmethod
    def message_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("dm_message must not be empty")
        return v


@router.post("/rules", status_code=201)
async def create_rule(body: RuleCreate):
    rule_id = f"rule_{uuid.uuid4().hex[:12]}"
    db = await get_db()
    await db.execute(
        "INSERT INTO rules (rule_id, keyword, dm_message, created_at) VALUES (?, ?, ?, ?)",
        (rule_id, body.keyword, body.dm_message, now_iso()),
    )
    # autocommit — immediately on disk
    logger.info("✅ Rule created: %s keyword=%s", rule_id, body.keyword)
    return {"rule_id": rule_id, "keyword": body.keyword, "dm_message": body.dm_message}


@router.get("/rules")
async def list_rules():
    db = await get_db()
    async with db.execute(
        "SELECT rule_id, keyword, dm_message, created_at FROM rules ORDER BY created_at DESC"
    ) as cur:
        rows = await cur.fetchall()
    return [{"rule_id": r[0], "keyword": r[1], "dm_message": r[2], "created_at": r[3]} for r in rows]


@router.delete("/rules/{rule_id}", status_code=204)
async def delete_rule(rule_id: str):
    db = await get_db()
    result = await db.execute("DELETE FROM rules WHERE rule_id = ?", (rule_id,))
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Rule not found")
