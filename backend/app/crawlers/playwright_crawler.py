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

KAKAO_VENTURES_BRUNCH_URL = "https://brunch.co.kr/@kakaoventures"
KAKAO_VENTURES_BRUNCH_BASE = "https://brunch.co.kr"


class KakaoVenturesCrawler(PlaywrightCrawler):
    """
    Playwright-based crawler for Kakao Ventures blog on Brunch.

    Target: https://brunch.co.kr/@kakaoventures
    Brunch blocks simple HTTP clients (curl/httpx) with bot detection,
    so we use Playwright with a real browser context.

    Confirmed selectors (Brunch platform, 2026-02-21):
      - Article list container: .wrap_article_list or fallback ul[class*="list"]
      - Article links: a[href*="/@kakaoventures/"]
      - Title: .tit_article or heading tags inside the anchor
    """

    async def crawl(self) -> list[CrawledItem]:
        """Override to use the fixed Brunch URL regardless of source.feed_url."""
        self._brunch_url = KAKAO_VENTURES_BRUNCH_URL
        self.feed_url = KAKAO_VENTURES_BRUNCH_URL
        return await super().crawl()

    async def parse_page(self, page: "Page") -> list[CrawledItem]:
        items: list[CrawledItem] = []

        # Wait for article links to appear
        try:
            await page.wait_for_selector(
                f'a[href*="/@kakaoventures/"]', timeout=20_000
            )
        except Exception:
            self.logger.warning(
                "KakaoVenturesCrawler: article links not found within timeout. "
                "Brunch structure may have changed."
            )
            return []

        # Collect all article anchor elements
        anchors = await page.query_selector_all('a[href*="/@kakaoventures/"]')

        seen_urls: set[str] = set()

        for anchor in anchors:
            try:
                href = await anchor.get_attribute("href") or ""
                if not href:
                    continue

                # Normalise URL
                if href.startswith("/"):
                    href = KAKAO_VENTURES_BRUNCH_BASE + href
                if not href.startswith("http"):
                    continue

                # Skip profile/about pages — only process numbered articles
                # Brunch article URLs look like: //@kakaoventures/123
                if href in seen_urls:
                    continue

                # Try dedicated title element first
                title_el = await anchor.query_selector(
                    ".tit_article, .tit_sub, strong, h2, h3, h4"
                )
                if title_el:
                    title = (await title_el.inner_text()).strip()
                else:
                    title = (await anchor.inner_text()).strip()

                # Skip non-article links (navigation, profile, etc.)
                if not title or len(title) < 4:
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
                self.logger.debug("Error parsing Brunch anchor: %s", exc)
                continue

        self.logger.info("KakaoVenturesCrawler parsed %d items", len(items))
        return items
