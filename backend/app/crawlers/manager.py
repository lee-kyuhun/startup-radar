from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.crawlers.base import BaseCrawler, CrawledItem
from app.crawlers.html_crawler import StartupTodayCrawler
from app.crawlers.playwright_crawler import KakaoVenturesCrawler
from app.crawlers.rss_crawler import RSSCrawler
from app.database import AsyncSessionFactory
from app.models.crawl_log import CrawlLog
from app.models.feed_item import FeedItem
from app.models.source import Source
from app.redis_client import acquire_crawl_lock, release_crawl_lock

logger = logging.getLogger(__name__)

# ── Strategy registry ─────────────────────────────────────────────────────────
# Maps (crawl_strategy, slug) → crawler class.
# The slug key allows source-specific overrides; falls back to strategy-only key.
_STRATEGY_MAP: dict[str, type[BaseCrawler]] = {
    "rss": RSSCrawler,
    "html": StartupTodayCrawler,
    "playwright": KakaoVenturesCrawler,
}

_SLUG_OVERRIDE_MAP: dict[str, type[BaseCrawler]] = {
    "startuptoday": StartupTodayCrawler,
    "kakao-ventures": KakaoVenturesCrawler,
}


def _resolve_crawler(source: Source) -> type[BaseCrawler] | None:
    # Slug-specific override first
    if source.slug in _SLUG_OVERRIDE_MAP:
        return _SLUG_OVERRIDE_MAP[source.slug]
    return _STRATEGY_MAP.get(source.crawl_strategy)


# ── Core crawl logic ──────────────────────────────────────────────────────────

async def crawl_source(source_id: int) -> None:
    """
    Main entry point called by APScheduler for each source.
    Handles locking, crawling, DB persistence, and log writing.
    """
    async with AsyncSessionFactory() as session:
        # Load source
        source: Source | None = await session.get(Source, source_id)
        if source is None or not source.is_active:
            logger.info("Source %s not found or inactive — skipping", source_id)
            return

        # Acquire distributed lock
        acquired = await acquire_crawl_lock(source_id)
        if not acquired:
            logger.info("Crawl lock held for source_id=%s — skipping", source_id)
            return

        # Create crawl log
        log = CrawlLog(source_id=source_id, status="running")
        session.add(log)
        await session.flush()  # get log.id
        log_id = log.id

        try:
            crawler_cls = _resolve_crawler(source)
            if crawler_cls is None:
                raise ValueError(f"No crawler registered for strategy={source.crawl_strategy!r}")

            crawler: BaseCrawler = crawler_cls(
                source_id=source.id,
                source_slug=source.slug,
                feed_url=source.feed_url,
            )
            items: list[CrawledItem] = await crawler.crawl()

            new_count = await _persist_items(session, source_id, items)

            # Update source.last_crawled_at
            await session.execute(
                update(Source)
                .where(Source.id == source_id)
                .values(last_crawled_at=datetime.now(tz=timezone.utc))
            )

            # Update log
            await session.execute(
                update(CrawlLog)
                .where(CrawlLog.id == log_id)
                .values(
                    status="success",
                    finished_at=datetime.now(tz=timezone.utc),
                    items_fetched=len(items),
                    items_new=new_count,
                )
            )
            await session.commit()
            logger.info(
                "Crawl success: source=%s fetched=%d new=%d",
                source.slug, len(items), new_count
            )

        except Exception as exc:
            logger.error("Crawl failed for source_id=%s: %s", source_id, exc, exc_info=True)
            await session.rollback()
            async with AsyncSessionFactory() as err_session:
                await err_session.execute(
                    update(CrawlLog)
                    .where(CrawlLog.id == log_id)
                    .values(
                        status="failed",
                        finished_at=datetime.now(tz=timezone.utc),
                        error_message=str(exc),
                    )
                )
                await err_session.commit()
        finally:
            await release_crawl_lock(source_id)


async def _persist_items(
    session: AsyncSession, source_id: int, items: list[CrawledItem]
) -> int:
    """
    Insert new feed items, skipping duplicates by URL (ON CONFLICT DO NOTHING pattern).
    Returns the count of newly inserted rows.
    """
    if not items:
        return 0

    new_count = 0
    for item in items:
        # Check for existing URL
        result = await session.execute(select(FeedItem.id).where(FeedItem.url == item.url))
        existing = result.scalar_one_or_none()
        if existing is not None:
            continue

        feed_item = FeedItem(
            source_id=source_id,
            title=item.title,
            url=item.url,
            summary=item.summary,
            author=item.author,
            published_at=item.published_at,
            crawled_at=datetime.now(tz=timezone.utc),
            raw_metadata=item.raw_metadata,
        )
        session.add(feed_item)
        new_count += 1

    await session.flush()
    return new_count


# ── Scheduler registration ────────────────────────────────────────────────────

async def register_all_crawl_jobs(scheduler) -> None:
    """
    Load all active sources from the DB and register APScheduler interval jobs.
    Called once at application startup.
    """
    async with AsyncSessionFactory() as session:
        result = await session.execute(select(Source).where(Source.is_active == True))
        sources = result.scalars().all()

    for source in sources:
        job_id = f"crawl_{source.slug}"
        scheduler.add_job(
            crawl_source,
            trigger="interval",
            minutes=source.crawl_interval,
            args=[source.id],
            id=job_id,
            replace_existing=True,
            coalesce=True,
            max_instances=1,
        )
        logger.info(
            "Registered crawl job: source=%s interval=%dm",
            source.slug, source.crawl_interval
        )

    logger.info("Total crawl jobs registered: %d", len(sources))
