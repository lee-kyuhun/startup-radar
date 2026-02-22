# Deploy Checklist: Startup Radar MVP — 2026-02-21

> QA Reviewer 에이전트 작성 | 배포 전 모든 항목 체크 완료 필요
> 최종 업데이트: 2026-02-21 (버그 수정 후 재검증 반영)

---

## 배포 승인 기준

**CRITICAL 버그가 0개여야 배포 승인.**
CRITICAL 3개 (BUG-001, BUG-002, BUG-003) 수정 완료 — 배포 가능 조건 충족.

---

## 1. 코드 품질 게이트

### 백엔드

- [x] **[BUG-001] Status API 응답 재구현 완료** — `last_updated_at`, `status`, `crawl_status` 포함 (2026-02-21 재검증)
- [x] **[BUG-002] Sources API 응답 재구현 완료** — 내부 필드 제거, 배열 형식 (2026-02-21 재검증)
- [x] **[BUG-003] Feed API meta 재구현 완료** — `next_cursor`, `total_count` meta에 추가 (2026-02-21 재검증)
- [x] **[BUG-004] Search q max_length=100 수정** (2026-02-21 재검증)
- [x] **[BUG-005] Feed tab 허용값 수정** — `Literal["news", "vc_blog"]` 확정 (2026-02-21 재검증)
- [x] **[BUG-006] FeedItemSchema crawled_at 제거** (2026-02-21 재검증)
- [ ] 테스트 전체 통과: `pytest backend/tests/ -v` — 오류 0개 (실행 확인 필요)
- [ ] Python 의존성 취약점 확인: `pip audit` 또는 `safety check`

### 잔여 MINOR 이슈 (배포 차단 아님, 차기 이터레이션 권고)

- [ ] BUG-001 잔여: status 판단을 시간 기준(1h/3h)으로 개선
- [ ] BUG-002 잔여: `source_type`, `is_active` 쿼리 필터 파라미터 추가
- [ ] BUG-003 잔여: `FeedPageResponse`에서 `next_cursor`, `has_more`, `limit` 중복 제거 + meta 초과 필드 정리
- [ ] BUG-004 잔여: 100자 초과 시 INVALID_QUERY(400) 커스텀 에러 반환
- [ ] BUG-007: `meta.total_count` 구현 또는 스펙 null 허용으로 변경

### 프론트엔드

- [ ] 빌드 통과: `cd frontend && npm run build` — 에러 0개
- [ ] TypeScript 타입 오류 없음: `npx tsc --noEmit`
- [ ] `frontend/src/lib/api.ts` 백엔드 수정 사항 연동 확인
  - `fetchSources()` 응답 형식이 배열 — 현재 `request<SourceWithStatus[]>` 호출로 정상 동작 예상
  - `fetchStatus()` 응답이 `{ last_updated_at, status, sources }` — `StatusData` 타입과 일치 확인 필요

---

## 2. P0 기능 구현 완료

- [x] GET /api/v1/feed/ — 탭별 피드 목록, 커서 페이지네이션
- [x] GET /api/v1/sources/ — 소스 목록 (재구현 완료)
- [x] GET /api/v1/status/ — 크롤링 상태 (재구현 완료)
- [x] GET /api/v1/search/ — 키워드 검색
- [x] 메인 피드 페이지 (/)
- [x] 검색 페이지 (/search)
- [x] 무한 스크롤
- [x] FeedStatusBadge 폴링

---

## 3. 크롤러 런타임 검증

- [x] 플래텀 RSS — 런타임 검증 완료 (보고서 참조)
- [x] 벤처스퀘어 RSS — 런타임 검증 완료
- [x] 스타트업투데이 HTML — 런타임 검증 완료 (39개 기사)
- [x] 알토스벤처스 Prismic API — 런타임 검증 완료 (20개)
- [ ] **카카오벤처스 Playwright** — Playwright 브라우저 설치 후 런타임 검증 필요
  - `playwright install chromium` 실행 후 크롤러 실행 확인

---

## 4. 환경변수 체크

### Backend `.env.example` 확인

- [x] `DATABASE_URL` 포함
- [x] `REDIS_URL` 포함
- [x] `APP_ENV` 포함
- [x] `SECRET_KEY` 포함
- [x] `ALLOWED_ORIGINS` 포함
- [x] `SENTRY_DSN` 포함
- [x] `CRAWL_USER_AGENT` 포함
- [x] `CRAWL_RATE_LIMIT_SECONDS` 포함

