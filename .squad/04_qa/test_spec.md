# Test Spec: Startup Radar MVP — 2026-02-21

> QA Reviewer 에이전트 작성 | 기준 스펙: `API_Contract.md`, `Tech_Spec.md`

---

## 테스트 전략 개요

| 레이어 | 도구 | 범위 | 우선순위 |
|--------|------|------|---------|
| 백엔드 단위 테스트 | pytest + pytest-asyncio | 서비스 로직, 크롤러 유틸, text_utils | P0 |
| 백엔드 API 통합 테스트 | pytest + httpx ASGITransport | 라우터 응답 형식 검증 | P0 |
| 프론트엔드 단위 테스트 | Jest + @testing-library/react | formatDate, 컴포넌트 렌더 | P1 |
| E2E 테스트 | Playwright (별도 프로젝트) | 피드 로드 → 무한 스크롤 → 검색 흐름 | P2 (배포 후) |

---

## 기존 테스트 현황 (`backend/tests/`)

### test_feed_api.py — 현재 상태: 통과 기대

| 테스트 ID | 설명 | 기대 결과 | 비고 |
|----------|------|----------|------|
| `test_feed_returns_envelope` | 응답이 `{ data, error, meta }` 구조인지 확인 | PASS | meta 구조는 현재 구현 기준 |
| `test_feed_default_tab_is_news` | 기본 탭이 `"news"`인지 확인 | PASS | |
| `test_feed_tab_vc_blog` | `vc_blog` 탭 허용 여부 | PASS | |
| `test_feed_limit_max_50` | `limit=100` → 422 반환 | PASS | |
| `test_feed_cursor_pagination` | `has_more=True`일 때 `next_cursor` 반환 | PASS | 현재 data 안에 위치 (재구현 후 meta로 이동) |
| `test_feed_keyword_filter` | keyword 파라미터 서비스 전달 확인 | PASS | |
| `test_feed_invalid_tab` | 잘못된 탭 → 422 반환 | PASS | |

### test_search_api.py — 현재 상태: 통과 기대

| 테스트 ID | 설명 | 기대 결과 | 비고 |
|----------|------|----------|------|
| `test_search_requires_q` | `q` 없으면 422 | PASS | |
| `test_search_returns_results` | 유효 키워드 → 결과 반환 | PASS | |
| `test_search_empty_results` | 결과 없음 → 빈 배열, 에러 없음 | PASS | |
| `test_search_limit_capped_at_50` | `limit=200` → 422 | PASS | |
| `test_search_offset_pagination` | offset 파라미터 서비스 전달 | PASS | |
| `test_search_source_type_filter` | source_type 파라미터 전달 | PASS | |
| `test_search_q_min_length` | 빈 q → 422 | PASS | |

### test_crawlers.py — 현재 상태: 통과 기대

| 테스트 ID | 설명 | 기대 결과 | 비고 |
|----------|------|----------|------|
| `TestStripHtml::test_removes_tags` | HTML 태그 제거 | PASS | |
| `TestStripHtml::test_empty_string` | 빈 문자열 처리 | PASS | |
| `TestStripHtml::test_nested_tags` | 중첩 태그 제거 | PASS | |
| `TestNormalizeWhitespace::*` | 공백/탭/줄바꿈 정규화 4개 | PASS | |
| `TestTruncateToSentence::*` | 문장 경계 자름 4개 | PASS | |
| `TestBuildSummary::*` | 전체 파이프라인 6개 | PASS | |
| `TestRSSCrawler::test_crawl_returns_items_on_valid_feed` | 정상 피드 파싱 | PASS | |
| `TestRSSCrawler::test_crawl_skips_entry_without_url` | URL 없는 항목 스킵 | PASS | |
| `TestRSSCrawler::test_crawl_returns_empty_when_no_feed_url` | feed_url 없음 처리 | PASS | |
| `TestRSSCrawler::test_crawl_returns_empty_on_bozo_with_no_entries` | 파싱 실패 피드 처리 | PASS | |
| `TestCrawlLock::test_acquire_returns_true_on_success` | Lock 획득 성공 | PASS | |
| `TestCrawlLock::test_acquire_returns_false_when_locked` | 이미 Lock 획득 시 실패 | PASS | |

