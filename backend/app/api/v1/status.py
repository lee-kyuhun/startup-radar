from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.schemas.common import ResponseEnvelope
from app.schemas.status import StatusResponse
from app.services.status_service import get_crawl_status

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/",
    response_model=ResponseEnvelope[StatusResponse],
    summary="Get crawling status for all sources",
)
async def crawl_status(
    session: AsyncSession = Depends(get_session),
) -> ResponseEnvelope[StatusResponse]:
    status = await get_crawl_status(session=session)
    return ResponseEnvelope.ok(data=status)
