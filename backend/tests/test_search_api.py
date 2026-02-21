"""
Tests for GET /api/v1/search/
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from datetime import datetime, timezone

from app.main import app
from app.schemas.feed import FeedItemSchema, FeedPageResponse, FeedSourceSummary


def _make_feed_item(
    id: int = 1,
    title: str = "AI 스타트업 투자 유치",
) -> FeedItemSchema:
    return FeedItemSchema(
        id=id,
        source=FeedSourceSummary(
            id=1, name="플래텀", slug="platum", source_type="news"
        ),
        title=title,
        url=f"https://example.com/article/{id}",
        summary="AI 관련 스타트업이 시리즈 A 투자를 유치했습니다.",
        author=None,
        published_at=datetime(2026, 2, 21, 10, 0, 0, tzinfo=timezone.utc),
        crawled_at=datetime(2026, 2, 21, 10, 5, 0, tzinfo=timezone.utc),
    )


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_search_requires_q():
    """Missing 'q' parameter should return 422."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/api/v1/search/")

    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_search_returns_results():
    """Valid keyword should return matching items."""
    mock_page = FeedPageResponse(
        items=[_make_feed_item()],
        next_cursor=None,
        has_more=False,
        limit=20,
    )

    with patch("app.api.v1.search.search_feed_items", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = mock_page

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/api/v1/search/?q=AI")

    assert resp.status_code == 200
    body = resp.json()
    assert body["error"] is None
    assert len(body["data"]["items"]) == 1
    assert body["meta"]["query"] == "AI"


@pytest.mark.asyncio
async def test_search_empty_results():
    """No matches should return empty items list, not an error."""
    mock_page = FeedPageResponse(
        items=[],
        next_cursor=None,
        has_more=False,
        limit=20,
    )

    with patch("app.api.v1.search.search_feed_items", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = mock_page

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/api/v1/search/?q=존재하지않는키워드")

    assert resp.status_code == 200
    body = resp.json()
    assert body["data"]["items"] == []
    assert body["error"] is None


@pytest.mark.asyncio
async def test_search_limit_capped_at_50():
    """limit > 50 should be rejected."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/api/v1/search/?q=AI&limit=200")

    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_search_offset_pagination():
    """offset parameter should be forwarded to the service."""
    mock_page = FeedPageResponse(items=[], next_cursor=None, has_more=False, limit=20)

    with patch("app.api.v1.search.search_feed_items", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = mock_page

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            await client.get("/api/v1/search/?q=스타트업&offset=40")

    call_kwargs = mock_search.call_args.kwargs
    assert call_kwargs["offset"] == 40


@pytest.mark.asyncio
async def test_search_source_type_filter():
    """source_type parameter should be forwarded to the service."""
    mock_page = FeedPageResponse(items=[], next_cursor=None, has_more=False, limit=20)

    with patch("app.api.v1.search.search_feed_items", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = mock_page

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            await client.get("/api/v1/search/?q=투자&source_type=vc_blog")

    call_kwargs = mock_search.call_args.kwargs
    assert call_kwargs["source_type"] == "vc_blog"


@pytest.mark.asyncio
async def test_search_q_min_length():
    """Empty 'q' string should be rejected."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/api/v1/search/?q=")

    assert resp.status_code == 422
