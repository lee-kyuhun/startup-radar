"""
초기 소스 데이터 시드 스크립트
PRD 섹션 6 (정보 소스) 기준

실행:
  python -m app.scripts.seed
"""
from __future__ import annotations

import asyncio
import logging

from sqlalchemy import select

from app.database import AsyncSessionFactory, init_db
from app.models.source import Source

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SOURCES: list[dict] = [
    # ── 뉴스 미디어 (P0-2) ────────────────────────────────────────────────────
    {
        "name": "플래텀",
        "slug": "platum",
        "source_type": "news",
        "feed_url": "https://platum.kr/feed",
        "crawl_strategy": "rss",
        "crawl_interval": 60,  # 1시간
        "is_active": True,
        "metadata_": {"site_url": "https://platum.kr", "language": "ko"},
    },
    {
        "name": "벤처스퀘어",
        "slug": "venturesquare",
        "source_type": "news",
        "feed_url": "https://www.venturesquare.net/feed",
        "crawl_strategy": "rss",
        "crawl_interval": 60,
        "is_active": True,
        "metadata_": {"site_url": "https://www.venturesquare.net", "language": "ko"},
    },
    {
        "name": "스타트업투데이",
        "slug": "startuptoday",
        "source_type": "news",
        "feed_url": "https://www.startuptoday.kr",
        "crawl_strategy": "html",
        "crawl_interval": 60,
        "is_active": True,
        "metadata_": {"site_url": "https://www.startuptoday.kr", "language": "ko"},
    },
    # ── VC 블로그 (P0-3) ──────────────────────────────────────────────────────
    {
        "name": "카카오벤처스 블로그",
        "slug": "kakao-ventures",
        "source_type": "vc_blog",
        "feed_url": "https://brunch.co.kr/@kakaoventures",
        "crawl_strategy": "playwright",
        "crawl_interval": 360,  # 6시간
        "is_active": True,
        "metadata_": {
            "site_url": "https://brunch.co.kr/@kakaoventures",
            "language": "ko",
            "note": "비공식 Brunch RSS 실패 시 Playwright 크롤링",
        },
    },
    {
        "name": "카카오벤처스 뉴스레터",
        "slug": "kakao-ventures-newsletter",
        "source_type": "vc_blog",
        "feed_url": "https://kakaovc.stibee.com",
        "crawl_strategy": "html",
        "crawl_interval": 360,
        "is_active": True,
        "metadata_": {
            "site_url": "https://kakaovc.stibee.com",
            "language": "ko",
            "note": "Stibee 아카이브 페이지 크롤링",
        },
    },
    {
        "name": "알토스벤처스",
        "slug": "altos-ventures",
        "source_type": "vc_blog",
        "feed_url": "https://altos.vc",
        "crawl_strategy": "html",
        "crawl_interval": 360,
        "is_active": True,
        "metadata_": {
            "site_url": "https://altos.vc",
            "language": "ko",
            "note": "robots.txt 확인 후 크롤링 전략 확정 필요 (TBD-1)",
        },
    },
]


async def seed_sources() -> None:
    await init_db()

    async with AsyncSessionFactory() as session:
        inserted = 0
        skipped = 0

        for data in SOURCES:
            result = await session.execute(
                select(Source).where(Source.slug == data["slug"])
            )
            existing = result.scalar_one_or_none()

            if existing:
                logger.info("SKIP (already exists): %s", data["slug"])
                skipped += 1
                continue

            source = Source(**data)
            session.add(source)
            inserted += 1
            logger.info("INSERT: %s", data["slug"])

        await session.commit()

    logger.info("Seed complete — inserted=%d skipped=%d", inserted, skipped)


if __name__ == "__main__":
    asyncio.run(seed_sources())
