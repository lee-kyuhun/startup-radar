from __future__ import annotations

import base64
import logging
from datetime import datetime, timezone

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.feed_item import FeedItem
from app.models.source import Source
from app.redis_client import cache_get, cache_set
from app.schemas.feed import FeedItemSchema, FeedPageResponse, FeedSourceSummary

logger = logging.getLogger(__name__)

FEED_CACHE_TTL = 60  # seconds


def _encode_cursor(published_at: datetime, item_id: int) -> str:
    raw = f"{published_at.isoformat()}:{item_id}"
    return base64.urlsafe_b64encode(raw.encode()).decode()


def _decode_cursor(cursor: str) -> tuple[datetime, int] | None:
    try:
        raw = base64.urlsafe_b64decode(cursor.encode()).decode()
        dt_str, id_str = raw.rsplit(":", 1)
        published_at = datetime.fromisoformat(dt_str)
        if published_at.tzinfo is None:
            published_at = published_at.replace(tzinfo=timezone.utc)
        return published_at, int(id_str)
    except Exception as exc:
        logger.warning("Invalid cursor %r: %s", cursor, exc)
        return None


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
    cursor: str | None,
    limit: int,
    keyword: str | None = None,
) -> FeedPageResponse:
    """
    Fetch a page of feed items with cursor-based pagination.
    Results are cached in Redis for FEED_CACHE_TTL seconds.
    """
    cache_key = f"feed:{tab}:cursor={cursor or 'start'}:limit={limit}:kw={keyword or ''}"
    cached = await cache_get(cache_key)
    if cached:
        logger.debug("Cache hit: %s", cache_key)
        return FeedPageResponse(**cached)

    # Determine source_type filter from tab name
    type_map = {
        "news": ["news"],
        "vc_blog": ["vc_blog"],
    }
    source_types = type_map.get(tab, ["news"])

    # Base query
    stmt = (
        select(FeedItem)
        .join(FeedItem.source)
        .options(joinedload(FeedItem.source))
        .where(
            and_(
                FeedItem.is_active == True,
                Source.source_type.in_(source_types),
                Source.is_active == True,
            )
        )
    )

    # Cursor pagination — keyset on (published_at DESC, id DESC)
    if cursor:
        decoded = _decode_cursor(cursor)
        if decoded:
            cursor_dt, cursor_id = decoded
            stmt = stmt.where(
                (FeedItem.published_at < cursor_dt)
                | (
                    (FeedItem.published_at == cursor_dt)
                    & (FeedItem.id < cursor_id)
                )
            )

    # Keyword filter
    if keyword:
        stmt = stmt.where(
            FeedItem.title.ilike(f"%{keyword}%")
            | FeedItem.summary.ilike(f"%{keyword}%")
        )

    stmt = stmt.order_by(FeedItem.published_at.desc(), FeedItem.id.desc()).limit(limit + 1)

    result = await session.execute(stmt)
    rows = result.scalars().all()

    has_more = len(rows) > limit
    page_items = rows[:limit]

    next_cursor: str | None = None
    if has_more and page_items:
        last = page_items[-1]
        next_cursor = _encode_cursor(last.published_at, last.id)

    response = FeedPageResponse(
        items=[_item_to_schema(item) for item in page_items],
        next_cursor=next_cursor,
        has_more=has_more,
        limit=limit,
    )

    # Cache serialised response (model_dump converts datetimes to strings)
    await cache_set(cache_key, response.model_dump(mode="json"), ttl=FEED_CACHE_TTL)

    return response
