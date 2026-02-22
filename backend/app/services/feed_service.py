from __future__ import annotations

import logging

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.feed_item import FeedItem
from app.models.source import Source
from app.redis_client import cache_get, cache_set
from app.schemas.feed import FeedItemSchema, FeedSourceSummary

logger = logging.getLogger(__name__)

FEED_CACHE_TTL = 300  # 5 minutes (as per API Contract / DB_Schema.md)


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


async def get_feed_page(
    session: AsyncSession,
    tab: str,
    page: int,
    limit: int,
    keyword: str | None = None,
) -> tuple[list[dict], int]:
    """
    Fetch a page of feed items with offset-based pagination.
    Returns (items_as_dicts, total_count).
    Results are cached in Redis for FEED_CACHE_TTL seconds.
    """
    # Redis cache key: feed:{tab}:p{page}:l{limit} (v1.1 format)
    cache_key = f"feed:{tab}:p{page}:l{limit}"
    if keyword:
        cache_key += f":kw={keyword}"

    cached = await cache_get(cache_key)
    if cached:
        logger.debug("Cache hit: %s", cache_key)
        return cached["items"], cached["total_count"]

    # Determine source_type filter from tab name
    type_map = {
        "news": ["news"],
        "vc_blog": ["vc_blog"],
    }
    source_types = type_map.get(tab, ["news"])

    # Build base filter conditions
    base_conditions = and_(
        FeedItem.is_active == True,  # noqa: E712
        Source.source_type.in_(source_types),
        Source.is_active == True,  # noqa: E712
    )

    # Keyword filter
    keyword_condition = None
    if keyword:
        keyword_condition = (
            FeedItem.title.ilike(f"%{keyword}%")
            | FeedItem.summary.ilike(f"%{keyword}%")
        )

    # Count total items matching the filter
    count_stmt = (
        select(func.count())
        .select_from(FeedItem)
        .join(FeedItem.source)
        .where(base_conditions)
    )
    if keyword_condition is not None:
        count_stmt = count_stmt.where(keyword_condition)

    total_count_result = await session.execute(count_stmt)
    total_count = total_count_result.scalar_one()

    # Fetch the page items with OFFSET/LIMIT
    offset = (page - 1) * limit
    items_stmt = (
        select(FeedItem)
        .join(FeedItem.source)
        .options(joinedload(FeedItem.source))
        .where(base_conditions)
    )
    if keyword_condition is not None:
        items_stmt = items_stmt.where(keyword_condition)

    items_stmt = (
        items_stmt
        .order_by(FeedItem.published_at.desc(), FeedItem.id.desc())
        .limit(limit)
        .offset(offset)
    )

    result = await session.execute(items_stmt)
    rows = result.scalars().all()

    items = [_item_to_schema(item).model_dump(mode="json") for item in rows]

    # Cache the result
    await cache_set(
        cache_key,
        {"items": items, "total_count": total_count},
        ttl=FEED_CACHE_TTL,
    )

    return items, total_count
