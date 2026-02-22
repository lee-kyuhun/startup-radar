"""
Tests for GET /api/v1/search/ (offset-based pagination, v1.1)
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from datetime import datetime, timezone

from app.main import app
from app.schemas.feed import FeedItemSchema, FeedSourceSummary


def _make_feed_item(
    id: int = 1,
    title: str = "AI 스타트업 투자 유치",
) -> dict:
    schema = FeedItemSchema(
        id=id,
        source=FeedSourceSummary(
            id=1, name="플래텀", slug="platum", source_type="news"
        ),
        title=title,
        url=f"https://example.com/article/{id}",
        summary="AI 관련 스타트업이 시리즈 A 투자를 유치했습니다.",
        author=None,
        published_at=datetime(2026, 2, 21, 10, 0, 0, tzinfo=timezone.utc),
    )
    return schema.model_dump(mode="json")


def _make_service_return(items=None, total_count=None):
    """Return value for the mocked search_feed_items: (items, total_count)."""
    if items is None:
        items = [_make_feed_item()]
    if total_count is None:
        total_count = len(items)
    return (items, total_count)


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_search_requires_q():
    """Missing 'q' parameter should return INVALID_QUERY error."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/api/v1/search/")

    assert resp.status_code == 400
    body = resp.json()
    assert body["error"]["code"] == "INVALID_QUERY"


@pytest.mark.asyncio
async def test_search_returns_results():
    """Valid keyword should return matching items with pagination meta."""
    with patch("app.api.v1.search.search_feed_items", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = _make_service_return()

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/api/v1/search/?q=AI")

    assert resp.status_code == 200
    body = resp.json()
    assert body["error"] is None
    assert len(body["data"]) == 1
    meta = body["meta"]
    assert meta["current_page"] == 1
    assert meta["total_count"] == 1


@pytest.mark.asyncio
async def test_search_empty_results():
    """No matches should return empty items list, not an error."""
    with patch("app.api.v1.search.search_feed_items", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = _make_service_return(items=[], total_count=0)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/api/v1/search/?q=존재하지않는키워드")

    assert resp.status_code == 200
    body = resp.json()
    assert body["data"] == []
    assert body["error"] is None
    assert body["meta"]["total_count"] == 0
    assert body["meta"]["total_pages"] == 0


@pytest.mark.asyncio
async def test_search_limit_capped_at_50():
    """limit > 50 should be rejected."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/api/v1/search/?q=AI&limit=200")

    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_search_page_pagination():
    """page parameter should be forwarded to the service."""
    with patch("app.api.v1.search.search_feed_items", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = _make_service_return(items=[], total_count=0)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            await client.get("/api/v1/search/?q=스타트업&page=2")

    call_kwargs = mock_search.call_args.kwargs
    assert call_kwargs["page"] == 2


@pytest.mark.asyncio
async def test_search_q_empty_string():
    """Empty 'q' string should return INVALID_QUERY."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/api/v1/search/?q=")

    assert resp.status_code == 400
    body = resp.json()
    assert body["error"]["code"] == "INVALID_QUERY"


@pytest.mark.asyncio
async def test_search_q_too_long():
    """Query longer than 100 chars should return INVALID_QUERY."""
    long_q = "가" * 101
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get(f"/api/v1/search/?q={long_q}")

    assert resp.status_code == 400
    body = resp.json()
    assert body["error"]["code"] == "INVALID_QUERY"


@pytest.mark.asyncio
async def test_search_pagination_meta():
    """Meta should contain offset-based pagination fields."""
    items = [_make_feed_item(i) for i in range(10)]
    with patch("app.api.v1.search.search_feed_items", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = _make_service_return(items=items, total_count=25)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/api/v1/search/?q=스타트업&page=1&limit=10")

    body = resp.json()
    meta = body["meta"]
    assert meta["current_page"] == 1
    assert meta["total_pages"] == 3  # ceil(25/10)
    assert meta["total_count"] == 25
    assert meta["limit"] == 10
    assert meta["has_prev"] is False
    assert meta["has_next"] is True