---

## 신규 작성 필요 테스트 케이스

### T-001: Status API 응답 형식 검증 (CRITICAL, 재구현 후 추가)

**파일:** `backend/tests/test_status_api.py` (신규)

```
TC-S01: GET /api/v1/status/ 기본 응답 구조
  조건: 소스 없음 (빈 DB)
  기대: 200, { data: { last_updated_at, status, sources: [] }, error: null, meta: null }

TC-S02: status 값이 "ok"인 경우
  조건: 가장 최근 crawled_at이 현재로부터 30분 이내
  기대: data.status == "ok"

TC-S03: status 값이 "warning"인 경우
  조건: 가장 최근 crawled_at이 현재로부터 2시간
  기대: data.status == "warning"

TC-S04: status 값이 "error"인 경우
  조건: 가장 최근 crawled_at이 현재로부터 4시간 초과
  기대: data.status == "error"

TC-S05: sources[].crawl_status 값 확인
  조건: crawl_log.status = "success"
  기대: crawl_status == "success"

TC-S06: crawl_log 없는 소스
  조건: 해당 소스에 crawl_log 없음
  기대: crawl_status == "unknown", last_crawled_at == null
```

### T-002: Sources API 재구현 후 검증

**파일:** `backend/tests/test_sources_api.py` (신규)

```
TC-SRC01: GET /api/v1/sources/ 전체 반환
  기대: 200, data가 배열 형식, 각 항목: { id, name, slug, source_type, is_active }
  검증: feed_url, crawl_strategy, crawl_interval, created_at 등 내부 필드 노출 없음

TC-SRC02: GET /api/v1/sources/?source_type=news
  기대: source_type == "news"인 소스만 반환

TC-SRC03: GET /api/v1/sources/?is_active=false
  기대: is_active == false인 소스만 반환

TC-SRC04: GET /api/v1/sources/?source_type=vc_blog&is_active=true
  기대: 복합 필터 적용
```

### T-003: Feed meta 구조 검증 (재구현 후)

**파일:** `backend/tests/test_feed_api.py` (기존 파일에 추가)

```
TC-F01: meta 필드 구조 확인
  기대: meta == { next_cursor: null|string, has_more: bool, total_count: null }
  검증: meta에 "tab", "limit" 없음

TC-F02: 다음 페이지 있을 때 next_cursor가 meta에 위치
  조건: has_more = True, next_cursor 값 존재
  기대: body["meta"]["next_cursor"] != null

TC-F03: tab=person 요청 시 400 반환
  기대: 400, data.error.code == "INVALID_TAB"
```

### T-004: Search API 재구현 후 검증

**파일:** `backend/tests/test_search_api.py` (기존 파일에 추가)

```
TC-SE01: q 파라미터 100자 초과 시 400 반환
  조건: q = "가" * 101
  기대: 400, error.code == "INVALID_QUERY"

TC-SE02: meta.total_count 반환 확인
  조건: 결과 3개
  기대: meta.total_count == 3

TC-SE03: 결과 없음 meta.total_count
  조건: 결과 없음
  기대: meta.total_count == 0, data == []
```

### T-005: text_utils 엣지 케이스

**파일:** `backend/tests/test_crawlers.py` (기존 파일에 추가)

```
TC-TU01: 일본어/특수문자 포함 텍스트 처리
  조건: "日本語テスト。" * 50
  기대: 200자 이내, 마침표 경계에서 자름

TC-TU02: HTML 특수문자 엔티티 처리
  조건: "<p>&lt;꺽쇠&gt; &amp; 앰퍼샌드</p>"
  기대: HTML 태그 없는 텍스트, 엔티티 디코딩 확인

TC-TU03: 줄바꿈만 있는 HTML
  조건: "<br/><br/><br/>"
  기대: build_summary 결과 == None
```

