"""
Tests for crawler utilities and text processing.
"""
from __future__ import annotations

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from app.crawlers.text_utils import build_summary, strip_html, normalize_whitespace, truncate_to_sentence


# ── text_utils tests ──────────────────────────────────────────────────────────

class TestStripHtml:
    def test_removes_tags(self):
        assert strip_html("<p>Hello <b>world</b></p>") == "Hello world"

    def test_empty_string(self):
        result = strip_html("")
        assert result.strip() == ""

    def test_nested_tags(self):
        html = "<div><h1>제목</h1><p>본문 <a href='#'>링크</a></p></div>"
        result = strip_html(html)
        assert "<" not in result
        assert "제목" in result
        assert "본문" in result

    def test_plain_text_unchanged(self):
        text = "아무 태그 없는 텍스트"
        result = strip_html(text)
        assert "아무 태그" in result


class TestNormalizeWhitespace:
    def test_collapses_spaces(self):
        assert normalize_whitespace("a   b") == "a b"

    def test_collapses_tabs(self):
        assert normalize_whitespace("a\t\tb") == "a b"

    def test_collapses_newlines(self):
        result = normalize_whitespace("a\n\n\n\nb")
        assert "\n\n" not in result

    def test_strips_leading_trailing(self):
        assert normalize_whitespace("  hello  ") == "hello"


class TestTruncateToSentence:
    def test_short_text_unchanged(self):
        text = "짧은 텍스트."
        assert truncate_to_sentence(text) == text

    def test_truncates_at_period(self):
        # Build a long text with a period before max_length
        text = "첫 번째 문장입니다. " + "x" * 300
        result = truncate_to_sentence(text, max_length=200)
        assert len(result) <= 200
        assert result.endswith(".")

    def test_hard_cut_when_no_boundary(self):
        text = "x" * 300  # No periods or newlines
        result = truncate_to_sentence(text, max_length=200)
        assert len(result) == 200

    def test_exact_length_not_truncated(self):
        text = "a" * 200
        assert truncate_to_sentence(text, max_length=200) == text


class TestBuildSummary:
    def test_none_input_returns_none(self):
        assert build_summary(None) is None

    def test_empty_string_returns_none(self):
        assert build_summary("") is None

    def test_only_whitespace_returns_none(self):
        assert build_summary("   ") is None

    def test_html_is_stripped(self):
        result = build_summary("<p>안녕하세요.</p>")
        assert result is not None
        assert "<p>" not in result
        assert "안녕하세요" in result

    def test_long_text_truncated(self):
        long_text = "가" * 500
        result = build_summary(long_text)
        assert result is not None
        assert len(result) <= 200

    def test_summary_with_period_cut(self):
        # Should cut at last period within 200 chars
        text = "첫 문장." + "두 번째 문장." + "x" * 300
        result = build_summary(text)
        assert result is not None
        assert len(result) <= 200


# ── RSSCrawler tests ──────────────────────────────────────────────────────────

class TestRSSCrawler:
    @pytest.mark.asyncio
    async def test_crawl_returns_items_on_valid_feed(self):
        """RSSCrawler should parse feed entries into CrawledItem objects."""
        from app.crawlers.rss_crawler import RSSCrawler

        mock_feed = MagicMock()
        mock_feed.bozo = False
        mock_entry = MagicMock()
        mock_entry.title = "테스트 기사"
        mock_entry.link = "https://platum.kr/archives/12345"
        mock_entry.summary = "기사 요약입니다."
        mock_entry.author = "홍길동"
        mock_entry.published_parsed = (2026, 2, 21, 10, 0, 0, 4, 52, 0)
        mock_entry.updated_parsed = None
        mock_entry.content = []
        mock_entry.tags = []
        mock_entry.id = "https://platum.kr/archives/12345"
        mock_feed.entries = [mock_entry]

        crawler = RSSCrawler(
            source_id=1,
            source_slug="platum",
            feed_url="https://platum.kr/feed",
        )

        with patch("feedparser.parse", return_value=mock_feed):
            items = await crawler.crawl()

        assert len(items) == 1
        assert items[0].title == "테스트 기사"
        assert items[0].url == "https://platum.kr/archives/12345"
        assert items[0].author == "홍길동"

    @pytest.mark.asyncio
    async def test_crawl_skips_entry_without_url(self):
        """Entries without a link should be skipped."""
        from app.crawlers.rss_crawler import RSSCrawler

        mock_feed = MagicMock()
        mock_feed.bozo = False
        mock_entry = MagicMock()
        mock_entry.title = "링크 없는 기사"
        mock_entry.link = ""  # No URL
        mock_entry.summary = ""
        mock_entry.content = []
        mock_entry.tags = []
        mock_entry.published_parsed = None
        mock_entry.updated_parsed = None
        mock_entry.published = None
        mock_entry.updated = None
        mock_feed.entries = [mock_entry]

        crawler = RSSCrawler(
            source_id=1,
            source_slug="platum",
            feed_url="https://platum.kr/feed",
        )

        with patch("feedparser.parse", return_value=mock_feed):
            items = await crawler.crawl()

        assert items == []

    @pytest.mark.asyncio
    async def test_crawl_returns_empty_when_no_feed_url(self):
        """Crawler with no feed_url should return empty list."""
        from app.crawlers.rss_crawler import RSSCrawler

        crawler = RSSCrawler(source_id=1, source_slug="test", feed_url=None)
        items = await crawler.crawl()
        assert items == []

    @pytest.mark.asyncio
    async def test_crawl_returns_empty_on_bozo_with_no_entries(self):
        """Bozo feed with no entries should return empty list."""
        from app.crawlers.rss_crawler import RSSCrawler

        mock_feed = MagicMock()
        mock_feed.bozo = True
        mock_feed.bozo_exception = Exception("Parse error")
        mock_feed.entries = []

        crawler = RSSCrawler(
            source_id=1,
            source_slug="broken",
            feed_url="https://broken.example.com/feed",
        )

        with patch("feedparser.parse", return_value=mock_feed):
            items = await crawler.crawl()

        assert items == []


# ── Crawl lock tests ──────────────────────────────────────────────────────────

class TestCrawlLock:
    @pytest.mark.asyncio
    async def test_acquire_returns_true_on_success(self):
        from app.redis_client import acquire_crawl_lock

        mock_redis = AsyncMock()
        mock_redis.set = AsyncMock(return_value=True)

        with patch("app.redis_client.get_redis", return_value=mock_redis):
            result = await acquire_crawl_lock(source_id=1)

        assert result is True

    @pytest.mark.asyncio
    async def test_acquire_returns_false_when_locked(self):
        from app.redis_client import acquire_crawl_lock

        mock_redis = AsyncMock()
        mock_redis.set = AsyncMock(return_value=None)  # NX failed

        with patch("app.redis_client.get_redis", return_value=mock_redis):
            result = await acquire_crawl_lock(source_id=1)

        assert result is False
