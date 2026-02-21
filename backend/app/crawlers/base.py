from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class CrawledItem:
    """Normalised output from any crawler strategy."""
    title: str
    url: str
    published_at: datetime
    summary: str | None = None
    author: str | None = None
    raw_metadata: dict = field(default_factory=dict)


class BaseCrawler(ABC):
    """Abstract base for all crawler strategies."""

    def __init__(self, source_id: int, source_slug: str, feed_url: str | None) -> None:
        self.source_id = source_id
        self.source_slug = source_slug
        self.feed_url = feed_url
        self.rate_limit = settings.CRAWL_RATE_LIMIT_SECONDS
        self.user_agent = settings.CRAWL_USER_AGENT
        self.logger = logging.getLogger(f"{__name__}.{source_slug}")

    @abstractmethod
    async def crawl(self) -> list[CrawledItem]:
        """Fetch and return a list of CrawledItem objects."""
        ...

    async def _rate_limit_sleep(self) -> None:
        """Enforce minimum request interval."""
        await asyncio.sleep(self.rate_limit)
