"""
services/dm_sender.py
──────────────────────
Sends a single DM via the mock API.

Handles:
  • 202  → accepted, return dm_id
  • 429  → rate-limited, raise RateLimitedError(retry_after)
  • 500  → transient error, raise TransientError
  • 400  → permanent error, raise PermanentError
  • network timeouts → raise TransientError
"""
import httpx
import logging
from app.config import PSEUDOGRAM_API_KEY, PSEUDOGRAM_BASE_URL

logger = logging.getLogger(__name__)

DM_ENDPOINT = f"{PSEUDOGRAM_BASE_URL}/v1/dm/send"
DM_STATUS_ENDPOINT = f"{PSEUDOGRAM_BASE_URL}/v1/dm"


class RateLimitedError(Exception):
    def __init__(self, retry_after: float):
        self.retry_after = retry_after


class TransientError(Exception):
    pass


class PermanentError(Exception):
    pass


async def send_dm(
    client: httpx.AsyncClient,
    recipient_user_id: str,
    message: str,
    comment_id: str,
    idempotency_key: str,
) -> str:
    """
    Returns dm_id on success.
    Raises RateLimitedError, TransientError, or PermanentError.
    """
    headers = {
        "X-API-Key": PSEUDOGRAM_API_KEY,
        "Idempotency-Key": idempotency_key,
        "Content-Type": "application/json",
    }
    payload = {
        "recipient_user_id": recipient_user_id,
        "message": message,
        "comment_id": comment_id,
    }

    try:
        resp = await client.post(DM_ENDPOINT, json=payload, headers=headers, timeout=15)
    except (httpx.TimeoutException, httpx.NetworkError) as exc:
        logger.warning("Network error sending DM: %s", exc)
        raise TransientError(str(exc))

    # Mock API returns 200 or 202 — both mean accepted
    if resp.status_code in (200, 202):
        data = resp.json()
        dm_id = data.get("dm_id", "")
        logger.info("DM accepted: dm_id=%s status=%s", dm_id, data.get("status"))
        return dm_id

    if resp.status_code == 429:
        retry_after = float(resp.headers.get("Retry-After", "60"))
        logger.warning("Rate-limited, retry_after=%.1fs", retry_after)
        raise RateLimitedError(retry_after)

    if resp.status_code == 500:
        logger.warning("API 500, will retry. Body: %s", resp.text[:200])
        raise TransientError("API 500")

    if resp.status_code == 400:
        logger.error("Permanent error: %s", resp.text[:200])
        raise PermanentError(f"400: {resp.text[:200]}")

    logger.warning("Unexpected status %d: %s", resp.status_code, resp.text[:200])
    raise TransientError(f"Unexpected status {resp.status_code}")


async def get_dm_status(client: httpx.AsyncClient, dm_id: str) -> dict:
    """
    Polls GET /v1/dm/{dm_id} for delivery status.
    Returns the full response dict.
    Reads do not count against rate limit (per spec).
    """
    headers = {"X-API-Key": PSEUDOGRAM_API_KEY}
    try:
        resp = await client.get(
            f"{DM_STATUS_ENDPOINT}/{dm_id}", headers=headers, timeout=10
        )
        if resp.status_code == 200:
            return resp.json()
        logger.warning("DM status check returned %d for %s", resp.status_code, dm_id)
        return {}
    except Exception as exc:
        logger.warning("Error polling DM status for %s: %s", dm_id, exc)
        return {}
