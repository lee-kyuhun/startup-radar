from __future__ import annotations

from datetime import datetime
from typing import Literal

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
    last_crawled_at: datetime | None
    crawl_status: Literal["success", "failed", "running", "unknown"]


class StatusResponse(BaseModel):
    last_updated_at: datetime | None
    status: Literal["ok", "warning", "error"]
    sources: list[SourceStatusSchema]
