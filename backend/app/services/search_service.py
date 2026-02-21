from __future__ import annotations

import logging

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.feed_item import FeedItem
from app.models.source import Source
from app.schemas.feed import FeedItemSchema, FeedPageResponse, FeedSourceSummary

logger = logging.getLogger(__name__)

MAX_SEARCH_LIMIT = 50


def _item_to_schema(item: FeedItem) -> FeedItemSchema:
    source_summary = FeedSourceSummary(
        id=item.source.id,
        name=item.source.name,
        slug=item.source.slug,
        source_type=item.source.source_type,
    )
    return FeedItemSchema(
        id=item.id,
        source=source_summary,
        title=item.title,
        url=item.url,
        summary=item.summary,
        author=item.author,
        published_at=item.published_at,
        crawled_at=item.crawled_at,
    )


async def search_feed_items(
    session: AsyncSession,
    keyword: str,
    source_type: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> FeedPageResponse:
    """
    Search feed items by keyword using PostgreSQL ILIKE (case-insensitive).
    Searches title and summary fields.

    Full-text search (tsvector / GIN index) is planned for a later phase.
    """
    limit = min(limit, MAX_SEARCH_LIMIT)

    stmt = (
        select(FeedItem)
        .join(FeedItem.source)
        .options(joinedload(FeedItem.source))
        .where(
            and_(
                FeedItem.is_active == True,
                Source.is_active == True,
                or_(
                    FeedItem.title.ilike(f"%{keyword}%"),
                    FeedItem.summary.ilike(f"%{keyword}%"),
                ),
            )
        )
    )

    if source_type:
        stmt = stmt.where(Source.source_type == source_type)

    stmt = (
        stmt
        .order_by(FeedItem.published_at.desc())
        .limit(limit + 1)
        .offset(offset)
    )

    result = await session.execute(stmt)
    rows = result.scalars().all()

    has_more = len(rows) > limit
    page_items = rows[:limit]

    return FeedPageResponse(
        items=[_item_to_schema(item) for item in page_items],
        next_cursor=None,  # Search uses offset, not cursor
        has_more=has_more,
        limit=limit,
    )
