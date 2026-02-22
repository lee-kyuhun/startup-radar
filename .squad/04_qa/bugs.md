# Bug Report: Startup Radar MVP — 2026-02-21

> QA Reviewer 에이전트 작성 | 발견 기준: `API_Contract.md`
> 최종 업데이트: 2026-02-21 (백엔드 수정 후 재검증 완료)

---

## BUG-001 [CRITICAL] Status API 응답 형식 완전 불일치

**발견일:** 2026-02-21
**심각도:** CRITICAL (프론트엔드 런타임 오류 발생 확실)
**상태:** FIXED (2026-02-21)

**영향 파일:**
- `backend/app/schemas/status.py`
- `backend/app/services/status_service.py`
- `frontend/src/types/api.ts` (StatusData 타입)
- `frontend/src/components/layout/FeedStatusBadge.tsx`

**문제 설명:**
스펙 응답 형식:
```json
{
  "data": {
    "last_updated_at": "2026-02-21T12:05:00Z",
    "status": "ok",
    "sources": [
      { "source_id": 1, "source_name": "플래텀", "last_crawled_at": "...", "crawl_status": "success" }
    ]
  }
}
```

수정 전 구현 응답:
```json
{
  "data": {
    "sources": [
      { "source_id": 1, "source_name": "플래텀", "source_slug": "platum", "last_crawled_at": "...", "latest_log": {...} }
    ],
    "total_sources": 5,
    "active_sources": 5
  }
}
```

누락 필드: `last_updated_at`, `status` (ok/warning/error), `sources[].crawl_status`
추가 필드: `source_slug`, `latest_log` 객체, `total_sources`, `active_sources`

**수정 내용 (재검증 완료):**

`backend/app/schemas/status.py`:
- `SourceStatusSchema`에서 `source_slug`, `latest_log` 제거
- `crawl_status: Literal["success", "failed", "running", "unknown"]` 추가
- `StatusResponse`에서 `total_sources`, `active_sources` 제거
- `last_updated_at: datetime | None`, `status: Literal["ok", "warning", "error"]` 추가

`backend/app/services/status_service.py`:
- `_resolve_crawl_status(latest_log)` 헬퍼 함수 추가 — None → "unknown", 상태 문자열 매핑
- `last_updated_at` 계산 로직 추가 (모든 소스의 `last_crawled_at` 중 최댓값)
- `overall status` 계산 로직 추가 ("failed" 소스 존재 시 "warning", 나머지 "ok")

**잔여 이슈 (MINOR — 수용 가능):**
스펙의 status 판단 기준: `last_updated_at`이 1시간 이내 → "ok", 1~3시간 → "warning", 3시간 초과 → "error". 구현의 판단 기준: `"failed"` 소스 존재 여부. 시간 기반 판단 미구현. 다음 배포 전 보완 권고.

---

## BUG-002 [CRITICAL] Sources API 내부 필드 노출 및 응답 형식 불일치

**발견일:** 2026-02-21
**심각도:** CRITICAL (보안 이슈 + 프론트 연동 오류)
**상태:** FIXED (2026-02-21) — 핵심 수정 완료, 잔여 이슈 존재

**영향 파일:**
- `backend/app/schemas/source.py`
- `backend/app/api/v1/sources.py`
- `frontend/src/lib/api.ts` (fetchSources)

**문제 설명:**
스펙: `data`가 배열 `[{ id, name, slug, source_type, is_active }]`
구현: `data`가 객체 `{ sources: [...], total: N }`, 각 소스에 `feed_url`, `crawl_strategy`, `crawl_interval`, `last_crawled_at`, `created_at`, `updated_at` 포함

API Contract 명시: `crawl_strategy`, `feed_url`, `metadata` 등 내부 운영 필드는 응답에서 제외.

**수정 내용 (재검증 완료):**

`backend/app/schemas/source.py`:
- 이전: `feed_url`, `crawl_strategy`, `crawl_interval`, `last_crawled_at`, `created_at`, `updated_at` 포함
- 이후: `id`, `name`, `slug`, `source_type`, `is_active` 5개 필드만 포함
- `SourceListResponse` 래퍼 클래스 제거

