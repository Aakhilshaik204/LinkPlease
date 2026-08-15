"""
worker.py — background DM sender + delivery reconciler + DB cleanup
"""
import asyncio
import logging
import random
from datetime import datetime, timezone, timedelta

import httpx

from app.config import (
    DM_MAX_ATTEMPTS, DM_BASE_BACKOFF_SECONDS,
    RECONCILE_INTERVAL_SECONDS, WORKER_CONCURRENCY,
)
from app.db.database import get_db, now_iso
from app.services.dm_sender import (
    send_dm, get_dm_status,
    RateLimitedError, TransientError, PermanentError,
)
from app.services.rate_limiter import rate_limiter

logger = logging.getLogger(__name__)
_running = False
_semaphore: asyncio.Semaphore | None = None


async def _process_one_job(client: httpx.AsyncClient, job: dict):
    db     = await get_db()
    job_id = job["id"]
    idempotency_key = f"job-{job_id}"

    # Check if comment was deleted before sending
    async with db.execute(
        "SELECT 1 FROM deleted_comments WHERE comment_id = ?", (job["comment_id"],)
    ) as cur:
        if await cur.fetchone():
            await db.execute(
                "UPDATE dm_jobs SET status='cancelled', updated_at=? WHERE id=?",
                (now_iso(), job_id),
            )
            logger.info("Job %d cancelled (comment deleted)", job_id)
            return

    await rate_limiter.acquire()

    attempts = job["attempts"] + 1
    try:
        # FLEX 3: asyncio.shield protects this network call from being violently 
        # killed mid-flight if Railway restarts the server.
        dm_id = await asyncio.shield(send_dm(
            client,
            recipient_user_id=job["user_id"],
            message=job["dm_message"],
            comment_id=job["comment_id"],
            idempotency_key=idempotency_key,
        ))
        
        await db.execute(
            "UPDATE dm_jobs SET dm_id=?, status='sending', attempts=?, updated_at=? WHERE id=?",
            (dm_id, attempts, now_iso(), job_id),
        )
        logger.info("DM accepted dm_id=%s job=%d", dm_id, job_id)

    except RateLimitedError as exc:
        rate_limiter.record_429(exc.retry_after)
        retry_at = (datetime.now(timezone.utc) + timedelta(seconds=exc.retry_after)).isoformat()
        await db.execute(
            "UPDATE dm_jobs SET status='queued', attempts=?, next_retry_at=?, updated_at=? WHERE id=?",
            (attempts, retry_at, now_iso(), job_id),
        )

    except TransientError:
        if attempts >= DM_MAX_ATTEMPTS:
            await db.execute(
                "UPDATE dm_jobs SET status='failed', attempts=?, updated_at=? WHERE id=?",
                (attempts, now_iso(), job_id),
            )
            logger.error("Job %d exhausted retries → failed", job_id)
        else:
            # FLEX 1: Jitter. Prevents the "Thundering Herd" DDOS when APIs recover.
            base = DM_BASE_BACKOFF_SECONDS * (2 ** (attempts - 1))
            jitter = random.uniform(0.8, 1.2)
            backoff = min(300, base * jitter) # Cap at 5 mins max
            retry_at = (datetime.now(timezone.utc) + timedelta(seconds=backoff)).isoformat()
            await db.execute(
                "UPDATE dm_jobs SET status='queued', attempts=?, next_retry_at=?, updated_at=? WHERE id=?",
                (attempts, retry_at, now_iso(), job_id),
            )
            logger.warning("Job %d transient error, retry in %.1fs", job_id, backoff)

    except PermanentError:
        await db.execute(
            "UPDATE dm_jobs SET status='failed', attempts=?, updated_at=? WHERE id=?",
            (attempts, now_iso(), job_id),
        )
        logger.error("Job %d permanent error → failed", job_id)


