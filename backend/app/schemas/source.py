from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class SourceSchema(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str
    slug: str
    source_type: str
    feed_url: str | None
    crawl_strategy: str
    crawl_interval: int
    last_crawled_at: datetime | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class SourceListResponse(BaseModel):
    sources: list[SourceSchema]
    total: int
