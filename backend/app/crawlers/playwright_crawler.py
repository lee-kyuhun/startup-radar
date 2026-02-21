from __future__ import annotations

import logging
from abc import abstractmethod
from datetime import datetime, timezone

from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from app.crawlers.base import BaseCrawler, CrawledItem
from app.crawlers.text_utils import build_summary

logger = logging.getLogger(__name__)


class PlaywrightCrawler(BaseCrawler):
    """
    Base class for JavaScript-heavy sites that require a headless browser.

    Subclasses implement `parse_page(page)` to extract items from a Playwright Page.
    """

    async def crawl(self) -> list[CrawledItem]:
        if not self.feed_url:
            self.logger.warning("No feed_url configured for source=%s", self.source_slug)
            return []

        self.logger.info("Crawling with Playwright: %s", self.feed_url)

        items: list[CrawledItem] = []

        async with async_playwright() as pw:
            browser: Browser = await pw.chromium.launch(headless=True)
            context: BrowserContext = await browser.new_context(
                user_agent=self.user_agent,
                locale="ko-KR",
            )
            page: Page = await context.new_page()

            try:
                await page.goto(self.feed_url, wait_until="networkidle", timeout=60_000)
                await self._rate_limit_sleep()
                items = await self.parse_page(page)
            except Exception as exc:
                self.logger.error(
                    "Playwright error for %s: %s", self.source_slug, exc, exc_info=True
                )
            finally:
                await context.close()
                await browser.close()

        self.logger.info("Fetched %d items from %s", len(items), self.source_slug)
        return items

    @abstractmethod
    async def parse_page(self, page: "Page") -> list[CrawledItem]:
        """Extract items from the loaded Playwright page."""
        ...


# ─────────────────────────────────────────────────────────────────────────────
# Concrete implementation: 카카오벤처스 블로그
# ─────────────────────────────────────────────────────────────────────────────

KAKAO_VENTURES_URL = "https://www.kakaoventures.com/blog"


class KakaoVenturesCrawler(PlaywrightCrawler):
    """
    Playwright-based crawler for Kakao Ventures blog.
    The page is rendered via React/Next.js — hence Playwright is required.

    Selectors should be verified against the live site and adjusted as needed.
    """

    async def parse_page(self, page: "Page") -> list[CrawledItem]:
        items: list[CrawledItem] = []

        # Wait for article cards to appear
        try:
            await page.wait_for_selector("a[href]", timeout=15_000)
        except Exception:
            self.logger.warning("KakaoVenturesCrawler: selector timeout — page may have changed")
            return []

        # Collect candidate article links
        anchors = await page.query_selector_all("article a, .post-card a, .blog-list a")
        if not anchors:
            anchors = await page.query_selector_all("a[href*='/blog/']")

        seen_urls: set[str] = set()

        for anchor in anchors:
            try:
                href = await anchor.get_attribute("href") or ""
                if not href or href in seen_urls:
                    continue
                if href.startswith("/"):
                    href = "https://www.kakaoventures.com" + href

                # Try to get the title from the anchor or a nearby heading
                title = (await anchor.inner_text()).strip()
                if not title:
                    heading = await anchor.query_selector("h1, h2, h3, h4")
                    if heading:
                        title = (await heading.inner_text()).strip()
                if not title:
                    continue

                seen_urls.add(href)
                items.append(
                    CrawledItem(
                        title=title,
                        url=href,
                        published_at=datetime.now(tz=timezone.utc),
                        summary=None,
                    )
                )
            except Exception as exc:
                self.logger.debug("Error parsing anchor: %s", exc)
                continue

        return items