### T-006: 커서 디코딩 엣지 케이스

**파일:** `backend/tests/test_feed_service.py` (신규)

```
TC-CS01: 유효한 커서 디코딩
  조건: 올바른 Base64 encoded "2026-02-21T12:00:00+00:00:123"
  기대: (datetime(2026, 2, 21, 12, 0, 0, utc), 123) 반환

TC-CS02: 손상된 커서 처리
  조건: 잘못된 Base64 문자열
  기대: None 반환, 예외 없음

TC-CS03: 타임존 없는 datetime 커서 처리
  조건: "2026-02-21T12:00:00:123" (tzinfo 없음)
  기대: UTC tzinfo 자동 부여
```

### T-007: 프론트엔드 단위 테스트 (Jest)

**파일:** `frontend/src/lib/__tests__/formatDate.test.ts` (신규)

```
TC-FE01: formatRelativeDate - 방금 전
  조건: 30초 전
  기대: "방금 전"

TC-FE02: formatRelativeDate - N분 전
  조건: 45분 전
  기대: "45분 전"

TC-FE03: formatRelativeDate - N시간 전
  조건: 3시간 전
  기대: "3시간 전"

TC-FE04: formatRelativeDate - MM월 DD일
  조건: 2일 전
  기대: "MM월 DD일" 형식

TC-FE05: formatLastUpdated - 방금 업데이트
  조건: 30초 전
  기대: "방금 업데이트"
```

---

## 통합 테스트 체크리스트 (수동 검증)

### 피드 흐름

- [ ] 서버 기동 후 `/api/v1/feed/?tab=news` 응답 확인
- [ ] `/api/v1/feed/?tab=vc_blog` 응답 확인
- [ ] 피드 아이템 20개 이상 시 `has_more=true`, `next_cursor` 반환 확인
- [ ] next_cursor로 두 번째 페이지 조회 확인
- [ ] keyword 필터 동작 확인 (`?keyword=AI`)

### 검색 흐름

- [ ] `/api/v1/search/?q=AI` 응답 200 확인
- [ ] 빈 결과 응답 (`{ data: [], error: null, meta: { total_count: 0 } }`)
- [ ] 100자 초과 검색어 → 400 INVALID_QUERY 확인

### 크롤러 동작 (로컬 검증)

- [ ] 플래텀 RSS 크롤러 실행 → DB INSERT 확인
- [ ] 벤처스퀘어 RSS 크롤러 실행 → DB INSERT 확인
- [ ] 스타트업투데이 HTML 크롤러 실행 → DB INSERT 확인
- [ ] 알토스벤처스 Prismic API 크롤러 실행 → DB INSERT 확인
- [ ] 카카오벤처스 Playwright 크롤러 (Playwright 브라우저 설치 후)

### 프론트엔드 수동 검증

- [ ] 메인 피드 페이지 로드 → FeedSkeleton 후 피드 아이템 표시
- [ ] 탭 전환 → 키워드 초기화 + 피드 갱신
- [ ] 스크롤 하단 → 추가 피드 자동 로드
- [ ] 검색 후 `/search?q=AI` 이동 → 결과 표시
- [ ] 빈 검색어 Enter → 이동 없음
- [ ] FeedStatusBadge → 색상 점 + 업데이트 시각 표시
- [ ] 모바일 뷰 (375px) → 검색 아이콘 탭 → 검색창 펼침

---

## 테스트 실행 방법

### 백엔드

```bash
# 의존성 설치
pip install -r backend/requirements.txt

# 테스트 실행 (DB/Redis 불필요 — 모킹 기반)
cd backend
pytest tests/ -v

# 특정 파일만
pytest tests/test_feed_api.py -v
pytest tests/test_crawlers.py -v
```

### 프론트엔드 (Jest 미설치 상태 — P1)

```bash
cd frontend
npm install --save-dev jest @testing-library/react @testing-library/jest-dom
# 테스트 파일 작성 후
npm test
```

---

*QA Reviewer | 2026-02-21*
