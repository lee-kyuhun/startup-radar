from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class CrawlLogSchema(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    source_id: int
    started_at: datetime
    finished_at: datetime | None
    status: str
    items_fetched: int
    items_new: int
    error_message: str | None
    created_at: datetime


class SourceStatusSchema(BaseModel):
    source_id: int
    source_name: str
    source_slug: str
    last_crawled_at: datetime | None
    latest_log: CrawlLogSchema | None


class StatusResponse(BaseModel):
    sources: list[SourceStatusSchema]
    total_sources: int
    active_sources: int
