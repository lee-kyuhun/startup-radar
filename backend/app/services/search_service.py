from __future__ import annotations

import logging

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.feed_item import FeedItem
from app.models.source import Source
from app.redis_client import cache_get, cache_set
from app.schemas.feed import FeedItemSchema, FeedSourceSummary

logger = logging.getLogger(__name__)

SEARCH_CACHE_TTL = 60  # 1 minute (as per DB_Schema.md)


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
    )


async def search_feed_items(
    session: AsyncSession,
    keyword: str,
    page: int = 1,
    limit: int = 20,
) -> tuple[list[dict], int]:
    """
    Search feed items by keyword using PostgreSQL ILIKE (case-insensitive).
    Searches title and summary fields.
    Returns (items_as_dicts, total_count).

    Full-text search (tsvector / GIN index) is planned for a later phase.
    """
    # Build base filter conditions
    base_conditions = and_(
        FeedItem.is_active == True,  # noqa: E712
        Source.is_active == True,  # noqa: E712
        or_(
            FeedItem.title.ilike(f"%{keyword}%"),
            FeedItem.summary.ilike(f"%{keyword}%"),
        ),
    )

    # Count total matching items
    count_stmt = (
        select(func.count())
        .select_from(FeedItem)
        .join(FeedItem.source)
        .where(base_conditions)
    )
    total_count_result = await session.execute(count_stmt)
    total_count = total_count_result.scalar_one()

    # Fetch the page items with OFFSET/LIMIT
    offset = (page - 1) * limit
    items_stmt = (
        select(FeedItem)
        .join(FeedItem.source)
        .options(joinedload(FeedItem.source))
        .where(base_conditions)
        .order_by(FeedItem.published_at.desc(), FeedItem.id.desc())
        .limit(limit)
        .offset(offset)
    )

    result = await session.execute(items_stmt)
    rows = result.scalars().all()

    items = [_item_to_schema(item).model_dump(mode="json") for item in rows]

    return items, total_count
