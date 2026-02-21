from __future__ import annotations

import logging

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.crawl_log import CrawlLog
from app.models.source import Source
from app.schemas.status import CrawlLogSchema, SourceStatusSchema, StatusResponse

logger = logging.getLogger(__name__)


async def get_crawl_status(session: AsyncSession) -> StatusResponse:
    """
    Return the crawl status for all sources, each with their latest crawl log.
    """
    # Load all sources
    sources_result = await session.execute(
        select(Source).order_by(Source.name)
    )
    sources = sources_result.scalars().all()

    source_statuses: list[SourceStatusSchema] = []

    for source in sources:
        # Get the most recent crawl log for this source
        log_result = await session.execute(
            select(CrawlLog)
            .where(CrawlLog.source_id == source.id)
            .order_by(CrawlLog.started_at.desc())
            .limit(1)
        )
        latest_log = log_result.scalar_one_or_none()

        source_statuses.append(
            SourceStatusSchema(
                source_id=source.id,
                source_name=source.name,
                source_slug=source.slug,
                last_crawled_at=source.last_crawled_at,
                latest_log=CrawlLogSchema.model_validate(latest_log) if latest_log else None,
            )
        )

    active_count = sum(1 for s in sources if s.is_active)

    return StatusResponse(
        sources=source_statuses,
        total_sources=len(sources),
        active_sources=active_count,
    )
