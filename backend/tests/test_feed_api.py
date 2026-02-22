"""
Tests for GET /api/v1/feed/ (offset-based pagination, v1.1)
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from datetime import datetime, timezone

from app.main import app
from app.schemas.feed import FeedItemSchema, FeedSourceSummary


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _make_feed_item(
    id: int = 1,
    title: str = "테스트 기사",
    url: str = "https://example.com/article/1",
    source_type: str = "news",
) -> dict:
    schema = FeedItemSchema(
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
    )
    return schema.model_dump(mode="json")


def _make_service_return(items=None, total_count=None):
    """Return value for the mocked get_feed_page: (items, total_count)."""
    if items is None:
        items = [_make_feed_item()]
    if total_count is None:
        total_count = len(items)
    return (items, total_count)


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_feed_returns_envelope():
    """Response must follow the { data, error, meta } envelope."""
    with patch("app.api.v1.feed.get_feed_page", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = _make_service_return()

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
    with patch("app.api.v1.feed.get_feed_page", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = _make_service_return()

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            await client.get("/api/v1/feed/")

    call_kwargs = mock_get.call_args.kwargs
    assert call_kwargs["tab"] == "news"


@pytest.mark.asyncio
async def test_feed_tab_vc_blog():
    """vc_blog tab should be accepted."""
    with patch("app.api.v1.feed.get_feed_page", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = _make_service_return(
            items=[_make_feed_item(source_type="vc_blog")]
        )

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/api/v1/feed/?tab=vc_blog")

    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_feed_limit_max_50():
    """limit > 50 should be rejected with 422."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/api/v1/feed/?limit=100")

    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_feed_offset_pagination_meta():
    """Meta should contain offset-based pagination fields."""
    items = [_make_feed_item(i, url=f"https://example.com/article/{i}") for i in range(20)]
    with patch("app.api.v1.feed.get_feed_page", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = _make_service_return(items=items, total_count=45)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/api/v1/feed/?page=1&limit=20")

    body = resp.json()
    meta = body["meta"]
    assert meta["current_page"] == 1
    assert meta["total_pages"] == 3  # ceil(45/20)
    assert meta["total_count"] == 45
    assert meta["limit"] == 20
    assert meta["has_prev"] is False
    assert meta["has_next"] is True


@pytest.mark.asyncio
async def test_feed_page_param_forwarded():
    """page parameter should be forwarded to the service."""
    with patch("app.api.v1.feed.get_feed_page", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = _make_service_return()

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            await client.get("/api/v1/feed/?page=3")

    call_kwargs = mock_get.call_args.kwargs
    assert call_kwargs["page"] == 3


@pytest.mark.asyncio
async def test_feed_keyword_filter():
    """keyword query param should be passed to the service."""
    with patch("app.api.v1.feed.get_feed_page", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = _make_service_return()

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


@pytest.mark.asyncio
async def test_feed_default_page_is_1():
    """Default page parameter should be 1."""
    with patch("app.api.v1.feed.get_feed_page", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = _make_service_return()

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            await client.get("/api/v1/feed/")

    call_kwargs = mock_get.call_args.kwargs
    assert call_kwargs["page"] == 1
