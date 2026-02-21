"""Create initial tables and seed data

Revision ID: 0001
Revises:
Create Date: 2026-02-21 00:00:00.000000

"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── sources ───────────────────────────────────────────────────────────────
    op.create_table(
        "sources",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column(
            "source_type",
            sa.String(30),
            nullable=False,
            comment="news | vc_blog | person_threads",
        ),
        sa.Column("feed_url", sa.Text(), nullable=True),
        sa.Column(
            "crawl_strategy",
            sa.String(20),
            nullable=False,
            server_default="rss",
            comment="rss | html | playwright | api",
        ),
        sa.Column("crawl_interval", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("last_crawled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_sources_slug", "sources", ["slug"])

    # ── feed_items ────────────────────────────────────────────────────────────
    op.create_table(
        "feed_items",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("author", sa.String(200), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "crawled_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "raw_metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["source_id"], ["sources.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("url"),
    )
    op.create_index("ix_feed_items_source_id", "feed_items", ["source_id"])
    op.create_index("ix_feed_items_url", "feed_items", ["url"])
    op.create_index("ix_feed_items_published_at", "feed_items", ["published_at"])

    # ── crawl_logs ────────────────────────────────────────────────────────────
    op.create_table(
        "crawl_logs",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="running",
            comment="running | success | failed",
        ),
        sa.Column("items_fetched", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("items_new", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["source_id"], ["sources.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_crawl_logs_source_id", "crawl_logs", ["source_id"])

    # ── Seed data ─────────────────────────────────────────────────────────────
    sources_table = sa.table(
        "sources",
        sa.column("name", sa.String),
        sa.column("slug", sa.String),
        sa.column("source_type", sa.String),
        sa.column("feed_url", sa.Text),
        sa.column("crawl_strategy", sa.String),
        sa.column("crawl_interval", sa.Integer),
        sa.column("is_active", sa.Boolean),
        sa.column("metadata", postgresql.JSONB),
    )

    op.bulk_insert(
        sources_table,
        [
            {
                "name": "플래텀",
                "slug": "platum",
                "source_type": "news",
                "feed_url": "https://platum.kr/feed",
                "crawl_strategy": "rss",
                "crawl_interval": 60,
                "is_active": True,
                "metadata": {},
            },
            {
                "name": "벤처스퀘어",
                "slug": "venturesquare",
                "source_type": "news",
                "feed_url": "https://www.venturesquare.net/feed",
                "crawl_strategy": "rss",
                "crawl_interval": 60,
                "is_active": True,
                "metadata": {},
            },
            {
                "name": "스타트업투데이",
                "slug": "startuptoday",
                "source_type": "news",
                "feed_url": "https://www.startuptoday.kr",
                "crawl_strategy": "html",
                "crawl_interval": 60,
                "is_active": True,
                "metadata": {},
            },
            {
                "name": "카카오벤처스",
                "slug": "kakao-ventures",
                "source_type": "vc_blog",
                "feed_url": None,
                "crawl_strategy": "playwright",
                "crawl_interval": 360,
                "is_active": True,
                "metadata": {},
            },
            {
                "name": "알토스벤처스",
                "slug": "altos-ventures",
                "source_type": "vc_blog",
                "feed_url": None,
                "crawl_strategy": "html",
                "crawl_interval": 360,
                "is_active": True,
                "metadata": {},
            },
        ],
    )


def downgrade() -> None:
    op.drop_table("crawl_logs")
    op.drop_table("feed_items")
    op.drop_table("sources")