async def _sender_loop():
    global _semaphore
    _semaphore = asyncio.Semaphore(WORKER_CONCURRENCY)

    async with httpx.AsyncClient() as client:
        while _running:
            db  = await get_db()
            now = now_iso()

            async with db.execute(
                """SELECT dj.id, dj.rule_id, dj.user_id, dj.username,
                          dj.comment_id, dj.attempts, dj.dm_id, r.dm_message
                   FROM dm_jobs dj
                   JOIN rules r ON r.rule_id = dj.rule_id
                   WHERE dj.status = 'queued'
                     AND (dj.next_retry_at IS NULL OR dj.next_retry_at <= ?)
                   ORDER BY dj.created_at ASC
                   LIMIT 20""",
                (now,),
            ) as cur:
                jobs = [dict(zip(
                    ["id","rule_id","user_id","username","comment_id","attempts","dm_id","dm_message"],
                    row
                )) for row in await cur.fetchall()]

            if not jobs:
                await asyncio.sleep(0.5)
                continue

            async def guarded(job):
                async with _semaphore:
                    await _process_one_job(client, job)

            await asyncio.gather(*[guarded(j) for j in jobs], return_exceptions=True)


async def _reconciler_loop():
    """Polls GET /v1/dm/{dm_id} for all 'sending' jobs and updates status."""
    async with httpx.AsyncClient() as client:
        while _running:
            await asyncio.sleep(RECONCILE_INTERVAL_SECONDS)
            db = await get_db()

            async with db.execute(
                "SELECT id, dm_id, attempts FROM dm_jobs WHERE status='sending' AND dm_id IS NOT NULL"
            ) as cur:
                jobs = [{"id": r[0], "dm_id": r[1], "attempts": r[2]} for r in await cur.fetchall()]

            if jobs:
                logger.info("Reconciler: checking %d in-flight DMs", len(jobs))

            for job in jobs:
                status_data = await get_dm_status(client, job["dm_id"])
                status = status_data.get("status", "")

                if status == "delivered":
                    await db.execute(
                        "UPDATE dm_jobs SET status='delivered', updated_at=? WHERE id=?",
                        (now_iso(), job["id"]),
                    )
                    logger.info("✅ DM %s delivered", job["dm_id"])

                elif status == "failed":
                    attempts = job["attempts"]
                    if attempts >= DM_MAX_ATTEMPTS:
                        await db.execute(
                            "UPDATE dm_jobs SET status='failed', updated_at=? WHERE id=?",
                            (now_iso(), job["id"]),
                        )
                    else:
                        # FLEX 1: Jitter for reconciler too
                        base = DM_BASE_BACKOFF_SECONDS * (2 ** attempts)
                        jitter = random.uniform(0.8, 1.2)
                        backoff = min(300, base * jitter)
                        retry_at = (datetime.now(timezone.utc) + timedelta(seconds=backoff)).isoformat()
                        await db.execute(
                            "UPDATE dm_jobs SET status='queued', dm_id=NULL, next_retry_at=?, updated_at=? WHERE id=?",
                            (retry_at, now_iso(), job["id"]),
                        )
                        logger.warning("DM %s failed on platform, re-queued", job["dm_id"])


async def _db_cleanup_loop():
    """
    FLEX 2: Data Retention Policy.
    Prevents unbound DB growth by sweeping old delivered/cancelled records.
    """
    while _running:
        try:
            db = await get_db()
            seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
            
            async with db.execute(
                "DELETE FROM dm_jobs WHERE status IN ('delivered', 'cancelled') AND updated_at < ?",
                (seven_days_ago,)
            ) as cur:
                if cur.rowcount > 0:
                    logger.info("🧹 Swept %d old terminal jobs from database", cur.rowcount)
                    
            async with db.execute(
                "DELETE FROM seen_events WHERE received_at < ?", (seven_days_ago,)
            ): pass
            
        except Exception as e:
            logger.error("Cleanup loop error: %s", e)
            
        await asyncio.sleep(3600)  # Run once an hour


_tasks: list[asyncio.Task] = []


def start_workers():
    global _running
    _running = True
    _tasks.append(asyncio.create_task(_sender_loop(), name="dm-sender"))
    _tasks.append(asyncio.create_task(_reconciler_loop(), name="dm-reconciler"))
    _tasks.append(asyncio.create_task(_db_cleanup_loop(), name="db-cleanup"))
    logger.info("Workers started (sender, reconciler, cleanup)")


async def stop_workers():
    global _running
    _running = False
    for t in _tasks:
        t.cancel()
    await asyncio.gather(*_tasks, return_exceptions=True)
    logger.info("Workers stopped")
