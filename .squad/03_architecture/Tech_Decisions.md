# Tech Decisions: Startup Radar MVP

> 작성: Tech Lead 에이전트 | 날짜: 2026-02-21 | 상태: 확정
> 기준 문서: `.squad/01_planning/PRD.md`, `.squad/02_design/UI_Specs.md`, `.squad/03_architecture/Open_Questions.md`

모든 기술 선택에는 반드시 근거가 있어야 한다. 구두로 결정하지 않는다. 이 파일이 결정의 유일한 기록이다.

---

## TD-001. 백엔드 런타임 — Python + FastAPI

**결정:** Python 3.12 + FastAPI 0.115.x

**근거:**
- Playwright (크롤링), BeautifulSoup (HTML 파싱), feedparser (RSS 파싱) 모두 Python 생태계에서 가장 성숙한 라이브러리
- FastAPI는 asyncio 기반으로 크롤링 I/O 병렬 처리에 유리
- Pydantic v2로 API 요청/응답 스키마 자동 검증 및 OpenAPI 문서 자동 생성
- Railway 배포 환경에서 Python 공식 지원, Dockerfile 없이 Procfile로 배포 가능
- AI 바이브코딩 환경에서 Python 예제 코드가 가장 풍부

**대안 검토:**
- Node.js (Express/Hono): 프론트와 언어 통일 가능하나, Playwright 연동이 Python보다 복잡하고 크롤링 생태계가 상대적으로 빈약
- Go (Gin/Echo): 성능 우수하나 학습 비용 높고 AI 코드 생성 품질이 Python 대비 낮음

**결정일:** 2026-02-21

---

## TD-002. 프론트엔드 프레임워크 — Next.js 14 (App Router)

**결정:** Next.js 14 + App Router + Tailwind CSS v3

**근거:**
- UI Spec에서 탭 전환이 클라이언트 상태로 관리되는 SPA 방식으로 확정 (UI_Specs.md 3-2-A)
- App Router의 서버 컴포넌트로 초기 피드 데이터를 SSR로 제공 → LCP < 2초 목표 달성 (PRD 성공 지표)
- Vercel 배포와 Next.js는 공식 지원 조합으로 배포 복잡도 0
- Tailwind CSS는 UI Spec의 색상 토큰/간격 시스템을 CSS 변수로 직접 매핑 가능
- `next/link`의 prefetch로 검색 결과 페이지 전환 속도 향상

**추가 결정 사항:**
- Pretendard 폰트: `next/font`로 로컬 호스팅 (외부 CDN 의존 제거)
- 상태 관리: Tanstack Query v5 (서버 상태 캐싱, 재요청, 로딩/에러 상태 통합)
- 추가 라이브러리 없음 — Zustand, Redux 미사용 (전역 클라이언트 상태가 탭 선택/키워드 필터뿐)

**결정일:** 2026-02-21

---

## TD-003. 데이터베이스 — PostgreSQL + Redis

**결정:** PostgreSQL 16 + Redis 7

**PostgreSQL 선택 근거:**
- 피드 아이템의 `published_at` 기반 시간순 정렬, 소스/탭 기반 필터링이 관계형 쿼리에 적합
- 향후 사용자(구독 기능, v2)를 추가할 때 관계형 스키마 확장이 자연스러움
- `url` 중복 체크를 위한 UNIQUE 제약 조건 활용
- Railway에서 PostgreSQL 관리형 인스턴스 무료 티어 제공

**Redis 선택 근거:**
- 피드 목록 API 응답 캐싱 (TTL 5분): 크롤링 주기(1시간)와 API 요청 빈도 간 버퍼 역할
- 크롤링 작업 Lock (동일 소스 중복 크롤링 방지)
- 향후 세션 스토어로 재사용 가능 (v2 인증 확장 시)
- Railway에서 Redis 관리형 인스턴스 무료 티어 제공

**결정일:** 2026-02-21

---

## TD-004. 크롤링 전략 — Dual-mode (RSS 우선, HTML 폴백)

**결정:** feedparser 우선 시도 → 실패 시 BeautifulSoup HTML 크롤링 자동 폴백. 동적 JS 렌더링 필요 시에만 Playwright 사용.

**근거:**
- Open_Questions.md Q1 답변 반영: 플래텀/벤처스퀘어는 WordPress 기반으로 RSS 가능성 높음
- RSS가 가능한 소스는 rate limit 걱정 없이 안정적으로 수집 가능
- Playwright는 헤드리스 브라우저 실행으로 메모리/CPU 비용이 높아 필요한 경우에만 사용
- 소스별로 수집 방식을 DB에 기록해 운영 중 전략 변경 가능하도록 설계

**소스별 초기 전략:**
| 소스 | 초기 전략 | 폴백 |
|------|---------|------|
| 플래텀 | feedparser (RSS) | BeautifulSoup |
| 벤처스퀘어 | feedparser (RSS) | BeautifulSoup |
| 스타트업투데이 | BeautifulSoup | Playwright |
| 카카오벤처스 (Brunch) | 비공식 RSS URL 패턴 | Playwright |
| 알토스벤처스 | 구현 시 확인 후 결정 | BeautifulSoup |

**결정일:** 2026-02-21

---

## TD-005. SNS 크롤링 범위 — MVP 제외, Threads API P1 유지

**결정:** MVP(v1.0)에서 인물 SNS 피드 제외. PRD P1-3 및 Open_Questions.md Q2 결정 그대로 따름.

