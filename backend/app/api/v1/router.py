from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import feed, search, sources, status

router = APIRouter()

router.include_router(feed.router, prefix="/feed", tags=["feed"])
router.include_router(sources.router, prefix="/sources", tags=["sources"])
router.include_router(status.router, prefix="/status", tags=["status"])
router.include_router(search.router, prefix="/search", tags=["search"])
