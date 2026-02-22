# Backend Lead 작업 완료 보고서

> 마지막 업데이트: 2026-02-21
> 상태: **빌드 완료 + 로컬 검증 통과**

---

## 1. 작업 요약

| 단계 | 작업 | 상태 |
|------|------|------|
| 1 | Open Questions 기술 검토 | 완료 |
| 2 | 백엔드 기반 구축 (46개 파일) | 완료 |
| 3 | 잔여 크롤러 3종 구현 | 완료 |
| 4 | 로컬 환경 구성 + 통합 실행 검증 | 완료 |

---

## 2. Open Questions 기술 검토

파일: `.squad/03_architecture/Open_Questions.md`

| 질문 | 결론 |
|------|------|
| Q1. 뉴스 RSS 피드 여부 | Dual-mode 전략 — feedparser 1차 시도 → BeautifulSoup fallback |
| Q2. Threads/LinkedIn 크롤링 | LinkedIn 불가(ToS), Threads는 공식 API로 가능 (P1 범위 조정) |
| Q3. VC 블로그 크롤링 | 카카오벤처스=Brunch(Playwright 필수), 알토스벤처스=Prismic API |

---

## 3. 백엔드 기반 구축

경로: `backend/`

### 생성된 파일 (46개)
- `app/main.py` — FastAPI 앱, APScheduler lifespan, CORS, Sentry
- `app/config.py` — pydantic-settings 환경변수 로드
- `app/database.py` — SQLAlchemy async 엔진 + 세션
- `app/redis_client.py` — 캐시 get/set + crawl_lock (Redis NX 패턴)
- `app/models/` — Source, FeedItem, CrawlLog SQLAlchemy 모델
- `app/schemas/` — Pydantic v2 요청/응답 스키마 + Envelope
- `app/api/v1/` — feed, sources, status, search 엔드포인트
- `app/services/` — FeedService(커서 페이지네이션), SearchService, StatusService
- `app/crawlers/` — BaseCrawler, RSSCrawler, HTMLCrawler, PlaywrightCrawler, TextUtils
- `app/crawlers/text_utils.py` — HTML 제거 + 200자 요약 생성
- `alembic/versions/0001_create_initial_tables.py` — 전체 테이블 + 5개 소스 시드
- `requirements.txt`, `Procfile`, `.env.example`, `Dockerfile`

---

## 4. 크롤러 구현 (5종 전체 완료)

### 4-1. RSS 크롤러 (기반 구축 시 완성)

| 소스 | 방식 | 검증 결과 |
|------|------|----------|
| 플래텀 (Platum) | feedparser RSS | 10개 기사 수집 성공 |
| 벤처스퀘어 (VentureSquare) | feedparser RSS | 30개 기사 수집 성공 |

### 4-2. 잔여 크롤러 3종 (추가 구현)

| 크롤러 | 방식 | 구현 세부 | 검증 결과 |
|--------|------|----------|----------|
| StartupTodayCrawler | HTMLCrawler (BeautifulSoup) | `div.item` → `a[href*=articleView]` → `strong.auto-titles` 선택자 | 39개 기사 수집 성공 |
| KakaoVenturesCrawler | PlaywrightCrawler (Chromium) | Brunch(`brunch.co.kr/@kakaoventures`), `a[href*="/@kakaoventures/"]` 선택자 | Playwright 미설치로 런타임 검증 보류 |
| AltosVenturesCrawler | Prismic REST API (httpx) | `altos.cdn.prismic.io/api/v2` → `type=post` 쿼리 | 20개 포트폴리오 투자소식 수집 성공 |

**알토스벤처스 특이사항:**
- altos.vc는 Nuxt.js + Prismic CMS 기반 SPA
- 블로그/인사이트 섹션 없음 → `post` 타입이 포트폴리오 회사 데이터
- 대안: 최근 추가 포트폴리오를 "알토스벤처스 포트폴리오: {회사명}" 형태로 제공

---

## 5. 로컬 환경 구성 + 통합 검증

### 5-1. 인프라 설치
- PostgreSQL 16 (Homebrew) → `startup_radar` 데이터베이스 생성
- Redis 7 (Homebrew) → localhost:6379
- Python 3 venv → `backend/.venv/`
- Alembic 마이그레이션 → 테이블 3개 + 소스 5개 시드 완료

### 5-2. 크롤러 실행 결과 (총 99개 기사)

```
플래텀 RSS:       10개 ✅
벤처스퀘어 RSS:   30개 ✅
스타트업투데이:   39개 ✅
알토스벤처스:     20개 ✅
카카오벤처스:     Playwright 미설치 (스킵)
─────────────────────────
합계:             99개
```

### 5-3. API 엔드포인트 검증

| 엔드포인트 | 메서드 | 결과 |
|-----------|--------|------|
| `/api/v1/feed/` | GET | 커서 페이지네이션 정상 (20개씩) |
| `/api/v1/sources/` | GET | 5개 소스 목록 반환 |
| `/api/v1/status/` | GET | 소스별 last_crawled_at, 크롤 로그 반환 |
| `/api/v1/search/?q=AI` | GET | 키워드 검색 정상 |

### 5-4. 해결한 이슈