**근거:**
- PRD Out of Scope 명시: 인물 SNS 피드는 P1-3이며 MVP 필수 기능 아님
- UI Spec D-2 확정: 인물 탭 자체를 MVP에서 제거
- LinkedIn: ToS 금지, 법적 리스크로 영구 제외
- Threads: Meta 공식 API 존재하나 앱 등록/심사 필요 → v2에서 처리

**아키텍처적 영향:**
- `sources` 테이블의 `source_type` 컬럼에 `'person_threads'` 값을 미리 예약해 v2 확장에 대비
- 인물(Person) 엔티티 테이블은 스키마에 정의하되 MVP에서는 데이터 미입력

**결정일:** 2026-02-21

---

## TD-006. 인증 아키텍처 — MVP 퍼블릭, v2 확장 대비

**결정:** MVP는 인증 없는 퍼블릭 API. 단, 확장을 고려한 구조로 설계.

**확장 대비 설계 원칙:**
- API 라우터를 `/api/v1/public/` (인증 불필요)와 `/api/v1/user/` (인증 필요, v2)로 경로 분리
- FastAPI Dependency Injection으로 `get_current_user` 의존성을 만들어 두되, MVP에서는 미사용
- DB 스키마에 `users` 테이블 정의 (MVP에서는 비어있음)
- Redis를 세션/토큰 스토어로 활용할 수 있는 구조 유지

**결정일:** 2026-02-21

---

## TD-007. 요약 텍스트 전략 — 백엔드 원문 잘라서 제공

**결정:** 크롤링 시 원문 텍스트에서 첫 200자(한글 기준)를 잘라 `summary` 필드에 저장. AI 요약 없음.

**근거:**
- 비용 0: AI 요약 API (OpenAI 등) 비용 발생 없음
- 구현 단순: 문자열 슬라이싱으로 구현, 장애 포인트 없음
- UI Spec D-3 이관 결정: 프론트에서 잘라서 표시하는 방식 대신 백엔드에서 통일된 길이로 제공
- 향후 AI 요약으로 교체 시 `summary` 필드 값만 변경하면 되므로 API 인터페이스 변경 없음

**구현 규칙:**
- HTML 태그 제거 후 순수 텍스트 기준 200자
- 문장 중간에 잘리지 않도록 최대 200자 내 마지막 마침표/줄바꿈 위치에서 자름
- 200자 미만인 경우 원문 그대로 사용

**결정일:** 2026-02-21

---

## TD-008. 스케줄러 — APScheduler (In-process)

**결정:** FastAPI 앱 내부에 APScheduler를 임베딩하여 크롤링 스케줄 관리.

**근거:**
- Railway 무료 티어에서 별도 Worker 서비스 추가 없이 단일 프로세스로 운용
- Celery + Redis 조합은 과도한 복잡도 (Worker, Beat, Broker 3개 프로세스)
- APScheduler는 FastAPI startup 이벤트에 통합 가능

**스케줄:**
| 작업 | 주기 | 비고 |
|------|------|------|
| 뉴스 미디어 크롤링 | 매 1시간 | PRD P0-2 요구사항 |
| VC 블로그 크롤링 | 매 6시간 | PRD P0-3 요구사항 |
| 오래된 피드 정리 | 매일 새벽 3시 | 30일 지난 아이템 삭제 |

**한계 인식:** 서버 재시작 시 다음 스케줄까지 수집 공백 발생 가능. 운영 규모가 커지면 Celery로 마이그레이션 검토.

**결정일:** 2026-02-21

---

## TD-009. 페이지네이션 — 커서 기반 (Cursor-based)

**결정:** 피드 목록 API는 커서 기반 페이지네이션 사용.

**근거:**
- Tech Lead 에이전트 누적 학습(learnings.md): "뉴스 피드처럼 무한 스크롤이 있는 경우 커서 기반 권장"
- 오프셋 기반은 크롤링으로 새 아이템이 계속 추가될 때 페이지 스킵/중복 문제 발생
- `published_at` + `id`를 커서로 사용: 정렬 기준과 고유성 동시 확보

**커서 형식:** `published_at:id` → Base64 인코딩 → URL 안전 문자열

**결정일:** 2026-02-21

---

## TD-010. API 응답 형식 — 통일된 Envelope

**결정:** 모든 API 응답은 `{ data, error, meta }` 구조를 따름.

**근거:**
- Tech Lead 에이전트 누적 학습(learnings.md): "응답 형식은 `{ data, error, meta }` 구조로 통일"
- 프론트엔드에서 에러 처리 로직을 통일 가능 (Tanstack Query의 `onError` 콜백 일원화)
- `meta`에 페이지네이션 정보(`next_cursor`, `has_more`)를 담아 피드 API와 검색 API 구조 통일

**결정일:** 2026-02-21

---

## TD-011. 배포 환경 — Railway (Backend) + Vercel (Frontend)

**결정:** Backend → Railway, Frontend → Vercel. CI/CD → GitHub Actions.

**근거:**
- PRD 제약 조건: "무료 티어 활용 (Railway/Vercel 무료 플랜 기준 설계)"
- Railway: Python + PostgreSQL + Redis를 단일 프로젝트에서 관리. `railway.json` 또는 `Procfile`로 배포.
- Vercel: Next.js 공식 지원 플랫폼. `git push`만으로 자동 배포.
- GitHub Actions: `main` 브랜치 push 시 테스트 실행 + 자동 배포 트리거

**결정일:** 2026-02-21

---

*Tech Lead 에이전트 작성 | 기준: PRD.md, UI_Specs.md, Open_Questions.md | 다음 갱신: 구현 중 신규 결정 발생 시*
