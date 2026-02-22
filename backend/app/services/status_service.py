from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.crawl_log import CrawlLog
from app.models.source import Source
from app.schemas.status import SourceStatusSchema, StatusResponse

logger = logging.getLogger(__name__)


def _resolve_crawl_status(latest_log: CrawlLog | None) -> str:
    """CrawlLog 레코드로부터 crawl_status 문자열을 결정한다."""
    if latest_log is None:
        return "unknown"
    s = (latest_log.status or "").lower()
    if s == "success":
        return "success"
    if s == "failed":
        return "failed"
    if s == "running":
        return "running"
    return "unknown"


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

        crawl_status = _resolve_crawl_status(latest_log)

        source_statuses.append(
            SourceStatusSchema(
                source_id=source.id,
                source_name=source.name,
                last_crawled_at=source.last_crawled_at,
                crawl_status=crawl_status,
            )
        )

    # last_updated_at: 가장 최근 last_crawled_at
    crawled_times = [
        s.last_crawled_at for s in source_statuses if s.last_crawled_at is not None
    ]
    last_updated_at: datetime | None = max(crawled_times) if crawled_times else None

    # overall status
    statuses = {s.crawl_status for s in source_statuses}
    if "failed" in statuses:
        overall = "warning"
    elif not statuses or statuses == {"unknown"}:
        overall = "ok"
    else:
        overall = "ok"

    return StatusResponse(
        last_updated_at=last_updated_at,
        status=overall,
        sources=source_statuses,
    )