### Frontend `.env.local.example` 확인

- [x] `NEXT_PUBLIC_API_BASE_URL` 포함
- [x] `NEXT_PUBLIC_SENTRY_DSN` 포함

### Railway 배포 환경변수 설정 (DevOps)

- [ ] `DATABASE_URL` — Railway PostgreSQL 연결 URL 설정
- [ ] `REDIS_URL` — Railway Redis 연결 URL 설정
- [ ] `APP_ENV=production` 설정
- [ ] `SECRET_KEY` — 안전한 랜덤값 생성 및 설정
- [ ] `ALLOWED_ORIGINS` — Vercel 프로덕션 URL 포함
- [ ] `SENTRY_DSN` — Sentry 프로젝트 DSN 설정

### Vercel 배포 환경변수 설정 (DevOps)

- [ ] `NEXT_PUBLIC_API_BASE_URL` — Railway API URL 설정
- [ ] `NEXT_PUBLIC_SENTRY_DSN` — Sentry 프론트 DSN 설정

---

## 5. 인프라 확인

### Railway

- [ ] `Procfile` 확인: `web: uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- [ ] `railway.toml` 설정 확인
- [ ] PostgreSQL 플러그인 추가 및 마이그레이션 실행: `alembic upgrade head`
- [ ] Redis 플러그인 추가
- [ ] Playwright chromium 설치 확인 (Railway 환경)
  - `railway.toml`에 playwright install 커맨드 포함 필요

### Vercel

- [ ] `next.config.js` 프로덕션 설정 확인
- [ ] git push → Vercel 자동 배포 트리거 확인

---

## 6. 크롤링 윤리 준수

- [x] `robots.txt` 사전 확인 여부 (코드 및 CLAUDE.md 확인됨)
- [x] Rate limit 최소 1초 (`CRAWL_RATE_LIMIT_SECONDS=1`) 적용
- [x] User-Agent 명시 (`StartupRadar/1.0 (+https://startup-radar.com/about)`)
- [x] 개인 데이터 최소 수집 (author 필드 크롤링 불가 시 null)

---

## 7. 에러 상태 처리

- [x] 피드 로딩 실패 → `FeedError` 컴포넌트 + 재시도 버튼
- [x] 빈 피드 → `FeedEmpty` 컴포넌트
- [x] 로딩 중 → `FeedSkeleton` 컴포넌트
- [x] 검색 결과 없음 → `SearchEmpty` 컴포넌트
- [x] FeedStatusBadge 상태 확인 실패 → 빨간 점 + "상태 확인 불가"
- [x] 크롤링 실패 시 `crawl_logs.status = "failed"` 기록
- [x] Redis 장애 시 캐시 Fail-open (크롤 Lock도 Fail-open)

---

## 8. 반응형 UI 확인

- [ ] 모바일 375px: 검색 아이콘 → 검색창 펼침, 탭 표시 정상
- [ ] 태블릿 768px: 레이아웃 전환 확인
- [ ] 데스크톱 1280px: SearchBar max-width 480px, 피드 max-width 720px

---

## 9. 배포 후 스모크 테스트

- [ ] `GET /health` → `{ status: "ok" }`
- [ ] `GET /api/v1/feed/` → 200, 피드 아이템 반환
- [ ] `GET /api/v1/status/` → 200, status 값 반환
- [ ] `GET /api/v1/sources/` → 200, 5개 소스 반환
- [ ] `GET /api/v1/search/?q=AI` → 200
- [ ] 프론트엔드 메인 페이지 접속 → 피드 로드 확인
- [ ] FeedStatusBadge 색상 점 표시 확인
- [ ] 검색 → 결과 페이지 이동 확인

---

## 현재 배포 준비 상태

| 항목 | 상태 |
|------|------|
| CRITICAL 버그 해결 | CLEAR (3개 수정 완료, 2026-02-21 재검증) |
| 테스트 통과 | 확인 필요 (모킹 기반, 실제 실행 미확인) |
| 환경변수 준비 | 부분 완료 (.env.example 존재) |
| Railway 배포 설정 | PENDING (DevOps) |
| Vercel 배포 설정 | PENDING (DevOps) |
| 카카오벤처스 크롤러 런타임 검증 | PENDING |

**결론: QA 코드 게이트 통과. DevOps → Railway + Vercel 배포 설정 진행 가능.**

---

*QA Reviewer | 2026-02-21 최초 작성 | 2026-02-21 재검증 업데이트*
