"""
main.py — FastAPI application entry point
"""
import logging
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.db.database import get_db, close_db
from app.worker import start_workers, stop_workers
from app.routes import webhook, rules, stats, dashboard, jobs, debug

# ── Logging setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


# ── Lifespan: startup / shutdown hooks ───────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 LinkPlease starting up…")
    await get_db()          # initialise DB + schema
    start_workers()         # sender + reconciler background tasks
    yield
    logger.info("🛑 LinkPlease shutting down…")
    await stop_workers()
    await close_db()


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="LinkPlease",
    description="Automates Instagram DMs when comments match keywords.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ────────────────────────────────────────────────────────────────────
app.include_router(webhook.router)
app.include_router(rules.router)
app.include_router(stats.router)
app.include_router(dashboard.router)
app.include_router(jobs.router)
app.include_router(debug.router)


@app.get("/")
async def root():
    return {
        "service": "LinkPlease",
        "status": "running",
        "docs": "/docs",
        "dashboard": "/dashboard",
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
