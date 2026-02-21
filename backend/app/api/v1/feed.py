from __future__ import annotations

import logging
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.config import settings
from app.schemas.common import ResponseEnvelope
from app.schemas.feed import FeedPageResponse
from app.services.feed_service import get_feed_page

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/",
    response_model=ResponseEnvelope[FeedPageResponse],
    summary="Get paginated feed by tab",
)
async def list_feed(
    tab: Annotated[
        Literal["news", "vc_blog", "all"],
        Query(description="Feed tab — 'news', 'vc_blog', or 'all'"),
    ] = "news",
    cursor: Annotated[
        str | None,
        Query(description="Pagination cursor (Base64-encoded published_at:id)"),
    ] = None,
    limit: Annotated[
        int,
        Query(ge=1, le=settings.MAX_PAGE_SIZE, description="Items per page (max 50)"),
    ] = settings.DEFAULT_PAGE_SIZE,
    keyword: Annotated[
        str | None,
        Query(description="Optional keyword filter"),
    ] = None,
    session: AsyncSession = Depends(get_session),
) -> ResponseEnvelope[FeedPageResponse]:
    page = await get_feed_page(
        session=session,
        tab=tab,
        cursor=cursor,
        limit=limit,
        keyword=keyword,
    )
    return ResponseEnvelope.ok(
        data=page,
        meta={
            "tab": tab,
            "limit": limit,
            "has_more": page.has_more,
        },
    )
