from __future__ import annotations

import logging
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import feedparser

from app.crawlers.base import BaseCrawler, CrawledItem
from app.crawlers.text_utils import build_summary

logger = logging.getLogger(__name__)


def _parse_date(entry: feedparser.FeedParserDict) -> datetime:
    """Try several date fields; fall back to now()."""
    for attr in ("published_parsed", "updated_parsed"):
        val = getattr(entry, attr, None)
        if val:
            try:
                return datetime(*val[:6], tzinfo=timezone.utc)
            except Exception:
                pass
    # Try string fields
    for attr in ("published", "updated"):
        val = getattr(entry, attr, None)
        if val:
            try:
                return parsedate_to_datetime(val)
            except Exception:
                pass
    return datetime.now(tz=timezone.utc)


class RSSCrawler(BaseCrawler):
    """Fetches items from an RSS/Atom feed using feedparser."""

    async def crawl(self) -> list[CrawledItem]:
        if not self.feed_url:
            self.logger.warning("No feed_url configured for source=%s", self.source_slug)
            return []

        self.logger.info("Crawling RSS feed: %s", self.feed_url)

        # feedparser is synchronous — run in executor to avoid blocking event loop
        import asyncio
        loop = asyncio.get_event_loop()
        feed = await loop.run_in_executor(
            None,
            lambda: feedparser.parse(
                self.feed_url,
                agent=self.user_agent,
            ),
        )

        await self._rate_limit_sleep()

        if feed.bozo and not feed.entries:
            self.logger.warning(
                "feedparser returned bozo error for %s: %s",
                self.source_slug,
                feed.bozo_exception,
            )
            return []

        items: list[CrawledItem] = []
        for entry in feed.entries:
            title = getattr(entry, "title", "").strip() or "(제목 없음)"
            url = getattr(entry, "link", "").strip()
            if not url:
                continue

            # Build summary from content or summary field
            raw_content = ""
            if hasattr(entry, "content") and entry.content:
                raw_content = entry.content[0].get("value", "")
            if not raw_content:
                raw_content = getattr(entry, "summary", "") or ""

            summary = build_summary(raw_content)
            author = getattr(entry, "author", None)
            published_at = _parse_date(entry)

            raw_metadata = {
                "tags": [t.get("term") for t in getattr(entry, "tags", [])],
                "id": getattr(entry, "id", None),
            }

            items.append(
                CrawledItem(
                    title=title,
                    url=url,
                    published_at=published_at,
                    summary=summary,
                    author=author,
                    raw_metadata=raw_metadata,
                )
            )

        self.logger.info("Fetched %d items from %s", len(items), self.source_slug)
        return items
