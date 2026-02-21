# Backend Lead 작업 현황

> 마지막 업데이트: 2026-02-21

---

## 완료된 작업

### 1. Open Questions 기술 검토 (2026-02-21)
파일: `.squad/03_architecture/Open_Questions.md`

| 질문 | 결론 |
|------|------|
| Q1. 뉴스 RSS 피드 여부 | Dual-mode 전략 — feedparser 1차 시도 → BeautifulSoup fallback |
| Q2. Threads/LinkedIn 크롤링 | LinkedIn 불가(ToS), Threads는 공식 API로 가능 (P1 범위 조정) |
| Q3. VC 블로그 크롤링 | 카카오벤처스=Brunch, 알토스벤처스=altos.vc (상세 구현 시 확인 필요) |

### 2. 백엔드 기반 구축 완료 (2026-02-21)
경로: `backend/`

**생성된 파일 (46개):**
- `app/main.py` — FastAPI 앱, APScheduler lifespan, CORS, Sentry
- `app/config.py` — pydantic-settings 환경변수 로드
- `app/database.py` — SQLAlchemy async 엔진 + 세션
- `app/redis_client.py` — 캐시 get/set + crawl_lock (Redis NX 패턴)
- `app/models/` — Source, FeedItem, CrawlLog SQLAlchemy 모델
- `app/schemas/` — Pydantic v2 요청/응답 스키마 + Envelope
- `app/api/v1/` — feed, sources, status, search 엔드포인트
- `app/services/` — FeedService(커서 페이지네이션), SearchService, StatusService
- `app/crawlers/` — BaseCrawler, RSSCrawler(완성), HTMLCrawler(기반), PlaywrightCrawler(기반), TextUtils
- `app/crawlers/text_utils.py` — HTML 제거 + 200자 요약 생성
- `alembic/versions/0001_create_initial_tables.py` — 전체 테이블 + 5개 소스 시드
- `requirements.txt`, `Procfile`, `.env.example`, `Dockerfile`

---

## 미완료 항목 (다음 작업)

| 항목 | 우선순위 | 비고 |
|------|---------|------|
| 스타트업투데이 HTML 크롤러 구체 구현 | High | 실제 사이트 CSS 선택자 분석 필요 |
| 카카오벤처스 Playwright 크롤러 구체 구현 | High | Brunch 실제 DOM 구조 분석 필요 |
| 알토스벤처스 HTML 크롤러 구체 구현 | High | altos.vc 블로그 URL 확정 후 구현 (TBD-1) |
| 피드 API 통합 테스트 | Medium | DB + Redis 환경 필요 |
| 한국어 풀텍스트 검색 설정 | Medium | PostgreSQL korean dictionary 설치 여부 확인 (TBD-3) |

---

## 아키텍처 결정 사항

- **크롤러 전략**: Dual-mode (RSS 실패 시 HTML fallback)
- **페이지네이션**: 커서 기반 (`published_at:id` Base64 인코딩)
- **중복 방지**: `feed_items.url` UNIQUE + `INSERT ON CONFLICT DO NOTHING`
- **캐싱**: Redis TTL 60초 (피드), 300초 (상태)
- **스케줄러**: APScheduler In-process (별도 Worker 없음, Railway 무료 티어 대응)

---

## 다른 에이전트에게

- **Frontend Lead**: API Contract는 `.squad/03_architecture/API_Contract.md` 참고. Base URL은 `.env.local`의 `NEXT_PUBLIC_API_BASE_URL` 사용.
- **DevOps**: Railway에 PostgreSQL + Redis + FastAPI를 단일 프로젝트로 배포. `backend/Procfile` 및 `backend/Dockerfile` 준비됨.
- **QA Reviewer**: 테스트 뼈대 `backend/tests/`에 있음. DB/Redis 연결 Mock 처리 필요.
