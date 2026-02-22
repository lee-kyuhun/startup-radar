# Tech Spec: Startup Radar — MVP v1.0 (v1.1 반영)

> 작성: Tech Lead 에이전트 | 날짜: 2026-02-21 | 수정: 2026-02-22 (v1.1) | 상태: 수정 반영
> 기준 문서: `.squad/01_planning/PRD.md (v1.1)`, `.squad/02_design/UI_Specs.md`
> 상세 문서: `API_Contract.md`, `DB_Schema.md`, `Tech_Decisions.md`

---

## 1. 기술 스택 (확정)

| 영역 | 기술 | 버전 | 선택 근거 |
|------|------|------|---------|
| Backend Runtime | Python | 3.12 | 크롤링 생태계 최강. Playwright, BeautifulSoup, feedparser 모두 Python 최우선 지원 |
| Backend Framework | FastAPI | 0.115.x | asyncio 기반 I/O 병렬 처리. Pydantic v2로 스키마 자동 검증. OpenAPI 자동 생성 |
| Frontend Framework | Next.js | 14 (App Router) | SSR로 LCP < 2초 목표 달성. Vercel 공식 지원 조합 |
| Frontend Styling | Tailwind CSS | v3 | UI Spec 색상 토큰/간격 시스템을 CSS 변수로 직접 매핑 |
| 프론트 상태 관리 | Tanstack Query | v5 | 서버 상태 캐싱, 페이지네이션(keepPreviousData), 로딩/에러 상태 통합 |
| 주 데이터베이스 | PostgreSQL | 16 | 관계형 필터링, UNIQUE 제약, v2 확장에 자연스러운 스키마 |
| 캐시 / Lock | Redis | 7 | 피드 API 응답 캐싱(TTL 5분), 크롤링 중복 방지 Lock |
| HTML 크롤링 | BeautifulSoup | 4.x | 정적 HTML 파싱 표준 라이브러리 |
| 동적 크롤링 | Playwright | 1.x | JS 렌더링 필요한 소스에만 선택적 사용 |
| RSS 파싱 | feedparser | 6.x | RSS/Atom 파싱 표준 |
| 스케줄러 | APScheduler | 3.x | FastAPI In-process 통합. Railway 단일 프로세스 운용 |
| DB 마이그레이션 | Alembic | 1.x | SQLAlchemy 표준 마이그레이션 도구 |
| 폰트 | Pretendard | — | UI Spec 한글 최적화 폰트. `next/font` 로컬 호스팅 |
| Backend 배포 | Railway | — | Python + PostgreSQL + Redis 단일 프로젝트 관리. 무료 티어 |
| Frontend 배포 | Vercel | — | Next.js 공식 플랫폼. `git push` 자동 배포 |
| CI/CD | GitHub Actions | — | main 브랜치 push 시 테스트 + 자동 배포 트리거 |
| 에러 모니터링 | Sentry | — | PRD 기술 스택 명시. Backend + Frontend 모두 연동 |

---

## 2. 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────┐
│                    사용자 브라우저                         │
│          Next.js 14 (App Router) — Vercel               │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌────────────────────────┐│
│  │ MainPage │  │SearchPage│  │ GlobalHeader (Sticky)  ││
│  │ TabNav   │  │ FeedList │  │ SearchBar, StatusBadge ││
│  │ FeedList │  │          │  │                        ││
│  └────┬─────┘  └────┬─────┘  └──────────┬─────────────┘│
└───────┼─────────────┼──────────────────┼──────────────┘
        │  HTTPS REST │                  │ /api/v1/status/
        │             │                  │
