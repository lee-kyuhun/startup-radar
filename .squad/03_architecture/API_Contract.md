# API Contract: Startup Radar MVP

> 작성: Tech Lead 에이전트 | 날짜: 2026-02-21 | 수정: 2026-02-22 (v1.1) | 상태: 수정 반영
> 기준 문서: `PRD.md (v1.1)`, `UI_Specs.md`, `DB_Schema.md`, `Tech_Decisions.md`
> Base URL: `https://api.startup-radar.com` (개발: `http://localhost:8000`)

이 문서가 프론트엔드와 백엔드 간의 유일한 계약이다.
프론트엔드는 이 스펙을 기준으로 구현하고, 백엔드는 이 스펙을 벗어나는 응답을 내려서는 안 된다.

---

## 공통 규칙

### 응답 Envelope (TD-010)

모든 API 응답은 아래 구조를 따른다.

```json
{
  "data": { ... } | [ ... ] | null,
  "error": null | { "code": "ERROR_CODE", "message": "사람이 읽을 수 있는 메시지" },
  "meta": { ... } | null
}
```

- 성공 시: `data`에 페이로드, `error`는 `null`
- 실패 시: `data`는 `null`, `error`에 코드와 메시지
- `meta`는 페이지네이션 정보 등 부가 데이터

### HTTP 상태 코드

| 코드 | 사용 상황 |
|------|---------|
| 200 | 성공 |
| 400 | 잘못된 요청 (파라미터 형식 오류 등) |
| 404 | 리소스 없음 |
| 422 | 입력 유효성 검증 실패 (FastAPI 기본) |
| 429 | Rate limit 초과 |
| 500 | 서버 내부 오류 |

### API 버전 및 경로

- 모든 엔드포인트: `/api/v1/` prefix
- 퍼블릭 (인증 불필요): `/api/v1/feed/`, `/api/v1/search/`, `/api/v1/sources/`, `/api/v1/status/`
- 사용자 전용 (v2, 현재 미구현): `/api/v1/user/`

### 페이지네이션 (TD-009, v1.1 변경)

> **v1.1 변경 (2026-02-22):** PRD v1.1에서 무한 스크롤 → 페이지네이션으로 UI 방식이 변경됨에 따라, API도 커서 기반에서 오프셋 기반으로 전환한다. 페이지 번호 표시, 전체 페이지 수 계산, 이전/다음 페이지 탐색을 위해 오프셋 기반이 필수적이다.

피드 목록 및 검색 결과는 오프셋 기반 페이지네이션을 사용한다.

**요청 파라미터:**
- `page`: 조회할 페이지 번호. 1부터 시작. 기본값 1.
- `limit`: 한 페이지에 표시할 아이템 수. 기본값 20, 최대 50.

**응답 meta:**
```json
{
  "meta": {
    "current_page": 1,
    "total_pages": 15,
    "total_count": 293,
    "limit": 20,
    "has_prev": false,
    "has_next": true
  }
}
```

- `current_page`: 현재 페이지 번호 (1-indexed).
- `total_pages`: 전체 페이지 수. `ceil(total_count / limit)`.
- `total_count`: 필터 조건에 맞는 전체 아이템 수.
- `limit`: 요청된 페이지당 아이템 수.
- `has_prev`: 이전 페이지 존재 여부. `current_page > 1`.
- `has_next`: 다음 페이지 존재 여부. `current_page < total_pages`.

### 공통 에러 코드

| `error.code` | HTTP | 설명 |
|-------------|------|------|
| `INVALID_PAGE` | 400 | page가 1 미만이거나 total_pages 초과 |
| `INVALID_LIMIT` | 400 | limit이 1~50 범위 밖 |
| `INVALID_QUERY` | 400 | 검색어가 비어있거나 너무 김 (최대 100자) |
| `SOURCE_NOT_FOUND` | 404 | 해당 소스 없음 |
| `INTERNAL_ERROR` | 500 | 서버 내부 오류 |

---

## 엔드포인트 목록

| 메서드 | 경로 | 설명 | 우선순위 |
|--------|------|------|---------|
| GET | `/api/v1/feed/` | 통합 피드 목록 (탭 기반) | P0 |
| GET | `/api/v1/sources/` | 등록된 소스 목록 | P0 |
| GET | `/api/v1/status/` | 피드 업데이트 상태 (StatusBadge용) | P0 |
| GET | `/api/v1/search/` | 키워드 검색 | P1 |

---

## GET /api/v1/feed/

통합 피드 메인 페이지용 엔드포인트. 탭(소스 유형)별로 필터링된 피드 아이템을 반환한다.

### 요청

