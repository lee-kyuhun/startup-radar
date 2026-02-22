# Review: Pagination (Feed + Search) -- 2026-02-22

## 검토 대상

**백엔드:**
- `/Users/igyuhun/Library/Mobile Documents/com~apple~CloudDocs/Project/PJ004_startup-radar/backend/app/schemas/common.py`
- `/Users/igyuhun/Library/Mobile Documents/com~apple~CloudDocs/Project/PJ004_startup-radar/backend/app/schemas/feed.py`
- `/Users/igyuhun/Library/Mobile Documents/com~apple~CloudDocs/Project/PJ004_startup-radar/backend/app/api/v1/feed.py`
- `/Users/igyuhun/Library/Mobile Documents/com~apple~CloudDocs/Project/PJ004_startup-radar/backend/app/api/v1/search.py`
- `/Users/igyuhun/Library/Mobile Documents/com~apple~CloudDocs/Project/PJ004_startup-radar/backend/app/services/feed_service.py`
- `/Users/igyuhun/Library/Mobile Documents/com~apple~CloudDocs/Project/PJ004_startup-radar/backend/app/services/search_service.py`
- `/Users/igyuhun/Library/Mobile Documents/com~apple~CloudDocs/Project/PJ004_startup-radar/backend/tests/test_feed_api.py`
- `/Users/igyuhun/Library/Mobile Documents/com~apple~CloudDocs/Project/PJ004_startup-radar/backend/tests/test_search_api.py`

**프론트엔드:**
- `/Users/igyuhun/Library/Mobile Documents/com~apple~CloudDocs/Project/PJ004_startup-radar/frontend/src/types/api.ts`
- `/Users/igyuhun/Library/Mobile Documents/com~apple~CloudDocs/Project/PJ004_startup-radar/frontend/src/lib/api.ts`
- `/Users/igyuhun/Library/Mobile Documents/com~apple~CloudDocs/Project/PJ004_startup-radar/frontend/src/lib/queries.ts`
- `/Users/igyuhun/Library/Mobile Documents/com~apple~CloudDocs/Project/PJ004_startup-radar/frontend/src/lib/constants.ts`
- `/Users/igyuhun/Library/Mobile Documents/com~apple~CloudDocs/Project/PJ004_startup-radar/frontend/src/components/feed/Pagination.tsx`
- `/Users/igyuhun/Library/Mobile Documents/com~apple~CloudDocs/Project/PJ004_startup-radar/frontend/src/components/feed/FeedList.tsx`
- `/Users/igyuhun/Library/Mobile Documents/com~apple~CloudDocs/Project/PJ004_startup-radar/frontend/src/app/page.tsx`
- `/Users/igyuhun/Library/Mobile Documents/com~apple~CloudDocs/Project/PJ004_startup-radar/frontend/src/app/search/page.tsx`

**기준 스펙:**
- `.squad/01_planning/PRD.md` (v1.1)
- `.squad/02_design/UI_Specs.md` (v1.1b)
- `.squad/03_architecture/API_Contract.md` (v1.1)
- `.squad/03_architecture/Tech_Spec.md` (v1.1)

---

## 결과: PASS -- P0 이슈 2건 수정 완료, P1 2건/P2 1건 잔여

---

## 1. API Contract vs 백엔드 코드 일치 여부

### 확인 항목

- [x] GET /api/v1/feed/ 파라미터: `tab`, `page`, `limit`, `keyword` -- 일치
- [x] GET /api/v1/search/ 파라미터: `q`, `page`, `limit` -- 일치
- [x] tab 허용 값: `"news"`, `"vc_blog"` (Literal type) -- 일치
- [x] page 기본값 1, limit 기본값 20, 최대 50 -- 일치
- [x] 응답 Envelope 구조: `{ data, error, meta }` -- 일치
- [x] PaginationMeta 필드: `current_page`, `total_pages`, `total_count`, `limit`, `has_prev`, `has_next` -- 일치
- [x] FeedItem 응답 필드: id, source(id/name/slug/source_type), title, url, summary, author, published_at -- 일치
- [x] 검색어 빈 문자열 -> INVALID_QUERY 에러 -- 일치
- [x] 검색어 100자 초과 -> INVALID_QUERY 에러 -- 일치
- [x] total_pages 계산: `ceil(total_count / limit)` -- 일치
- [x] has_prev: `current_page > 1` -- 일치
- [x] has_next: `current_page < total_pages` -- 일치
- [x] 정렬: `published_at DESC, id DESC` -- 일치 (feed_service.py 107행, search_service.py 77행)
- [x] Redis 캐시 키: `feed:{tab}:p{page}:l{limit}` -- 일치 (feed_service.py 50행)
- [ ] **INVALID_PAGE, INVALID_LIMIT, INVALID_TAB 에러의 HTTP 상태 코드** -- 불일치 (아래 상세)
- [ ] **검색 결과 Redis 캐싱 미구현** -- 누락 (아래 상세)

