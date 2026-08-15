"""
services/rule_matcher.py — matches comment text against all active rules.
Keyword matching is case-insensitive substring match.
"""
import logging
from app.db.database import get_db

logger = logging.getLogger(__name__)


async def match_rules(comment_text: str) -> list[dict]:
    db = await get_db()
    text_lower = comment_text.lower()

    async with db.execute("SELECT rule_id, keyword, dm_message FROM rules") as cursor:
        all_rules = await cursor.fetchall()

    logger.info("Matching %r against %d rule(s)", text_lower, len(all_rules))

    matched = []
    for row in all_rules:
        kw = row[1]  # keyword column
        if kw in text_lower:
            matched.append({
                "rule_id":    row[0],
                "keyword":    row[1],
                "dm_message": row[2],
            })
            logger.info("  ✅ Rule '%s' matched!", kw)

    return matched
