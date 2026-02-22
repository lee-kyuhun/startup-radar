from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class FeedSourceSummary(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str
    slug: str
    source_type: str


class FeedItemSchema(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    source: FeedSourceSummary
    title: str
    url: str
    summary: str | None
    author: str | None
    published_at: datetime
