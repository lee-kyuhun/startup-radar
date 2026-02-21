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

    Confirmed structure (2026-02-21):
      - Article cards: div.item (classes: large | medium | small)
      - Link: <a href="/news/articleView.html?idxno=XXXXX">
      - Title: <strong class="auto-titles ...">
      - Date: not present on list page → use crawled_at
    """

    BASE_URL = "https://www.startuptoday.kr"

    def parse(self, html: str) -> list[CrawledItem]:
        soup = BeautifulSoup(html, "lxml")
        items: list[CrawledItem] = []

        article_divs = soup.select("div.item")
        if not article_divs:
            self.logger.warning(
                "StartupTodayCrawler: div.item not found — page structure may have changed."
            )
            return []

        seen_urls: set[str] = set()

        for div in article_divs:
            a_tag = div.find("a", href=True)
            if not a_tag:
                continue

            href = str(a_tag["href"])
            # Only process article pages
            if "articleView" not in href:
                continue

            url = href if href.startswith("http") else self.BASE_URL + href
            if url in seen_urls:
                continue
            seen_urls.add(url)

            # Title: prefer strong.auto-titles, fall back to link text
            title_tag = a_tag.find("strong", class_=lambda c: c and "auto-titles" in c)
            title = title_tag.get_text(strip=True) if title_tag else a_tag.get_text(strip=True)
            title = title.strip()
            if not title:
                continue

            items.append(
                CrawledItem(
                    title=title,
                    url=url,
                    published_at=datetime.now(tz=timezone.utc),
                    summary=None,
                )
            )

        self.logger.info("StartupTodayCrawler parsed %d items", len(items))
        return items


# ─────────────────────────────────────────────────────────────────────────────
# Concrete implementation: 알토스벤처스 (Prismic API)
# ─────────────────────────────────────────────────────────────────────────────

import httpx  # noqa: E402 — imported here to keep top-level imports clean


class AltosVenturesCrawler(HTMLCrawler):
    """
    Crawls Altos Ventures portfolio updates via the Prismic CMS API.

    altos.vc is a Nuxt.js SPA backed by Prismic (https://altos.cdn.prismic.io).
    There is no editorial blog; instead we surface recently-added portfolio
    companies as "investment news" items.

    Prismic API reference:
      GET https://altos.cdn.prismic.io/api/v2
      GET https://altos.cdn.prismic.io/api/v2/documents/search?ref=<ref>&type=post&orderings=[document.first_publication_date+desc]&pageSize=20
    """

    PRISMIC_API_URL = "https://altos.cdn.prismic.io/api/v2"
    PORTFOLIO_URL_BASE = "https://altos.vc/portfolio"

    async def crawl(self) -> list[CrawledItem]:
        """Override crawl() to use Prismic API directly instead of HTML fetch."""
        self.logger.info("Crawling Altos Ventures via Prismic API")

        headers = {"User-Agent": self.user_agent}

        async with httpx.AsyncClient(headers=headers, timeout=30) as client:
            # Step 1: fetch the master ref
            try:
                meta_resp = await client.get(self.PRISMIC_API_URL)
                meta_resp.raise_for_status()
                meta = meta_resp.json()
            except Exception as exc:
                self.logger.error("Failed to fetch Prismic API meta: %s", exc)
                return []

            master_ref = next(
                (r["ref"] for r in meta.get("refs", []) if r.get("isMasterRef")),
                None,
            )
            if not master_ref:
                self.logger.error("Prismic master ref not found")
                return []

            await self._rate_limit_sleep()

            # Step 2: query latest portfolio additions (type=post)
            try:
                search_resp = await client.get(
                    f"{self.PRISMIC_API_URL}/documents/search",
                    params={
                        "ref": master_ref,
                        "type": "post",
                        "pageSize": 20,
                        "orderings": "[document.first_publication_date desc]",
                    },
                )
                search_resp.raise_for_status()
                data = search_resp.json()
            except Exception as exc:
                self.logger.error("Prismic search failed: %s", exc)
                return []

        return self._parse_prismic_results(data.get("results", []))

    def _parse_prismic_results(self, results: list[dict]) -> list[CrawledItem]:
        items: list[CrawledItem] = []

        for doc in results:
            uid = doc.get("uid", "")
            if not uid:
                continue

            doc_data = doc.get("data", {})

            # Extract company name from `name` rich-text field
            name_field = doc_data.get("name", [])
            if isinstance(name_field, list) and name_field:
                title_text = name_field[0].get("text", "").strip()
            else:
                title_text = uid

            if not title_text:
                continue

            title = f"알토스벤처스 포트폴리오: {title_text}"

            # Company website URL (prefer) or altos.vc portfolio page
            link_field = doc_data.get("link", [])
            company_url: str = ""
            if isinstance(link_field, list) and link_field:
                spans = link_field[0].get("spans", [])
                for span in spans:
                    if span.get("type") == "hyperlink":
                        company_url = span.get("data", {}).get("url", "")
                        break
            url = company_url or f"{self.PORTFOLIO_URL_BASE}/{uid}"

            # Summary from `content` or `one_liner`
            one_liner = doc_data.get("one_liner", [])
            content_field = doc_data.get("content", [])
            raw_text = ""
            for field in (one_liner, content_field):
                if isinstance(field, list) and field:
                    raw_text = field[0].get("text", "")
                    if raw_text:
                        break

            summary = build_summary(raw_text) if raw_text else None

            # Date: first_publication_date
            pub_date_str = doc.get("first_publication_date", "")
            try:
                from datetime import datetime, timezone
                published_at = datetime.fromisoformat(
                    pub_date_str.replace("Z", "+00:00")
                )
            except Exception:
                published_at = datetime.now(tz=timezone.utc)

            # location as metadata
            location = doc_data.get("location")
            raw_metadata = {"uid": uid, "location": location}

            items.append(
                CrawledItem(
                    title=title,
                    url=url,
                    published_at=published_at,
                    summary=summary,
                    raw_metadata=raw_metadata,
                )
            )

        self.logger.info("AltosVenturesCrawler parsed %d items", len(items))
        return items

    def parse(self, html: str) -> list[CrawledItem]:
        # Not used — crawl() is overridden directly
        return []
