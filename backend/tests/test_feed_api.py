"""
Tests for GET /api/v1/feed/
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from app.main import app
from app.schemas.feed import FeedItemSchema, FeedPageResponse, FeedSourceSummary


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _make_feed_item(
    id: int = 1,
    title: str = "테스트 기사",
    url: str = "https://example.com/article/1",
    source_type: str = "news",
) -> FeedItemSchema:
    return FeedItemSchema(
        id=id,
        source=FeedSourceSummary(
            id=1,
            name="플래텀",
            slug="platum",
            source_type=source_type,
        ),
        title=title,
        url=url,
        summary="요약 텍스트입니다.",
        author="홍길동",
        published_at=datetime(2026, 2, 21, 12, 0, 0, tzinfo=timezone.utc),
        crawled_at=datetime(2026, 2, 21, 12, 5, 0, tzinfo=timezone.utc),
    )


def _make_page_response(items=None, has_more=False, next_cursor=None) -> FeedPageResponse:
    return FeedPageResponse(
        items=items or [_make_feed_item()],
        next_cursor=next_cursor,
        has_more=has_more,
        limit=20,
    )


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_feed_returns_envelope():
    """Response must follow the { data, error, meta } envelope."""
    mock_page = _make_page_response()

    with patch("app.api.v1.feed.get_feed_page", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_page

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/api/v1/feed/")

    assert resp.status_code == 200
    body = resp.json()
    assert "data" in body
    assert "error" in body
    assert "meta" in body
    assert body["error"] is None


@pytest.mark.asyncio
async def test_feed_default_tab_is_news():
    """Default tab parameter should be 'news'."""
    mock_page = _make_page_response()

    with patch("app.api.v1.feed.get_feed_page", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_page

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            await client.get("/api/v1/feed/")

    call_kwargs = mock_get.call_args.kwargs
    assert call_kwargs["tab"] == "news"


@pytest.mark.asyncio
async def test_feed_tab_vc_blog():
    """vc_blog tab should be accepted."""
    mock_page = _make_page_response(
        items=[_make_feed_item(source_type="vc_blog")]
    )

    with patch("app.api.v1.feed.get_feed_page", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_page

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/api/v1/feed/?tab=vc_blog")

    assert resp.status_code == 200
    body = resp.json()
    assert body["meta"]["tab"] == "vc_blog"


@pytest.mark.asyncio
async def test_feed_limit_max_50():
    """limit > 50 should be rejected with 422."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/api/v1/feed/?limit=100")

    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_feed_cursor_pagination():
    """next_cursor should be returned when has_more is True."""
    mock_page = _make_page_response(
        items=[_make_feed_item(i) for i in range(20)],
        has_more=True,
        next_cursor="dGVzdF9jdXJzb3I=",
    )

    with patch("app.api.v1.feed.get_feed_page", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_page

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/api/v1/feed/")

    body = resp.json()
    assert body["data"]["has_more"] is True
    assert body["data"]["next_cursor"] == "dGVzdF9jdXJzb3I="


@pytest.mark.asyncio
async def test_feed_keyword_filter():
    """keyword query param should be passed to the service."""
    mock_page = _make_page_response()

    with patch("app.api.v1.feed.get_feed_page", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_page

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            await client.get("/api/v1/feed/?keyword=AI")

    call_kwargs = mock_get.call_args.kwargs
    assert call_kwargs["keyword"] == "AI"


@pytest.mark.asyncio
async def test_feed_invalid_tab():
    """Invalid tab value should return 422."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/api/v1/feed/?tab=invalid_tab")

    assert resp.status_code == 422