**Query Parameters:**

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---------|------|------|-------|------|
| `tab` | string | 선택 | `"news"` | 탭 필터. `"news"` 또는 `"vc_blog"` |
| `page` | integer | 선택 | `1` | 페이지 번호 (1부터 시작) |
| `limit` | integer | 선택 | `20` | 페이지당 아이템 수 (1~50) |
| `keyword` | string | 선택 | — | 키워드 필터 (P1). 제목+요약에서 부분 일치 검색 |

**`tab` 허용 값:**

| 값 | 설명 | source_type 매핑 |
|----|------|----------------|
| `"news"` | 뉴스 미디어 피드 | `source_type = 'news'` |
| `"vc_blog"` | VC 블로그 피드 | `source_type = 'vc_blog'` |

> UI Spec D-2: 인물 탭은 MVP에서 제외. `tab=person` 요청 시 400 반환.

**요청 예시:**
```
GET /api/v1/feed/?tab=news
GET /api/v1/feed/?tab=news&page=1&limit=20
GET /api/v1/feed/?tab=vc_blog&page=3&limit=20
GET /api/v1/feed/?tab=news&keyword=AI&page=1
```

### 응답

**성공 (200):**

```json
{
  "data": [
    {
      "id": 123,
      "source": {
        "id": 1,
        "name": "플래텀",
        "slug": "platum",
        "source_type": "news"
      },
      "title": "카카오벤처스, AI 헬스케어 스타트업 A에 100억 투자",
      "url": "https://platum.kr/archives/12345",
      "summary": "카카오벤처스가 인공지능 기반 의료진단 솔루션을 개발하는 스타트업 A사에 시리즈A 100억 원 투자를 완료했다고 밝혔다.",
      "author": null,
      "published_at": "2026-02-21T12:00:00Z"
    },
    {
      "id": 122,
      "source": {
        "id": 2,
        "name": "벤처스퀘어",
        "slug": "venturesquare",
        "source_type": "news"
      },
      "title": "2026년 1분기 국내 스타트업 투자 현황 분석",
      "url": "https://www.venturesquare.net/articles/12345",
      "summary": "2026년 1분기 국내 스타트업 투자 규모가 전년 동기 대비 15% 증가한 것으로 나타났다.",
      "author": "홍길동 기자",
      "published_at": "2026-02-21T10:30:00Z"
    }
  ],
  "error": null,
  "meta": {
    "current_page": 1,
    "total_pages": 15,
    "total_count": 293,
    "limit": 20,
    "has_prev": false,
    "has_next": true
  }
}
```

**`data` 아이템 필드 정의:**

| 필드 | 타입 | Nullable | 설명 |
|------|------|---------|------|
| `id` | integer | No | 피드 아이템 고유 ID |
| `source.id` | integer | No | 소스 ID |
| `source.name` | string | No | 소스 표시 이름 (UI SourceTag에 표시) |
| `source.slug` | string | No | 소스 슬러그 |
| `source.source_type` | string | No | `"news"` 또는 `"vc_blog"` |
| `title` | string | No | 기사/포스트 제목 |
| `url` | string | No | 원본 링크 (새 탭 오픈용) |
| `summary` | string | Yes | 원문 첫 200자 (HTML 제거 후). 없으면 `null` |
| `author` | string | Yes | 작성자. 크롤링에서 파싱 불가 시 `null` |
| `published_at` | string (ISO 8601) | No | 발행 시각. 항상 UTC (`Z` suffix) |

**실패 (400 — 잘못된 tab 값):**
```json
{
  "data": null,
  "error": {
    "code": "INVALID_TAB",
    "message": "tab은 'news' 또는 'vc_blog'만 허용됩니다."
  },
  "meta": null
}
```

---

## GET /api/v1/sources/

등록된 크롤링 소스 목록을 반환한다. 프론트엔드에서 SourceTag 색상 매핑 등에 활용.

### 요청

**Query Parameters:**

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---------|------|------|-------|------|
| `source_type` | string | 선택 | — | 타입 필터. 생략 시 전체 반환 |
| `is_active` | boolean | 선택 | `true` | 활성 소스만 반환 여부 |

**요청 예시:**
```
GET /api/v1/sources/
GET /api/v1/sources/?source_type=news
```

### 응답

**성공 (200):**

```json
{
  "data": [
    {
      "id": 1,
      "name": "플래텀",
      "slug": "platum",
      "source_type": "news",
      "is_active": true
    },
    {
      "id": 2,
      "name": "벤처스퀘어",
      "slug": "venturesquare",
      "source_type": "news",
      "is_active": true
    },
    {
      "id": 4,
      "name": "카카오벤처스",
      "slug": "kakao-ventures",
      "source_type": "vc_blog",
      "is_active": true
    }
  ],
  "error": null,
  "meta": null
}
```