### 발견된 문제

| # | 심각도 | 위치 | 문제 | 스펙 기준 |
|---|--------|------|------|-----------|
| B-1 | P0 | `backend/app/api/v1/feed.py` 60-64행, `search.py` 68-72행 | INVALID_PAGE 에러를 HTTP 200으로 반환한다. `ResponseEnvelope.fail()`은 FastAPI의 기본 200 상태 코드를 사용하므로, 클라이언트가 HTTP 상태 코드로 에러를 구분할 수 없다. | API Contract: INVALID_PAGE -> HTTP 400 |
| B-2 | P1 | `backend/app/api/v1/feed.py`, `search.py` | INVALID_TAB, limit 범위 초과 에러가 FastAPI의 422 Unprocessable Entity로 반환된다 (Literal, Query ge/le 유효성 검사). API Contract은 400을 명시한다. | API Contract: INVALID_TAB -> HTTP 400, INVALID_LIMIT -> HTTP 400 |
| B-3 | P2 | `backend/app/services/search_service.py` | search_service에 Redis 캐싱이 구현되어 있지 않다. feed_service는 5분 TTL 캐싱을 사용하지만 search_service는 매번 DB 쿼리를 실행한다. Tech Spec/API Contract에서 검색 캐싱을 명시하지는 않았으나, DB_Schema.md에서 검색 캐시 TTL 60초를 언급하고 있고, search_service.py 16행에 `SEARCH_CACHE_TTL = 60` 상수가 정의되어 있으나 실제로 사용되지 않는다. | DB_Schema.md 참조, 코드 내 미사용 상수 |

---

## 2. UI Specs vs 프론트엔드 코드 일치 여부

### 확인 항목

- [x] Pagination 컴포넌트 위치: FeedList 하단 -- 일치 (FeedList.tsx 84-91행)
- [x] 전체 페이지 1개 이하 시 Pagination 숨김 -- 일치 (Pagination.tsx 22행)
- [x] 빈 상태/에러 시 Pagination 숨김 -- 일치 (FeedList.tsx 47-61행에서 조기 반환)
- [x] 이전/다음 버튼: chevron SVG 16x16, 36x36px (desktop) -- 일치 (w-9 h-9 = 36x36)
- [x] 이전 버튼 1페이지에서 disabled -- 일치 (Pagination.tsx 33행)
- [x] 다음 버튼 마지막 페이지에서 disabled -- 일치 (Pagination.tsx 53행)
- [x] disabled 상태: `cursor-not-allowed`, `text-dark-500` -- 일치
- [x] 페이지 번호 활성 상태: `bg-accent-blue`, `text-white` -- 일치 (Pagination.tsx 231행)
- [x] 페이지 번호 hover: `bg-dark-700`, `text-gray-100` -- 일치 (Pagination.tsx 247행)
- [x] 말줄임(...) `aria-hidden="true"`, `tabIndex={-1}` -- 일치 (Pagination.tsx 263-264행)
- [x] 활성 페이지 버튼: `<span>` (클릭 불가), `cursor-default` -- 일치 (Pagination.tsx 226-237행)
- [x] Desktop 최대 10슬롯 -- 일치 (`buildPageSlots(current, total, 10, 2)`)
- [x] Mobile 최대 7슬롯, 고정 edge 1개 -- 일치 (`buildPageSlots(current, total, 7, 1)`)
- [x] Mobile 버튼 크기 32x32px -- 일치 (`min-w-8 h-8` = 32x32)
- [x] Mobile 갭 2px -- 일치 (`gap-0.5` = 2px)
- [x] 로딩 중 Pagination `opacity-50`, `pointer-events-none` -- 일치 (Pagination.tsx 28행)
- [x] 페이지 전환 시 스크롤 상단 이동 -- 일치 (FeedList.tsx 34-39행)
- [x] Desktop/Mobile 분기: `hidden sm:flex` / `flex sm:hidden` -- 일치 (Pagination.tsx 160, 193행)
- [x] 페이지 번호 `aria-label` -- 일치 (`${page} 페이지로 이동`)
- [x] 이전/다음 버튼 `aria-label` -- 일치 (`이전 페이지`, `다음 페이지`)