| 이슈 | 원인 | 해결 |
|------|------|------|
| SSL CERTIFICATE_VERIFY_FAILED | macOS Python에 SSL 인증서 미설정 | `certifi` 패키지 설치 + `SSL_CERT_FILE` 환경변수 설정 |
| Alembic "role user does not exist" | `.env` 파일이 alembic/env.py에서 자동 로드되지 않음 | `DATABASE_URL` 환경변수 직접 export |
| Brunch curl 빈 응답 | Brunch가 봇 탐지로 HTTP 클라이언트 차단 | Playwright 크롤러로 전환 (설계대로) |
| altos.vc HTML 빈 응답 | Nuxt.js SPA로 서버사이드 렌더링 없음 | Prismic CMS API 직접 호출로 전환 |

---

## 6. 아키텍처 결정 사항

| 항목 | 결정 |
|------|------|
| 크롤러 전략 | Dual-mode (RSS 우선 → HTML/Playwright/API fallback) |
| 페이지네이션 | 커서 기반 (`published_at:id` Base64 인코딩) |
| 중복 방지 | `feed_items.url` UNIQUE + SELECT 존재 체크 후 INSERT |
| 캐싱 | Redis TTL 60초 (피드), 300초 (상태) |
| 스케줄러 | APScheduler In-process (별도 Worker 없음, Railway 무료 티어 대응) |
| 크롤 잠금 | Redis NX 패턴 (분산 락) |

---

## 7. 파일 변경 이력

| 파일 | 작업 |
|------|------|
| `backend/` (46개 파일) | 신규 생성 (기반 구축) |
| `backend/app/crawlers/html_crawler.py` | StartupTodayCrawler 재작성 + AltosVenturesCrawler 추가 |
| `backend/app/crawlers/playwright_crawler.py` | KakaoVenturesCrawler 재작성 (Brunch 타겟) |
| `backend/app/crawlers/manager.py` | AltosVenturesCrawler import + slug 매핑 추가 |
| `backend/.env` | 로컬 개발 환경변수 생성 |
| `.squad/03_architecture/Open_Questions.md` | 기술 검토 답변 작성 |
| `.squad/memory/backend-lead.md` | 본 보고서 |
| `.squad/hired_agents.json` | build_status 업데이트 |
| `CLAUDE.md` | 백엔드 진행 현황 반영 |

---

## 8. 미완료 항목 (다음 단계)

| 항목 | 우선순위 | 비고 |
|------|---------|------|
| Playwright 브라우저 설치 + 카카오벤처스 크롤러 런타임 검증 | High | `playwright install chromium` 실행 필요 |
| 한국어 풀텍스트 검색 설정 | Medium | PostgreSQL korean dictionary 설치 여부 확인 (TBD-3) |
| 피드 API 통합 테스트 작성 | Medium | `backend/tests/` 뼈대 있음, Mock 처리 필요 |
| Railway 배포 | Medium | `Procfile`, `Dockerfile` 준비 완료 |

---

## [PM 전달] Railway 배포 시 DB 초기화 이슈 (2026-02-21)

### 알아야 할 사항

`database.py`의 `engine`이 모듈 로드 시점에 `settings.async_database_url`로 생성됨.
Railway에서 `postgres.railway.internal` DNS가 resolve 안 되면 이 엔진을 사용하는 **모든 DB 작업이 실패**함.

### 영향 받는 코드 경로

1. `seed.py:seed_sources()` → `init_db()` → `engine.begin()` → DNS 에러
2. `manager.py:register_all_crawl_jobs()` → `AsyncSessionFactory()` → DNS 에러
3. `alembic/env.py` → `async_engine_from_config()` → DNS 에러

### 현재 main.py 구조

```
lifespan 시작
  → _run_production_init()
    → subprocess: alembic upgrade head  ← DNS 에러 (rc=1)
    → seed_sources()                     ← DNS 에러
  → register_all_crawl_jobs(scheduler)   ← DNS 에러
  → scheduler.start() (0 jobs)
  → yield (앱 정상 실행, /health OK)
```

### DevOps가 해결하면 코드 변경 불필요

DNS 문제가 해결되면 (외부 URL 사용 등) 현재 코드가 그대로 정상 작동함.
`main.py`의 subprocess 기반 alembic 호출도 정상 동작할 것.

### 검토 요청 사항

DNS 해결 후에도 `seed.py`의 `init_db()` 호출이 적절한지 확인 필요:
- production에서 `Base.metadata.create_all`이 alembic과 충돌하지 않는지
- alembic이 먼저 실행되므로 `init_db()`는 사실상 no-op이 되어야 하지만, 순서 보장 확인

---

## 9. 다른 에이전트에게

- **Frontend Lead**: API Contract는 `.squad/03_architecture/API_Contract.md` 참고. Base URL은 `.env.local`의 `NEXT_PUBLIC_API_BASE_URL` 사용. 백엔드 로컬 실행: `cd backend && uvicorn app.main:app --reload`
- **DevOps**: Railway에 PostgreSQL + Redis + FastAPI를 단일 프로젝트로 배포. `backend/Procfile` 및 `backend/Dockerfile` 준비됨. Playwright 설치는 Dockerfile에 포함됨.
- **QA Reviewer**: 테스트 뼈대 `backend/tests/`에 있음. DB/Redis 연결 Mock 처리 필요. 크롤러 99개 기사 수집 검증 완료 (카카오벤처스 제외).
- **Tech Lead**: 알토스벤처스를 Prismic API 기반으로 변경함. Tech Spec/API Contract에 반영 필요시 알려주세요.