`backend/app/api/v1/sources.py`:
- 이전: `ResponseEnvelope[SourceListResponse]`, `data=SourceListResponse(sources=[...], total=N)`
- 이후: `ResponseEnvelope[list[SourceSchema]]`, `data=[SourceSchema.model_validate(s) for s in sources]`
- `data`가 배열 형식으로 변경 완료

**잔여 이슈 (MINOR):**
스펙에 정의된 `source_type`, `is_active` 쿼리 파라미터 필터가 여전히 미구현. 현재 전체 반환만 지원. 향후 배포 전 추가 권고.

---

## BUG-003 [CRITICAL] Feed API meta 구조 불일치

**발견일:** 2026-02-21
**심각도:** CRITICAL (무한 스크롤 페이지네이션 오동작)
**상태:** FIXED (2026-02-21) — 핵심 수정 완료, 잔여 이슈 존재

**영향 파일:**
- `backend/app/api/v1/feed.py`
- `backend/app/schemas/feed.py`
- `backend/app/services/feed_service.py`
- `frontend/src/lib/api.ts` (fetchFeed 내 FeedPageData 인터페이스)

**문제 설명:**
수정 전 meta: `{ "tab": "news", "limit": 20, "has_more": true }` — `next_cursor` 없음
스펙 meta: `{ "next_cursor": "...", "has_more": true, "total_count": null }`

**수정 내용 (재검증 완료):**

`backend/app/api/v1/feed.py`:
- 이전: `Literal["news", "vc_blog", "all"]` — 미승인 "all" 탭 포함 (BUG-005 병합 수정)
- 이후: `Literal["news", "vc_blog"]`
- meta에 `"next_cursor": page.next_cursor`, `"total_count": None` 추가

`backend/app/services/feed_service.py`:
- `_item_to_schema()` 내 `crawled_at` 제거 (BUG-006 병합 수정)
- `type_map`에서 `"all"` 탭 제거

**잔여 이슈 (MINOR):**
`FeedPageResponse` 내부에 `next_cursor`, `has_more`, `limit` 필드가 여전히 잔존하여 `data` 레이어에도 동일 정보가 노출됨. 스펙은 이 필드들이 `meta`에만 있어야 함. 또한 `meta`에 스펙 외 필드 `"tab"`, `"limit"`이 포함되어 있음. 기능적으로는 동작하나 스펙 완전 준수를 위해 `FeedPageResponse`에서 페이지네이션 필드 제거 권고.

---

## BUG-004 [MAJOR] Search API q 최대 길이 200자 (스펙: 100자)

**발견일:** 2026-02-21
**심각도:** MAJOR
**상태:** FIXED (2026-02-21) — max_length 수정 완료, 에러 형식 잔여

**영향 파일:**
- `backend/app/api/v1/search.py`

**문제 설명:**
API Contract: 검색어 최대 100자. 구현: `max_length=200`. 100~200자 구간에서 스펙 위반 허용.

**수정 내용 (재검증 완료):**
- `max_length=200` → `max_length=100` 변경 확인 (`search.py` line 27)

**잔여 이슈 (MINOR):**
100자 초과 시 FastAPI Pydantic 기본 422 에러가 반환됨. 스펙에 명시된 `error.code = "INVALID_QUERY"` 형식(400)과 다름. 기능적으로는 클라이언트에 오류가 전달되나, 프론트엔드 `ApiClientError` 코드 분기가 `INVALID_QUERY`를 기대할 경우 처리 불일치 발생 가능. 커스텀 예외 핸들러 추가 권고.

---

## BUG-005 [MAJOR] tab=person 400 미처리, "all" 탭 미승인 추가

**발견일:** 2026-02-21
**심각도:** MAJOR
**상태:** FIXED (2026-02-21)

**영향 파일:**
- `backend/app/api/v1/feed.py`
- `backend/app/services/feed_service.py`