### Truncation 알고리즘 검증

UI Spec의 truncation 규칙과 코드의 `buildPageSlots` 함수를 비교 검증했다.

**Desktop (maxSlots=10, fixedEdge=2):**

| 시나리오 | UI Spec 기대 결과 | 코드 결과 | 판정 |
|---------|------------------|----------|------|
| total=8, current=4 | `1 2 3 [4] 5 6 7 8` | 동일 | PASS |
| total=25, current=1 | `[1] 2 3 4 5 6 7 ... 24 25` | 동일 | PASS |
| total=25, current=5 | `1 2 3 4 [5] 6 7 ... 24 25` | 동일 | PASS |
| total=25, current=12 | `1 2 ... 10 11 [12] 13 14 ... 24 25` | 동일 (middleSlots=4, halfMiddle=2) | PASS |
| total=25, current=22 | `1 2 ... 19 20 21 22 23 24 25` | 동일 | PASS |
| total=25, current=25 | `1 2 ... 19 20 21 22 23 24 [25]` | 동일 | PASS |
| total=2, current=2 | `1 [2]` | 동일 | PASS |

**참고:** UI Spec은 `current <= 5`를 "앞쪽 가까이" 기준으로 명시하지만, 코드는 `nearStartThreshold = 7`을 사용한다. 이는 수학적으로 올바르다 -- current=6일 때 양쪽 말줄임 패턴(`1 2 ... 4 5 [6] 7 8 ... 24 25`)은 11슬롯이 필요하여 10슬롯 제한을 초과하기 때문이다. 코드의 동적 계산이 스펙의 정적 예시보다 정확하므로, 이는 이슈가 아닌 개선이다.

---

## 3. Tech Spec vs 구현 일치 여부

### 확인 항목

- [x] Tanstack Query v5 `useQuery` 사용 (useInfiniteQuery 아님) -- 일치 (queries.ts 36, 53행)
- [x] `placeholderData: (previousData) => previousData` (keepPreviousData v5 equivalent) -- 일치 (queries.ts 46, 63행)
- [x] 캐시 키 구조: `['feed', tab, page, keyword]` -- 일치 (queries.ts 27행)
- [x] 검색 캐시 키: `['search', query, page]` -- 일치 (queries.ts 28행)
- [x] URL 파라미터로 페이지 상태 관리: `?tab=news&page=3` -- 일치 (page.tsx 42-51행)
- [x] 탭 전환 시 page=1 리셋 -- 일치 (page.tsx 54-56행)
- [x] 키워드 변경 시 page=1 리셋 -- 일치 (page.tsx 59-61행)
- [x] 정렬 안정성: `published_at DESC, id DESC` -- 일치
- [x] OFFSET 계산: `(page - 1) * limit` -- 일치 (feed_service.py 95행)
- [x] COUNT(*) 별도 실행 -- 일치 (feed_service.py 82-92행)
- [x] Redis 캐시 키 패턴 v1.1: `feed:{tab}:p{page}:l{limit}` -- 일치 (feed_service.py 50행)
- [x] Feed 캐시 TTL 5분 -- 일치 (feed_service.py 16행, `FEED_CACHE_TTL = 300`)
- [x] staleTime 5분 -- 일치 (constants.ts 51행, `FEED_STALE_TIME = 5 * 60 * 1000`)
- [x] 유효하지 않은 페이지 번호 (0, 음수, NaN) -> 1페이지 폴백 -- 일치 (page.tsx 33-34행)

---

## 4. 프론트엔드-백엔드 인터페이스 일치 여부

### 확인 항목

- [x] TypeScript `PaginationMeta` 인터페이스 필드 == Python `PaginationMeta` 필드 -- 일치
- [x] TypeScript `FeedItem` 인터페이스 필드 == Python `FeedItemSchema` 필드 -- 일치
- [x] TypeScript `ApiEnvelope<T>` == Python `ResponseEnvelope` -- 일치
- [x] `fetchFeed` 요청 파라미터: tab, page, limit, keyword -- 백엔드 라우터와 일치
- [x] `fetchSearch` 요청 파라미터: q, page, limit -- 백엔드 라우터와 일치
- [x] 기본값: tab="news", page=1, limit=20 -- 양측 일치
- [ ] **프론트엔드 fetchFeed/fetchSearch의 HTTP 에러 처리** -- 불완전 (아래 상세)

