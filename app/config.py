"""
config.py — centralised settings loaded from environment / .env file
"""
import os
from dotenv import load_dotenv

load_dotenv()

PSEUDOGRAM_API_KEY: str = os.getenv("PSEUDOGRAM_API_KEY", "")
PSEUDOGRAM_BASE_URL: str = os.getenv(
    "PSEUDOGRAM_BASE_URL", "https://pseudogram-api.onrender.com"
)

DB_PATH: str = os.getenv("DB_PATH", "linkplease.db")

# Retry / backoff
DM_MAX_ATTEMPTS: int = int(os.getenv("DM_MAX_ATTEMPTS", "5"))
DM_BASE_BACKOFF_SECONDS: float = float(os.getenv("DM_BASE_BACKOFF_SECONDS", "1"))

# How often the reconciler polls delivered status (seconds)
RECONCILE_INTERVAL_SECONDS: int = int(os.getenv("RECONCILE_INTERVAL_SECONDS", "30"))

# Number of concurrent DM sender coroutines
WORKER_CONCURRENCY: int = int(os.getenv("WORKER_CONCURRENCY", "3"))

# Rate limit: 10 requests per rolling 60 seconds
RATE_LIMIT_MAX: int = 10
RATE_LIMIT_WINDOW: float = 60.0