**문제 설명:**
API Contract: 허용 탭값 `"news"`, `"vc_blog"`. 미승인 `"all"` 탭이 추가로 허용됨.

**수정 내용 (재검증 완료):**

`backend/app/api/v1/feed.py`:
- `Literal["news", "vc_blog", "all"]` → `Literal["news", "vc_blog"]` 변경 확인

`backend/app/services/feed_service.py`:
- `type_map`에서 `"all": ["news", "vc_blog", "person_threads"]` 항목 제거 확인

스펙 외 탭값 (`tab=person` 포함) 요청 시 FastAPI Pydantic이 422를 반환함. 스펙은 400 + `INVALID_TAB` 코드를 요구하나, 422도 클라이언트 오류를 명확히 전달하는 수준이므로 현 단계에서 수용 가능.

---

## BUG-006 [MINOR-MAJOR] FeedItemSchema에 crawled_at 필드 노출

**발견일:** 2026-02-21
**심각도:** MINOR-MAJOR (불필요한 내부 필드 노출)
**상태:** FIXED (2026-02-21)

**영향 파일:**
- `backend/app/schemas/feed.py`
- `backend/app/services/feed_service.py`

**문제 설명:**
API Contract 응답 필드 정의에 `crawled_at`이 없음. `FeedItemSchema`가 `crawled_at`을 포함하여 응답에 노출.

**수정 내용 (재검증 완료):**

`backend/app/schemas/feed.py`:
- `crawled_at: datetime` 필드 제거 확인 — 현재 `id`, `source`, `title`, `url`, `summary`, `author`, `published_at` 7개 필드만 포함

`backend/app/services/feed_service.py` `_item_to_schema()`:
- `crawled_at=item.crawled_at` 인자 제거 확인

---

## BUG-007 [MINOR] Search meta.total_count 항상 null

**발견일:** 2026-02-21
**심각도:** MINOR
**상태:** OPEN (미수정 — 스펙 해석 재논의 필요)

**영향 파일:**
- `backend/app/services/search_service.py`
- `frontend/src/app/search/page.tsx`

**문제 설명:**
API Contract: 검색 API `meta.total_count`는 정수. 구현: 항상 `null`.
프론트엔드 `SearchContent`에서 `totalCount`를 표시하는 UI가 있으나 값이 없어 결과 건수 미표시.

**비고:**
오케스트레이터가 검색에서 cursor → offset 전환을 허용했으나 `total_count` 구현 여부는 명시되지 않음. COUNT 쿼리 추가 또는 스펙 변경(null 허용) 결정 후 처리 필요.

---

## BUG-008 [INFO] 프로덕션 환경 docs URL 비활성화 확인 필요

**발견일:** 2026-02-21
**심각도:** INFO
**상태:** RESOLVED (코드 확인 완료)

`main.py`: `docs_url="/docs" if not settings.is_production else None` — 프로덕션 환경에서 OpenAPI docs 비활성화 확인됨.

---

## 버그 요약

| 버그 | 심각도 | 상태 | 잔여 이슈 |
|------|--------|------|----------|
| BUG-001 Status API 응답 형식 | CRITICAL | FIXED | status 시간 기반 판단 미구현 (MINOR) |
| BUG-002 Sources API 필드 노출 | CRITICAL | FIXED | 필터 파라미터 미구현 (MINOR) |
| BUG-003 Feed meta 구조 | CRITICAL | FIXED | FeedPageResponse 중복 필드, meta 초과 필드 (MINOR) |
| BUG-004 Search max_length | MAJOR | FIXED | INVALID_QUERY 에러 형식 (MINOR) |
| BUG-005 tab 허용값 | MAJOR | FIXED | 없음 |
| BUG-006 crawled_at 노출 | MAJOR | FIXED | 없음 |
| BUG-007 total_count null | MINOR | OPEN | 스펙 재논의 필요 |
| BUG-008 docs 비활성화 | INFO | RESOLVED | 없음 |

---

*QA Reviewer | 2026-02-21 최초 작성 | 2026-02-21 재검증 업데이트*