> `crawl_strategy`, `feed_url`, `metadata` 등 내부 운영 필드는 응답에서 제외.

---

## GET /api/v1/status/

피드 최종 업데이트 시각을 반환한다. UI Spec의 `FeedStatusBadge` 컴포넌트에서 사용.

### 요청

Query Parameters 없음.

**요청 예시:**
```
GET /api/v1/status/
```

### 응답

**성공 (200):**

```json
{
  "data": {
    "last_updated_at": "2026-02-21T12:05:00Z",
    "status": "ok",
    "sources": [
      {
        "source_id": 1,
        "source_name": "플래텀",
        "last_crawled_at": "2026-02-21T12:05:00Z",
        "crawl_status": "success"
      },
      {
        "source_id": 2,
        "source_name": "벤처스퀘어",
        "last_crawled_at": "2026-02-21T11:05:00Z",
        "crawl_status": "success"
      },
      {
        "source_id": 3,
        "source_name": "스타트업투데이",
        "last_crawled_at": "2026-02-21T09:00:00Z",
        "crawl_status": "failed"
      }
    ]
  },
  "error": null,
  "meta": null
}
```

**`data` 필드 정의:**

| 필드 | 타입 | 설명 |
|------|------|------|
| `last_updated_at` | string (ISO 8601) | 전체 소스 중 가장 최근 성공 크롤링 시각 |
| `status` | string | 전체 상태. `"ok"` / `"warning"` / `"error"` |
| `sources[].crawl_status` | string | 소스별 상태. `"success"` / `"failed"` / `"running"` / `"unknown"` |

**`status` 판단 기준 (UI Spec FeedStatusBadge 매핑):**

| `status` 값 | 조건 | UI 표시 |
|------------|------|---------|
| `"ok"` | `last_updated_at`이 현재로부터 1시간 이내 | 초록 점 |
| `"warning"` | `last_updated_at`이 1~3시간 사이 | 노란 점 |
| `"error"` | `last_updated_at`이 3시간 초과 또는 모든 소스 실패 | 빨간 점 |

---

## GET /api/v1/search/ (P1)

키워드로 피드 아이템을 검색한다. 제목과 요약 텍스트 전체에서 검색.

### 요청

**Query Parameters:**

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---------|------|------|-------|------|
| `q` | string | 필수 | — | 검색어 (1~100자) |
| `page` | integer | 선택 | `1` | 페이지 번호 (1부터 시작) |
| `limit` | integer | 선택 | `20` | 페이지당 아이템 수 (1~50) |

**요청 예시:**
```
GET /api/v1/search/?q=AI
GET /api/v1/search/?q=시리즈A&page=1&limit=20
GET /api/v1/search/?q=AI&page=2
```

### 응답

**성공 (200) — 결과 있음:**

```json
{
  "data": [
    {
      "id": 123,
      "source": {
        "id": 1,
        "name": "플래텀",
        "slug": "platum",
        "source_type": "news"
      },
      "title": "AI 스타트업 A, 시리즈A 100억 투자 유치",
      "url": "https://platum.kr/archives/12345",
      "summary": "AI 기반 의료진단 스타트업 A사가 카카오벤처스로부터 시리즈A 투자를 유치했다.",
      "author": null,
      "published_at": "2026-02-21T12:00:00Z"
    }
  ],
  "error": null,
  "meta": {
    "current_page": 1,
    "total_pages": 1,
    "total_count": 1,
    "limit": 20,
    "has_prev": false,
    "has_next": false
  }
}
```

> 검색 결과는 탭 구분 없이 모든 소스 혼합 표시. `source.source_type`으로 출처 구분 (UI Spec SearchPage).

**성공 (200) — 결과 없음:**

```json
{
  "data": [],
  "error": null,
  "meta": {
    "current_page": 1,
    "total_pages": 0,
    "total_count": 0,
    "limit": 20,
    "has_prev": false,
    "has_next": false
  }
}
```

**실패 (400 — 빈 검색어):**
```json
{
  "data": null,
  "error": {
    "code": "INVALID_QUERY",
    "message": "검색어를 입력해주세요."
  },
  "meta": null
}
```

**실패 (400 — 검색어 100자 초과):**
```json
{
  "data": null,
  "error": {
    "code": "INVALID_QUERY",
    "message": "검색어는 100자 이하로 입력해주세요."
  },
  "meta": null
}
```

---

## 프론트엔드 연동 가이드

### 탭별 피드 조회 (Tanstack Query 예시 구조)

