from __future__ import annotations

import logging
import math
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.config import settings
from app.schemas.common import PaginationMeta, ResponseEnvelope
from app.services.search_service import search_feed_items

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/",
    summary="Search feed items by keyword (offset-based pagination)",
)
async def search(
    q: Annotated[
        str | None,
        Query(description="Search keyword (1~100 chars)"),
    ] = None,
    page: Annotated[
        int,
        Query(ge=1, description="Page number (1-indexed)"),
    ] = 1,
    limit: Annotated[
        int,
        Query(ge=1, le=settings.MAX_PAGE_SIZE, description="Results per page (max 50)"),
    ] = settings.DEFAULT_PAGE_SIZE,
    session: AsyncSession = Depends(get_session),
) -> ResponseEnvelope:
    # Validate query parameter
    if not q or len(q.strip()) == 0:
        return JSONResponse(
            status_code=400,
            content=ResponseEnvelope.fail(
                code="INVALID_QUERY",
                message="검색어를 입력해주세요.",
            ).model_dump(),
        )

    if len(q) > 100:
        return JSONResponse(
            status_code=400,
            content=ResponseEnvelope.fail(
                code="INVALID_QUERY",
                message="검색어는 100자 이하로 입력해주세요.",
            ).model_dump(),
        )

    # Validate limit range
    if limit < 1 or limit > settings.MAX_PAGE_SIZE:
        return JSONResponse(
            status_code=400,
            content=ResponseEnvelope.fail(
                code="INVALID_LIMIT",
                message=f"limit은 1~{settings.MAX_PAGE_SIZE} 범위여야 합니다.",
            ).model_dump(),
        )

    items, total_count = await search_feed_items(
        session=session,
        keyword=q.strip(),
        page=page,
        limit=limit,
    )

    total_pages = math.ceil(total_count / limit) if total_count > 0 else 0

    # Validate page range (after we know total_pages)
    if page < 1 or (total_pages > 0 and page > total_pages):
        return JSONResponse(
            status_code=400,
            content=ResponseEnvelope.fail(
                code="INVALID_PAGE",
                message="유효하지 않은 페이지 번호입니다.",
            ).model_dump(),
        )

    meta = PaginationMeta(
        current_page=page,
        total_pages=total_pages,
        total_count=total_count,
        limit=limit,
        has_prev=page > 1,
        has_next=page < total_pages,
    )

    return ResponseEnvelope.ok(
        data=items,
        meta=meta.model_dump(),
    )
