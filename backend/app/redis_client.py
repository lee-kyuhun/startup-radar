from __future__ import annotations

import json
import logging
from typing import Any

import redis.asyncio as aioredis

from app.config import settings

logger = logging.getLogger(__name__)

# ── Client singleton ──────────────────────────────────────────────────────────
_redis: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None
        logger.info("Redis connection closed")


# ── Cache utilities ───────────────────────────────────────────────────────────
async def cache_get(key: str) -> Any | None:
    """Retrieve a JSON-serialised value from Redis. Returns None on miss."""
    try:
        client = await get_redis()
        raw = await client.get(key)
        if raw is None:
            return None
        return json.loads(raw)
    except Exception as exc:
        logger.warning("Redis GET failed for key=%s: %s", key, exc)
        return None


async def cache_set(key: str, value: Any, ttl: int = 60) -> None:
    """Store a JSON-serialisable value in Redis with a TTL (seconds)."""
    try:
        client = await get_redis()
        await client.setex(key, ttl, json.dumps(value, default=str))
    except Exception as exc:
        logger.warning("Redis SET failed for key=%s: %s", key, exc)


async def cache_delete(key: str) -> None:
    """Delete a key from Redis."""
    try:
        client = await get_redis()
        await client.delete(key)
    except Exception as exc:
        logger.warning("Redis DELETE failed for key=%s: %s", key, exc)


# ── Crawl lock ────────────────────────────────────────────────────────────────
async def acquire_crawl_lock(source_id: int, ttl: int = 300) -> bool:
    """
    Try to set crawl_lock:{source_id} with NX (set if not exists).
    Returns True if lock was acquired, False if already held.
    """
    try:
        client = await get_redis()
        key = f"crawl_lock:{source_id}"
        result = await client.set(key, "1", ex=ttl, nx=True)
        return result is True
    except Exception as exc:
        logger.warning("Failed to acquire crawl lock for source_id=%s: %s", source_id, exc)
        # Fail open — allow crawl if Redis is unavailable
        return True


async def release_crawl_lock(source_id: int) -> None:
    """Release the crawl lock for a source."""
    await cache_delete(f"crawl_lock:{source_id}")