### 발견된 문제

| # | 심각도 | 위치 | 문제 | 수정 요청 |
|---|--------|------|------|-----------|
| F-1 | P0 | `frontend/src/lib/api.ts` 73-88행 | `fetchFeed`와 `fetchSearch` 함수가 HTTP 상태 코드를 확인하지 않고 바로 `res.json()`을 호출한다. FastAPI가 422를 반환할 경우 (예: limit=100, tab=invalid), 응답 JSON 구조가 Envelope이 아닌 FastAPI 기본 ValidationError 형식이므로, `envelope.error`가 undefined가 되어 에러가 정상 처리되지 않고 잘못된 빈 데이터가 반환된다. | `fetchFeed`/`fetchSearch`에서 `res.ok` 확인을 추가하거나, 백엔드에서 FastAPI 422를 커스텀 에러 핸들러로 Envelope 형식 400 응답으로 변환해야 한다. |
| F-2 | P1 | `frontend/src/lib/api.ts` 26행 | `request<T>` 함수의 조건 `!res.ok && res.status !== 200`은 논리적으로 중복이다. `res.ok`는 HTTP 200-299를 의미하므로, `res.status !== 200`은 불필요하다. 기능상 문제는 없으나 코드 의도가 불명확하다. | `if (!res.ok)` 로 단순화할 것. |

---

## 5. 테스트 커버리지 적절성

### 백엔드 테스트 (test_feed_api.py: 8개, test_search_api.py: 8개)

**Feed API 테스트 커버리지:**

| 시나리오 | 커버됨 | 테스트명 |
|---------|--------|---------|
| 응답 Envelope 구조 | O | `test_feed_returns_envelope` |
| 기본 tab = "news" | O | `test_feed_default_tab_is_news` |
| tab = "vc_blog" 허용 | O | `test_feed_tab_vc_blog` |
| limit > 50 거부 (422) | O | `test_feed_limit_max_50` |
| PaginationMeta 필드 검증 | O | `test_feed_offset_pagination_meta` |
| page 파라미터 전달 | O | `test_feed_page_param_forwarded` |
| keyword 파라미터 전달 | O | `test_feed_keyword_filter` |
| 잘못된 tab 값 거부 | O | `test_feed_invalid_tab` |
| 기본 page = 1 | O | `test_feed_default_page_is_1` |
| **INVALID_PAGE (total_pages 초과)** | **X** | 미작성 |
| **빈 피드 (total_count=0)** | **X** | 미작성 |
| **has_prev/has_next 정확성 (2페이지 이상)** | **X** | 미작성 |
| **limit=0 또는 limit=-1 거부** | **X** | 미작성 |
| **page=0 또는 page=-1 거부** | **X** | 미작성 |

**Search API 테스트 커버리지:**

| 시나리오 | 커버됨 | 테스트명 |
|---------|--------|---------|
| q 미제공 -> INVALID_QUERY | O | `test_search_requires_q` |
| 정상 검색 결과 + meta | O | `test_search_returns_results` |
| 결과 없음 -> 빈 배열 | O | `test_search_empty_results` |
| limit > 50 거부 | O | `test_search_limit_capped_at_50` |
| page 파라미터 전달 | O | `test_search_page_pagination` |
| q 빈 문자열 -> INVALID_QUERY | O | `test_search_q_empty_string` |
| q 100자 초과 -> INVALID_QUERY | O | `test_search_q_too_long` |
| PaginationMeta 필드 검증 | O | `test_search_pagination_meta` |
| **탭 없이 전체 소스 혼합 검색** | **X** | 미작성 |
| **INVALID_PAGE (total_pages 초과)** | **X** | 미작성 |
| **공백만 있는 q (" ")** | **X** | 미작성 (코드는 `q.strip()` 처리 있음) |

### 프론트엔드 테스트

프론트엔드 테스트 파일은 검증 대상에 포함되어 있지 않았다. Pagination 컴포넌트의 `buildPageSlots` truncation 알고리즘은 순수 함수이므로 단위 테스트 작성이 권장된다.

---

## 종합 이슈 목록