┌───────▼─────────────▼──────────────────▼──────────────┐
│             FastAPI 서버 — Railway                      │
│                                                        │
│  ┌─────────────────────────────────────────────────┐   │
│  │              API Routers (/api/v1/)             │   │
│  │  /feed/   /sources/   /status/   /search/      │   │
│  └──────────────────┬──────────────────────────────┘   │
│                     │                                   │
│  ┌──────────────────▼──────────────────────────────┐   │
│  │              Service Layer                      │   │
│  │  FeedService  SearchService  StatusService      │   │
│  └──────┬────────────────────────────┬─────────────┘   │
│         │                            │                  │
│  ┌──────▼──────┐            ┌────────▼────────┐        │
│  │  PostgreSQL │            │     Redis        │        │
│  │  (Railway)  │            │    (Railway)     │        │
│  └─────────────┘            └─────────────────┘        │
│                                                        │
│  ┌──────────────────────────────────────────────────┐  │
│  │           Crawler Engine (APScheduler)           │  │
│  │                                                  │  │
│  │  ┌──────────────┐  ┌──────────────────────────┐  │  │
│  │  │ FeedParser   │  │  BeautifulSoup / Playwright│  │  │
│  │  │ (RSS)        │  │  (HTML 크롤링)             │  │  │
│  │  └──────┬───────┘  └────────────┬─────────────┘  │  │
│  │         └──────────────┬────────┘                │  │
│  │                ┌───────▼────────┐                │  │
│  │                │ CrawlerManager │                │  │
│  │                │ (Dual-mode)    │                │  │
│  │                └───────┬────────┘                │  │
│  │                        │ → feed_items INSERT     │  │
│  │                        │ → crawl_logs INSERT     │  │
│  └────────────────────────┼─────────────────────────┘  │
│                           │                             │
│                    ┌──────▼──────┐                      │
│                    │  PostgreSQL │                      │
│                    └─────────────┘                      │
└────────────────────────────────────────────────────────┘

외부 소스 (크롤링 대상)
 ├── platum.kr (RSS)
 ├── venturesquare.net (RSS)
 ├── startuptoday.kr (HTML)
 ├── brunch.co.kr/@kakaoventures (Playwright)
 └── altos.vc (HTML/TBD)
