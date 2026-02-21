from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.models.source import Source
from app.schemas.common import ResponseEnvelope
from app.schemas.source import SourceListResponse, SourceSchema

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/",
    response_model=ResponseEnvelope[SourceListResponse],
    summary="List all registered sources",
)
async def list_sources(
    session: AsyncSession = Depends(get_session),
) -> ResponseEnvelope[SourceListResponse]:
    result = await session.execute(
        select(Source).order_by(Source.source_type, Source.name)
    )
    sources = result.scalars().all()

    return ResponseEnvelope.ok(
        data=SourceListResponse(
            sources=[SourceSchema.model_validate(s) for s in sources],
            total=len(sources),
        )
    )