| # | 심각도 | 영역 | 문제 요약 | 조치 |
|---|--------|------|----------|------|
| B-1 | **P0** | Backend | INVALID_PAGE 에러가 HTTP 200으로 반환됨 (API Contract: 400) | **수정 완료** -- JSONResponse(status_code=400) 적용 |
| F-1 | **P0** | Frontend | fetchFeed/fetchSearch가 HTTP 422 응답을 정상 처리하지 못함 | **수정 완료** -- res.ok 체크 + Envelope/HTTP 에러 구분 처리 |
| B-2 | P1 | Backend | INVALID_TAB/INVALID_LIMIT가 FastAPI 422로 반환 (API Contract: 400) | 수정 권장 (FastAPI exception_handler 추가 필요) |
| F-2 | P1 | Frontend | api.ts의 `request` 함수에 불필요한 조건절 | **수정 완료** -- `!res.ok` 로 단순화 |
| B-3 | P2 | Backend | search_service에 SEARCH_CACHE_TTL 상수가 정의되어 있으나 미사용 | 수정 선택 |

---

## 수정 요청 (Ephemeral Agent에 전달)

### B-1 수정: INVALID_PAGE 에러 HTTP 상태 코드 (P0)

**파일:** `backend/app/api/v1/feed.py` (60-64행), `backend/app/api/v1/search.py` (68-72행)

**현재 동작:** `ResponseEnvelope.fail()` 반환 시 FastAPI가 기본 200을 사용한다.

**수정 방법:** `JSONResponse`를 사용하여 명시적으로 HTTP 400을 반환한다.

```python
from fastapi.responses import JSONResponse

# INVALID_PAGE 반환 시:
if page < 1 or (total_pages > 0 and page > total_pages):
    return JSONResponse(
        status_code=400,
        content=ResponseEnvelope.fail(
            code="INVALID_PAGE",
            message="유효하지 않은 페이지 번호입니다.",
        ).model_dump(),
    )
```

feed.py와 search.py 모두 동일하게 수정할 것. INVALID_LIMIT 에러도 동일 패턴 적용.

### F-1 수정: fetchFeed/fetchSearch HTTP 에러 처리 (P0)

**파일:** `frontend/src/lib/api.ts` (60-117행)

**현재 동작:** `fetchFeed`와 `fetchSearch`가 `res.ok` 확인 없이 바로 `res.json()`을 호출한다. FastAPI 422 응답은 Envelope 형식이 아니므로 파싱에 실패하거나 잘못된 결과를 반환한다.

**수정 방법:** `res.ok` 확인을 추가한다.

```typescript
export async function fetchFeed(params: { ... }): Promise<FeedResponse> {
  // ... (기존 코드)
  const res = await fetch(`${BASE_URL}${url}`, { ... });

  if (!res.ok) {
    // FastAPI 422 등 비-200 응답 처리
    throw new ApiClientError('HTTP_ERROR', `HTTP ${res.status}: ${res.statusText}`);
  }

  const envelope: Envelope<FeedItem[]> = await res.json();
  // ... (기존 코드)
}
```

`fetchSearch`에도 동일하게 적용할 것.

---

## 배포 전 체크리스트 (Pagination 관련)

- [x] 페이지네이션 기본 동작: 페이지 이동, 이전/다음 버튼
- [x] Truncation 알고리즘 정확성
- [x] 탭 전환 시 1페이지 리셋
- [x] 키워드 변경 시 1페이지 리셋
- [x] URL 파라미터 연동 (`?tab=news&page=3`)
- [x] 유효하지 않은 페이지 번호 폴백 (프론트엔드)
- [x] 검색 결과 페이지네이션
- [x] 빈 쿼리 리다이렉트 (`/search` -> `/`)
- [x] Desktop/Mobile 반응형 Pagination
- [x] 로딩 상태 (opacity, pointer-events)
- [x] 페이지 전환 시 스크롤 상단 이동
- [x] 1페이지만 있을 때 Pagination 숨김
- [x] 빈 상태/에러 시 Pagination 숨김
- [x] Redis 캐시 키 패턴 (v1.1)
- [x] keepPreviousData (placeholderData) 적용
- [x] **P0 이슈 B-1 해결: HTTP 상태 코드** -- 2026-02-22 수정 완료
- [x] **P0 이슈 F-1 해결: HTTP 에러 처리** -- 2026-02-22 수정 완료
- [ ] INVALID_PAGE 테스트 추가
- [ ] 빈 피드 테스트 추가

---

*작성: QA Reviewer 에이전트 | 2026-02-22 | 기준 스펙: PRD v1.1, UI_Specs v1.1b, API_Contract v1.1, Tech_Spec v1.1*
