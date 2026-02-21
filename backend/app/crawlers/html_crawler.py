from __future__ import annotations

import logging
from abc import abstractmethod
from datetime import datetime, timezone

import httpx
from bs4 import BeautifulSoup

from app.crawlers.base import BaseCrawler, CrawledItem
from app.crawlers.text_utils import build_summary

logger = logging.getLogger(__name__)


class HTMLCrawler(BaseCrawler):
    """
    Base class for HTML-scraping crawlers.

    Subclasses must implement `parse(html)` to extract items from the raw HTML.
    This class provides the HTTP fetch logic with rate-limiting and user-agent headers.
    """

    async def crawl(self) -> list[CrawledItem]:
        if not self.feed_url:
            self.logger.warning("No feed_url configured for source=%s", self.source_slug)
            return []

        self.logger.info("Crawling HTML page: %s", self.feed_url)

        headers = {"User-Agent": self.user_agent}

        async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=30) as client:
            try:
                response = await client.get(self.feed_url)
                response.raise_for_status()
            except httpx.HTTPError as exc:
                self.logger.error("HTTP error crawling %s: %s", self.source_slug, exc)
                return []

        await self._rate_limit_sleep()

        html = response.text
        try:
            items = self.parse(html)
        except Exception as exc:
            self.logger.error("Parse error for %s: %s", self.source_slug, exc, exc_info=True)
            return []

        self.logger.info("Fetched %d items from %s", len(items), self.source_slug)
        return items

    @abstractmethod
    def parse(self, html: str) -> list[CrawledItem]:
        """Parse the raw HTML and return a list of CrawledItem objects."""
        ...


# ─────────────────────────────────────────────────────────────────────────────
# Concrete implementation: StartupToday (스타트업투데이)
# ─────────────────────────────────────────────────────────────────────────────

class StartupTodayCrawler(HTMLCrawler):
    """
    Scraper for https://www.startuptoday.kr

    Targets the article list on the main page.
    The exact CSS selectors should be adjusted after inspecting the live site.
    """

    def parse(self, html: str) -> list[CrawledItem]:
        soup = BeautifulSoup(html, "lxml")
        items: list[CrawledItem] = []

        # Attempt to find article cards — adjust selectors as needed
        # Common patterns: <article>, .post-item, .news-item, li.item
        article_tags = (
            soup.select("article.post")
            or soup.select(".article-list li")
            or soup.select(".news_list li")
            or soup.select("ul.list li")
        )

        if not article_tags:
            self.logger.warning(
                "StartupTodayCrawler: could not find article elements. "
                "The page structure may have changed."
            )
            return []

        for tag in article_tags:
            # Title + URL
            a_tag = tag.find("a", href=True)
            if not a_tag:
                continue
            title = a_tag.get_text(strip=True)
            url = str(a_tag["href"])
            if url.startswith("/"):
                url = "https://www.startuptoday.kr" + url

            if not title or not url:
                continue

            # Summary (optional)
            summary_tag = tag.find(class_=lambda c: c and "summary" in c.lower()) if tag else None
            raw_summary = summary_tag.get_text(strip=True) if summary_tag else ""
            summary = build_summary(raw_summary) if raw_summary else None

            # Date (optional — fall back to now)
            date_tag = tag.find("time") or tag.find(class_=lambda c: c and "date" in c.lower())
            published_at: datetime
            if date_tag:
                try:
                    dt_str = date_tag.get("datetime") or date_tag.get_text(strip=True)
                    published_at = datetime.fromisoformat(dt_str).replace(tzinfo=timezone.utc)
                except Exception:
                    published_at = datetime.now(tz=timezone.utc)
            else:
                published_at = datetime.now(tz=timezone.utc)

            items.append(
                CrawledItem(
                    title=title,
                    url=url,
                    published_at=published_at,
                    summary=summary,
                )
            )

        return items
