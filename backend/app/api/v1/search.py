from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.config import settings
from app.schemas.common import ResponseEnvelope
from app.schemas.feed import FeedPageResponse
from app.services.search_service import search_feed_items

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/",
    response_model=ResponseEnvelope[FeedPageResponse],
    summary="Search feed items by keyword (ILIKE)",
)
async def search(
    q: Annotated[
        str,
        Query(min_length=1, max_length=200, description="Search keyword"),
    ],
    source_type: Annotated[
        str | None,
        Query(description="Filter by source type (news | vc_blog | person_threads)"),
    ] = None,
    limit: Annotated[
        int,
        Query(ge=1, le=settings.MAX_PAGE_SIZE, description="Results per page (max 50)"),
    ] = settings.DEFAULT_PAGE_SIZE,
    offset: Annotated[
        int,
        Query(ge=0, description="Pagination offset"),
    ] = 0,
    session: AsyncSession = Depends(get_session),
) -> ResponseEnvelope[FeedPageResponse]:
    results = await search_feed_items(
        session=session,
        keyword=q,
        source_type=source_type,
        limit=limit,
        offset=offset,
    )
    return ResponseEnvelope.ok(
        data=results,
        meta={
            "query": q,
            "limit": limit,
            "offset": offset,
            "has_more": results.has_more,
        },
    )