```

---

## 3. 백엔드 디렉토리 구조

```
backend/
├── app/
│   ├── main.py                  # FastAPI 앱 진입점. APScheduler 초기화.
│   ├── config.py                # 환경변수 로드 (pydantic-settings)
│   ├── database.py              # SQLAlchemy 엔진, 세션 의존성
│   ├── redis_client.py          # Redis 연결 및 캐시 유틸리티
│   │
│   ├── api/
│   │   ├── v1/
│   │   │   ├── router.py        # v1 라우터 집합 (/api/v1/)
│   │   │   ├── feed.py          # GET /api/v1/feed/
│   │   │   ├── sources.py       # GET /api/v1/sources/
│   │   │   ├── status.py        # GET /api/v1/status/
│   │   │   └── search.py        # GET /api/v1/search/
│   │   └── deps.py              # 공통 의존성 (DB 세션, 페이지네이션 파라미터)
│   │
│   ├── models/
│   │   ├── source.py            # Source SQLAlchemy 모델
│   │   ├── feed_item.py         # FeedItem SQLAlchemy 모델
│   │   └── crawl_log.py         # CrawlLog SQLAlchemy 모델
│   │
│   ├── schemas/
│   │   ├── feed.py              # FeedItem 요청/응답 Pydantic 스키마
│   │   ├── source.py            # Source 응답 Pydantic 스키마
│   │   ├── status.py            # Status 응답 Pydantic 스키마
│   │   └── common.py            # Envelope, Pagination 공통 스키마
│   │
│   ├── services/
│   │   ├── feed_service.py      # 피드 조회 비즈니스 로직
│   │   ├── search_service.py    # 검색 비즈니스 로직
│   │   └── status_service.py    # 크롤링 상태 조회 로직
│   │
│   └── crawlers/
│       ├── manager.py           # CrawlerManager (소스별 전략 선택, Lock 관리)
│       ├── base.py              # 크롤러 추상 기반 클래스
│       ├── rss_crawler.py       # feedparser 기반 RSS 크롤러
│       ├── html_crawler.py      # BeautifulSoup 기반 HTML 크롤러
│       ├── playwright_crawler.py# Playwright 기반 동적 크롤러
│       └── text_utils.py        # HTML 태그 제거, 200자 요약 생성 (TD-007)
│
├── alembic/
│   ├── env.py
│   └── versions/
│       └── 0001_create_initial_tables.py
│
├── tests/
│   ├── test_feed_api.py
│   ├── test_search_api.py
│   └── test_crawlers.py
│
├── requirements.txt
├── Procfile                     # Railway 배포: web: uvicorn app.main:app
└── .env.example
```

---

## 4. 프론트엔드 디렉토리 구조

```
frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx           # 루트 레이아웃. GlobalHeader 포함. Pretendard 폰트.
│   │   ├── page.tsx             # 메인 피드 페이지 (/)
│   │   └── search/
│   │       └── page.tsx         # 검색 결과 페이지 (/search?q=...)
│   │
│   ├── components/
│   │   ├── layout/
│   │   │   ├── GlobalHeader.tsx
│   │   │   ├── Logo.tsx
│   │   │   ├── SearchBar.tsx
│   │   │   └── FeedStatusBadge.tsx
│   │   │
│   │   ├── feed/
│   │   │   ├── TabNav.tsx
│   │   │   ├── FeedList.tsx
│   │   │   ├── FeedItem.tsx
│   │   │   ├── SourceTag.tsx
│   │   │   ├── FeedSkeleton.tsx
│   │   │   ├── FeedEmpty.tsx
│   │   │   └── FeedError.tsx
│   │   │
│   │   └── filter/
│   │       ├── FilterBar.tsx    # P1
│   │       └── FilterTag.tsx    # P1
│   │
│   ├── lib/
│   │   ├── api.ts               # API 클라이언트 (fetch wrapper)
│   │   ├── queries.ts           # Tanstack Query queryFn 정의
│   │   ├── formatDate.ts        # published_at → "N분 전" 변환 (D-4 반영)
│   │   └── constants.ts         # TAB 타입, 색상 토큰 매핑 등
│   │
│   └── types/
│       └── api.ts               # API_Contract.md의 응답 타입 TypeScript 정의
│
├── tailwind.config.ts           # UI Spec 색상 토큰 커스텀 확장
├── package.json
└── .env.local.example
```

---

## 5. API 계약 요약

상세 스펙: `API_Contract.md` 참고.

| 엔드포인트 | 메서드 | 용도 | 우선순위 |
|-----------|--------|------|---------|
| `/api/v1/feed/` | GET | 탭별 피드 목록 (오프셋 페이지네이션) | P0 |
| `/api/v1/sources/` | GET | 등록 소스 목록 | P0 |
| `/api/v1/status/` | GET | 크롤링 상태 (StatusBadge용) | P0 |
| `/api/v1/search/` | GET | 키워드 검색 | P1 |

**응답 Envelope:**
```json
{ "data": ..., "error": null | { "code": "...", "message": "..." }, "meta": ... }
```

**피드 오프셋 페이지네이션 (v1.1):** `page` + `limit` 파라미터. 응답 meta에 `current_page`, `total_pages`, `total_count`, `has_prev`, `has_next` 포함.

---

## 6. 데이터 모델 요약

상세 스펙: `DB_Schema.md` 참고.

| 테이블 | MVP 사용 | 핵심 역할 |
|--------|---------|---------|
| `sources` | 사용 | 크롤링 소스 등록. 초기 5개 시드. |
| `feed_items` | 사용 | 수집된 피드 아이템. `url` UNIQUE로 중복 방지. |
| `crawl_logs` | 사용 | 크롤링 이력. StatusBadge 업데이트 시각 계산. |
| `persons` | 스키마만 | v2 인물 피드 대비 |
| `users` | 스키마만 | v2 인증/구독 대비 |

---

## 7. 크롤링 상세 설계

### 수집 주기 및 전략

| 소스 | 주기 | 전략 | 폴백 |
|------|------|------|------|
| 플래텀 | 1시간 | RSS (feedparser) | BeautifulSoup |
| 벤처스퀘어 | 1시간 | RSS (feedparser) | BeautifulSoup |
| 스타트업투데이 | 1시간 | BeautifulSoup | Playwright |
| 카카오벤처스 | 6시간 | Playwright | — |
| 알토스벤처스 | 6시간 | BeautifulSoup | Playwright |

### 요약 텍스트 생성 규칙 (TD-007)

1. 원문 HTML에서 모든 태그 제거 → 순수 텍스트 추출
2. 연속 공백/줄바꿈 정규화
3. 200자 이내 마지막 마침표(`.`, `。`) 또는 줄바꿈 위치에서 자름
4. 해당 경계가 없으면 200자에서 강제 자름
5. 결과가 비어있으면 `summary = null`

### 중복 방지

- `feed_items.url`에 UNIQUE 제약
- INSERT 시 `ON CONFLICT (url) DO NOTHING` 사용
- Redis `crawl_lock:{source_id}` 로 동시 크롤링 방지

### 크롤링 윤리 준수 (PRD 제약 조건)

- 모든 소스 `robots.txt` 사전 확인 후 구현
- 요청 간격: 최소 1초 (`asyncio.sleep(1)`)
- User-Agent 명시: `StartupRadar/1.0 (+https://startup-radar.com/about)`

---

## 8. 인증 아키텍처 (확장 대비)

MVP는 인증 없음. 향후 확장을 위한 구조를 미리 잡아둔다.

### 경로 분리 전략

```
/api/v1/feed/          ← 퍼블릭 (인증 불필요)
/api/v1/search/        ← 퍼블릭 (인증 불필요)
/api/v1/sources/       ← 퍼블릭 (인증 불필요)
/api/v1/status/        ← 퍼블릭 (인증 불필요)
/api/v1/user/...       ← 인증 필요 (v2, 현재 404)
```

### FastAPI 의존성 구조 (미리 정의)

```python
# app/api/deps.py
async def get_current_user_optional():
    """MVP에서는 항상 None 반환. v2에서 JWT 검증 로직 추가."""
    return None

async def get_current_user_required():
    """v2에서 JWT 검증 후 User 객체 반환. 미인증 시 401."""
    raise HTTPException(status_code=401)
```

### Redis 세션 예약

Redis 키 `session:{token}` 패턴을 v2 세션 스토어로 예약. MVP에서는 미사용.

---

## 9. 기술 제약 조건

| 제약 | 내용 | 출처 |
|------|------|------|
| 예산 | Railway + Vercel 무료 티어 기준 설계 | PRD 제약 조건 |
| 크롤링 | 모든 소스 robots.txt 준수 필수 | PRD 제약 조건 |
| 크롤링 | Rate limit: 요청 간격 최소 1초 | PRD 제약 조건 |
| 개인정보 | SNS 크롤링 시 개인 데이터 최소 수집 | PRD 제약 조건 |
| 인증 | MVP에서 인증 없음 (퍼블릭 서비스) | 사용자 확정 |
| 요약 | AI 요약 없음, 원문 200자 잘라서 제공 | 사용자 확정 |
| 인물 피드 | MVP에서 인물 탭 제거 (SNS 크롤링 미포함) | UI Spec D-2, 사용자 확정 |
| 스케줄러 | APScheduler In-process (별도 Worker 없음) | Railway 무료 티어 제약 |
| 성능 | LCP < 2초 (PRD 성공 지표) | PRD 성공 지표 |
| 성능 | 페이지 전환 속도 < 1초 (이전/다음 페이지 클릭 후 콘텐츠 표시까지) | PRD v1.1 성공 지표 |

---

## 10. 환경변수 목록

**Backend (`.env`):**

```
# Database
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/startup_radar

# Redis
REDIS_URL=redis://default:password@host:6379

# App
APP_ENV=production          # development | production
SECRET_KEY=...              # v2 JWT 서명용 (미리 생성)
ALLOWED_ORIGINS=https://startup-radar.vercel.app

# Sentry
SENTRY_DSN=...

# Crawling
CRAWL_USER_AGENT=StartupRadar/1.0 (+https://startup-radar.com/about)
CRAWL_RATE_LIMIT_SECONDS=1
```

**Frontend (`.env.local`):**

```
NEXT_PUBLIC_API_BASE_URL=https://api.startup-radar.com
NEXT_PUBLIC_SENTRY_DSN=...
```

---

## 11. 미결 결정 사항 (TBD)

| # | 항목 | 담당 | 기한 |
|---|------|------|------|
| TBD-1 | 알토스벤처스 실제 블로그 URL 확인 및 크롤링 전략 확정 | Backend Lead | 첫 크롤러 구현 시 |
| TBD-2 | 카카오벤처스 Brunch 비공식 RSS URL 패턴 동작 여부 검증 | Backend Lead | 첫 크롤러 구현 시 |
| TBD-3 | PostgreSQL 풀텍스트 검색 한국어 설정 (`korean` dictionary 설치 여부) | Backend Lead | 검색 기능 구현 시 |
| TBD-4 | Railway 무료 티어에서 APScheduler + Playwright 메모리 한도 충족 여부 | DevOps | 배포 시 |
| TBD-5 | Sentry 무료 티어 이벤트 한도 검토 | DevOps | 배포 시 |

---

## 12. 구현 우선순위

### Phase 2 구현 순서 (빌드 게이트 진입 후)

1. **백엔드 기반 구축** — FastAPI 앱 초기화, DB 마이그레이션, 소스 시드
2. **뉴스 크롤러** — 플래텀 RSS 크롤러 (Ephemeral Agent)
3. **피드 API** — `GET /api/v1/feed/` 구현 (Backend Lead → Ephemeral Agent)
4. **프론트엔드 기반** — Next.js 초기화, 디자인 시스템 (Tailwind 토큰 설정)
5. **피드 UI** — FeedList, FeedItem, TabNav, StatusBadge (Frontend Lead → Ephemeral Agent)
6. **추가 크롤러** — 벤처스퀘어, 스타트업투데이, VC 블로그
7. **검색 기능** — `GET /api/v1/search/`, SearchPage (P1)
8. **배포** — Railway + Vercel CI/CD 구성

---

## 승인 체크리스트

- [ ] 기술 스택이 PRD 요구사항과 충돌하지 않는가?
- [ ] 크롤링 전략이 PRD 데이터 소스 목록을 모두 커버하는가?
- [ ] DB 스키마가 API 응답 필드를 모두 지원하는가?
- [ ] 인증 없는 구조가 PRD Out of Scope와 일치하는가?
- [ ] v2 확장 경로(인증, 구독, 인물 피드)가 아키텍처에 반영됐는가?
- [ ] 환경변수 목록이 완전한가?
- [ ] 사용자가 "Tech Spec 승인"을 선언했는가?

---

---

## 변경 이력 (Changelog)

| 버전 | 날짜 | 변경 내용 | 사유 |
|------|------|----------|------|
| v1.0 | 2026-02-21 | 초안 작성 | - |
| v1.1 | 2026-02-22 | 페이지네이션 방식 변경 반영 | PRD v1.1: 무한 스크롤 → 페이지네이션 |

### v1.1 변경 상세

**변경 범위:** 기술 스택 설명, API 계약 요약, 기술 제약 조건

**주요 변경:**
1. **Tanstack Query 사용 방식 변경**: `useInfiniteQuery` (무한 스크롤) → `useQuery` + `keepPreviousData` (페이지 단위 조회)
2. **API 계약**: 커서 기반 → 오프셋 기반 페이지네이션. `page`/`limit` 파라미터, `current_page`/`total_pages`/`total_count`/`has_prev`/`has_next` 응답 meta.
3. **성능 제약 추가**: 페이지 전환 속도 < 1초 (PRD v1.1 성공 지표)
4. **Redis 캐시 키**: `feed:{tab}:{cursor}` → `feed:{tab}:p{page}:l{limit}`

**백엔드 기술 결정 (오프셋 기반 전환 시 고려사항):**
- SQL 쿼리: `ORDER BY published_at DESC OFFSET {(page-1)*limit} LIMIT {limit}`
- `COUNT(*)` 쿼리를 별도 실행하여 `total_count` 산출 (Redis 캐싱으로 부하 완화)
- 크롤링으로 새 아이템 추가 시 오프셋 밀림 가능성 있으나, PRD 요구사항(페이지 번호 표시/공유)이 우선하므로 수용
- `published_at DESC, id DESC` 정렬로 동일 시각 아이템 정렬 안정성 확보

**프론트엔드 기술 결정:**
- 페이지 상태를 URL 쿼리 파라미터(`?tab=news&page=3`)로 관리하여 페이지 공유/북마크 지원
- 탭 전환 시 `page=1`로 리셋 (PRD v1.1 명시)
- `keepPreviousData: true`로 페이지 전환 시 이전 데이터 유지하여 깜빡임 방지 → 페이지 전환 속도 < 1초 목표 달성 지원

---

*Tech Lead 에이전트 작성 | 2026-02-22 (v1.1) | 다음 단계: 사용자 승인 → hired_agents.json gates.tech_spec_approved = true → 빌드 게이트 진입*
