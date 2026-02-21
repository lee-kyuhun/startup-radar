from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    source_type: Mapped[str] = mapped_column(
        String(30), nullable=False, comment="news | vc_blog | person_threads"
    )
    feed_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    crawl_strategy: Mapped[str] = mapped_column(
        String(20), nullable=False, default="rss",
        comment="rss | html | playwright | api"
    )
    crawl_interval: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    last_crawled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    metadata_: Mapped[dict] = mapped_column(
        "metadata", JSONB, nullable=False, default=dict
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        server_default=func.now(), onupdate=func.now()
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    feed_items: Mapped[list["FeedItem"]] = relationship(  # noqa: F821
        "FeedItem", back_populates="source", cascade="all, delete-orphan"
    )
    crawl_logs: Mapped[list["CrawlLog"]] = relationship(  # noqa: F821
        "CrawlLog", back_populates="source", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Source id={self.id} slug={self.slug!r}>"
