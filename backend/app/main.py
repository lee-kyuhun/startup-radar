from __future__ import annotations

import asyncio
import logging
import subprocess
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import sentry_sdk
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from tenacity import retry, retry_if_exception_type, stop_after_delay, wait_exponential

from app.config import settings
from app.crawlers.manager import register_all_crawl_jobs
from app.database import close_db, engine
from app.redis_client import close_redis

logger = logging.getLogger(__name__)

# ── Sentry ────────────────────────────────────────────────────────────────────
if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        traces_sample_rate=0.2,
        environment=settings.APP_ENV,
    )

# ── Scheduler singleton ───────────────────────────────────────────────────────
scheduler = AsyncIOScheduler(timezone="Asia/Seoul")


# ── DB readiness check ────────────────────────────────────────────────────────
@retry(
    wait=wait_exponential(multiplier=1, min=2, max=10),
    stop=stop_after_delay(60),
    retry=retry_if_exception_type(Exception),
    before_sleep=lambda retry_state: logger.info(
        "[startup] Waiting for DB... attempt %d", retry_state.attempt_number
    ),
)
async def _wait_for_db() -> None:
    """Verify DB connectivity. Retries with exponential backoff up to 60s."""
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    logger.info("[startup] DB connection verified")


# ── Production init (migration + seed) ────────────────────────────────────────
async def _run_production_init() -> None:
    """Run alembic migrations + seed data only when APP_ENV == 'production'."""
    if settings.APP_ENV != "production":
        return

    # 0) Wait for DB to be reachable
    try:
        await _wait_for_db()
    except Exception as exc:
        logger.error("[startup] DB not reachable after 60s: %s", exc)
        return

    # 1) Alembic migration via subprocess (separate process = no event loop conflict)
    try:
        logger.info("[startup] Running alembic upgrade head …")
        result = await asyncio.to_thread(
            subprocess.run,
            ["alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            logger.info("[startup] alembic upgrade head — OK")
        else:
            logger.error("[startup] alembic FAILED (rc=%d): %s", result.returncode, result.stderr)
    except Exception as exc:
        logger.error("[startup] alembic FAILED: %s", exc, exc_info=True)

    # 2) Seed initial data
    try:
        from app.scripts.seed import seed_sources
        logger.info("[startup] Running seed_sources …")
        await seed_sources()
        logger.info("[startup] seed_sources — OK")
    except Exception as exc:
        logger.error("[startup] seed_sources FAILED: %s", exc, exc_info=True)


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Starting up Startup Radar API (env=%s)", settings.APP_ENV)

    # Production-only: auto-migrate DB and seed initial data
    await _run_production_init()

    # Register crawler jobs
    try:
        await register_all_crawl_jobs(scheduler)
    except Exception as exc:
        logger.warning("Failed to register crawl jobs (DB may not be ready): %s", exc)

    scheduler.start()
    logger.info("APScheduler started with %d jobs", len(scheduler.get_jobs()))

    yield

    # Shutdown
    scheduler.shutdown(wait=False)
    logger.info("APScheduler stopped")
    await close_redis()
    await close_db()
    logger.info("Startup Radar API shutdown complete")


# ── App factory ───────────────────────────────────────────────────────────────
def create_app() -> FastAPI:
    app = FastAPI(
        title="Startup Radar API",
        description="한국 VC/스타트업 생태계 종사자를 위한 피드 허브",
        version="0.1.0",
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        lifespan=lifespan,
    )

    # ── CORS ──────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routes ────────────────────────────────────────────────────────────────
    from app.api.v1.router import router as v1_router
    app.include_router(v1_router, prefix=settings.API_V1_PREFIX)

    # ── Health check ──────────────────────────────────────────────────────────
    @app.get("/health", tags=["health"], include_in_schema=False)
    async def health() -> dict:
        return {"status": "ok", "env": settings.APP_ENV}

    # ── Global exception handler ──────────────────────────────────────────────
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error("Unhandled exception: %s", exc, exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "data": None,
                "error": {"code": "INTERNAL_ERROR", "message": "Internal server error"},
                "meta": None,
            },
        )

    return app


app = create_app()