```
useQuery({
  queryKey: ['feed', tab, keyword, page],
  queryFn: () => GET /api/v1/feed/?tab={tab}&keyword={keyword}&page={page}&limit=20
})
```

### 페이지네이션 구현 (v1.1 변경)

```
// 페이지 상태를 URL 파라미터 또는 컴포넌트 상태로 관리
const [page, setPage] = useState(1)

const { data } = useQuery({
  queryKey: ['feed', tab, page],
  queryFn: () => GET /api/v1/feed/?tab={tab}&page={page}&limit=20,
  keepPreviousData: true  // 페이지 전환 시 이전 데이터 유지하여 깜빡임 방지
})

// 탭 전환 시 1페이지로 리셋
const handleTabChange = (newTab) => {
  setTab(newTab)
  setPage(1)
}

// 페이지 이동
const handlePageChange = (newPage) => setPage(newPage)
// data.meta.has_prev / data.meta.has_next로 버튼 활성화 제어
// data.meta.current_page / data.meta.total_pages로 페이지 정보 표시
```

### URL 기반 페이지 상태 관리 (권장)

```
// 특정 페이지를 URL로 공유할 수 있도록 쿼리 파라미터에 page 반영
// 예: /?tab=news&page=3
// Next.js useSearchParams()로 page 값 읽기/쓰기
```

### FeedStatusBadge 폴링

- 폴링 주기: 60초 (서버 캐시 TTL과 동일)
- `GET /api/v1/status/` 응답의 `data.status`로 배지 색상 결정
- `data.last_updated_at`으로 "N분 전" 계산

### 날짜 표시 (D-4 결정 반영)

UI Spec D-4는 "상대적 표시"(3분 전)으로 결정. `published_at` (ISO 8601 UTC)을 프론트엔드에서 상대 시간으로 변환.
- 1시간 이내: "N분 전"
- 1시간 ~ 24시간: "N시간 전"
- 24시간 초과: "MM월 DD일"

---

## v2 예약 엔드포인트 (현재 미구현)

향후 인증 및 구독 기능 추가 시 아래 경로로 확장 예정. 현재 404 반환.

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/api/v1/user/auth/login` | 이메일 로그인 |
| POST | `/api/v1/user/auth/logout` | 로그아웃 |
| GET | `/api/v1/user/subscriptions/` | 내 구독 목록 |
| POST | `/api/v1/user/subscriptions/` | 소스 구독 추가 |
| DELETE | `/api/v1/user/subscriptions/{id}` | 구독 취소 |
| GET | `/api/v1/user/feed/` | 구독 기반 맞춤 피드 |

---

---

## 변경 이력 (Changelog)

| 버전 | 날짜 | 변경 내용 | 사유 |
|------|------|----------|------|
| v1.0 | 2026-02-21 | 초안 작성 및 확정 | - |
| v1.1 | 2026-02-22 | 커서 기반 → 오프셋 기반 페이지네이션 전환 | PRD v1.1: 무한 스크롤 → 페이지네이션 변경. 페이지 번호 표시, 전체 페이지 수, 이전/다음 탐색 요구 |

### v1.1 변경 상세

**변경 범위:** 페이지네이션 공통 규칙, GET /api/v1/feed/, GET /api/v1/search/, 프론트엔드 연동 가이드

**변경 전:**
- 커서 기반 페이지네이션 (`cursor`, `next_cursor`, `has_more`)
- `total_count` 미제공 (피드 API)
- `useInfiniteQuery`로 무한 스크롤 구현

**변경 후:**
- 오프셋 기반 페이지네이션 (`page`, `limit`)
- 응답 meta에 `current_page`, `total_pages`, `total_count`, `has_prev`, `has_next` 포함
- `useQuery` + `keepPreviousData`로 페이지 단위 조회
- 탭 전환 시 `page=1`로 리셋
- URL 쿼리 파라미터에 `page` 반영 (페이지 공유 가능)

**영향받는 구현:**
- Backend: `feed.py`, `search.py` 라우터 — 쿼리 파라미터 및 SQL OFFSET/LIMIT 변경
- Backend: `schemas/common.py` — PaginationMeta 스키마 변경
- Backend: Redis 캐시 키 패턴 — `feed:{tab}:{cursor}` → `feed:{tab}:{page}:{limit}`
- Frontend: `queries.ts` — `useInfiniteQuery` → `useQuery` 전환
- Frontend: `FeedList.tsx` — 무한 스크롤 제거, 페이지네이션 컴포넌트 연동
- Frontend: `types/api.ts` — Meta 타입 정의 변경

---

*Tech Lead 에이전트 작성 | 2026-02-22 (v1.1) | 변경 시 Frontend Lead와 Backend Lead 동시 통보 필요*
