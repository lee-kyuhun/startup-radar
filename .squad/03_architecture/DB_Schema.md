# DB Schema: Startup Radar MVP

> 작성: Tech Lead 에이전트 | 날짜: 2026-02-21 | 상태: 확정
> 기준 문서: `PRD.md`, `Tech_Decisions.md`
> DB: PostgreSQL 16

---

## 설계 원칙

1. **MVP 최소 스키마**: 구현에 필요한 테이블만 생성. 과도한 사전 설계 금지.
2. **확장 대비 예약**: `source_type`, `users` 등 v2 확장 경로를 스키마에 미리 반영.
3. **중복 방지**: `feed_items.url`에 UNIQUE 제약으로 동일 기사 중복 수집 차단.
4. **소프트 딜리트**: 데이터는 `is_active` 플래그로 비활성화. 실제 DELETE 최소화.

---

## 테이블 목록

| 테이블 | 설명 | MVP 사용 |
|--------|------|---------|
| `sources` | 크롤링 대상 소스 (미디어, VC 블로그) | 사용 |
| `feed_items` | 수집된 피드 아이템 | 사용 |
| `crawl_logs` | 크롤링 실행 이력 | 사용 |
| `persons` | 인물 엔티티 | 스키마만 정의, 데이터 미입력 |
| `users` | 서비스 사용자 (v2) | 스키마만 정의 |

---

## 1. `sources` 테이블

크롤링 대상 소스. 뉴스 미디어, VC 블로그, 인물 SNS 채널을 모두 이 테이블로 관리.

```sql
CREATE TABLE sources (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(100)    NOT NULL,           -- 표시 이름 (예: "플래텀", "카카오벤처스 블로그")
    slug            VARCHAR(100)    NOT NULL UNIQUE,    -- URL 친화적 식별자 (예: "platum", "kakao-ventures")
    source_type     VARCHAR(30)     NOT NULL,           -- 소스 종류 (아래 Enum 참고)
    feed_url        TEXT,                               -- RSS URL 또는 크롤링 대상 URL
    crawl_strategy  VARCHAR(20)     NOT NULL DEFAULT 'rss', -- 수집 방식: 'rss' | 'html' | 'playwright' | 'api'
    crawl_interval  INTEGER         NOT NULL DEFAULT 60,    -- 크롤링 주기 (분)
    last_crawled_at TIMESTAMPTZ,                        -- 마지막 성공 크롤링 시각
    is_active       BOOLEAN         NOT NULL DEFAULT TRUE,  -- 비활성화 가능
    metadata        JSONB           DEFAULT '{}',       -- 소스별 추가 설정 (CSS selector, API key 등)
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);
```

**`source_type` 허용 값:**

| 값 | 설명 | MVP 사용 |
|----|------|---------|
| `'news'` | 뉴스 미디어 (플래텀, 벤처스퀘어 등) | 사용 |
| `'vc_blog'` | VC 공식 블로그 (카카오벤처스 등) | 사용 |
| `'person_threads'` | 인물 Threads 피드 (v2 예약) | 미사용 |
| `'person_linkedin'` | 인물 LinkedIn (영구 제외 — TD-005) | 미사용 |

**`crawl_strategy` 허용 값:**

| 값 | 설명 |
|----|------|
| `'rss'` | feedparser로 RSS 파싱 |
| `'html'` | BeautifulSoup HTML 크롤링 |
| `'playwright'` | Playwright 헤드리스 브라우저 크롤링 |
| `'api'` | 공식 API 호출 (Threads API 등, v2) |

**초기 데이터 (시드):**

```sql
INSERT INTO sources (name, slug, source_type, feed_url, crawl_strategy, crawl_interval) VALUES
('플래텀',        'platum',         'news',    'https://platum.kr/feed',              'rss',        60),
('벤처스퀘어',    'venturesquare',  'news',    'https://www.venturesquare.net/feed',  'rss',        60),
('스타트업투데이', 'startuptoday',   'news',    'https://www.startuptoday.kr',        'html',       60),
('카카오벤처스',  'kakao-ventures', 'vc_blog', NULL,                                  'playwright', 360),
('알토스벤처스',  'altos-ventures', 'vc_blog', NULL,                                  'html',       360);
```

> `feed_url`이 NULL인 소스는 `metadata` JSONB에 크롤링 진입 URL과 CSS 선택자를 저장.

---

## 2. `feed_items` 테이블

수집된 모든 피드 아이템. 뉴스, VC 블로그 포스트, (v2) 인물 SNS 포스트 모두 이 테이블에 통합 저장.

```sql
CREATE TABLE feed_items (
    id           BIGSERIAL PRIMARY KEY,
    source_id    INTEGER         NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    title        TEXT            NOT NULL,              -- 원본 제목
    url          TEXT            NOT NULL UNIQUE,       -- 원본 링크 (중복 방지 핵심)
    summary      TEXT,                                  -- 원문 첫 200자 (HTML 제거 후) — TD-007
    author       VARCHAR(200),                          -- 작성자 (있는 경우)
    published_at TIMESTAMPTZ     NOT NULL,              -- 원본 발행 시각
    crawled_at   TIMESTAMPTZ     NOT NULL DEFAULT NOW(),-- 수집 시각
    is_active    BOOLEAN         NOT NULL DEFAULT TRUE, -- 소프트 딜리트
    raw_metadata JSONB           DEFAULT '{}',          -- 소스별 원본 데이터 (카테고리, 태그 등)
    created_at   TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

-- 인덱스
CREATE INDEX idx_feed_items_source_published
    ON feed_items (source_id, published_at DESC)
    WHERE is_active = TRUE;

CREATE INDEX idx_feed_items_published
    ON feed_items (published_at DESC)
    WHERE is_active = TRUE;

CREATE INDEX idx_feed_items_title_search
    ON feed_items USING GIN (to_tsvector('korean', title || ' ' || COALESCE(summary, '')));
```

**컬럼 설명:**

| 컬럼 | 제약 | 설명 |
|------|------|------|
| `url` | UNIQUE | 동일 기사 중복 방지. `INSERT ... ON CONFLICT DO NOTHING`으로 멱등성 확보 |
| `summary` | NULL 허용 | 원문 200자. HTML 태그 제거 후 순수 텍스트. 마침표 경계 준수 (TD-007) |
| `published_at` | NOT NULL | 피드 정렬 기준. RSS의 `pubDate`, HTML 크롤링 시 페이지에서 파싱 |
| `raw_metadata` | JSONB | 카테고리, 원본 태그, 이미지 URL 등 소스별 추가 데이터. v2 기능 확장 시 활용 |

---

## 3. `crawl_logs` 테이블

크롤링 실행 이력. 운영 모니터링 및 `FeedStatusBadge` 업데이트 시각 계산에 사용.

```sql
CREATE TABLE crawl_logs (
    id             BIGSERIAL PRIMARY KEY,
    source_id      INTEGER         NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    started_at     TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    finished_at    TIMESTAMPTZ,
    status         VARCHAR(20)     NOT NULL DEFAULT 'running', -- 'running' | 'success' | 'failed'
    items_fetched  INTEGER         DEFAULT 0,    -- 이번 크롤링에서 가져온 아이템 수
    items_new      INTEGER         DEFAULT 0,    -- 실제 신규 저장된 아이템 수
    error_message  TEXT,                         -- 실패 시 에러 메시지
    created_at     TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

-- 인덱스
CREATE INDEX idx_crawl_logs_source_started
    ON crawl_logs (source_id, started_at DESC);

CREATE INDEX idx_crawl_logs_started
    ON crawl_logs (started_at DESC);
```

**활용 예시:**

- FeedStatusBadge 업데이트 시각: `SELECT MAX(finished_at) FROM crawl_logs WHERE status = 'success'`
- 소스별 마지막 성공 크롤링: `SELECT * FROM crawl_logs WHERE source_id = ? AND status = 'success' ORDER BY started_at DESC LIMIT 1`

---

## 4. `persons` 테이블 (v2 예약)

인물 엔티티. MVP에서는 테이블만 생성하고 데이터를 입력하지 않는다.

```sql
CREATE TABLE persons (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100)    NOT NULL,
    slug        VARCHAR(100)    NOT NULL UNIQUE,
    bio         TEXT,
    affiliation VARCHAR(200),               -- 소속 기관 (예: "카카오벤처스 심사역")
    threads_url TEXT,                       -- Threads 프로필 URL
    is_active   BOOLEAN         NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);
```

> MVP에서 인물 소스(`source_type = 'person_threads'`)가 추가될 때 `sources.person_id`를 FK로 추가 예정.

---

## 5. `users` 테이블 (v2 예약)

서비스 사용자. MVP에서는 테이블만 생성하고 데이터를 입력하지 않는다.

```sql
CREATE TABLE users (
    id            BIGSERIAL PRIMARY KEY,
    email         VARCHAR(255)    NOT NULL UNIQUE,
    password_hash TEXT,                             -- NULL이면 OAuth 전용 계정
    display_name  VARCHAR(100),
    is_active     BOOLEAN         NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    last_login_at TIMESTAMPTZ
);
```

---

## Redis 데이터 구조

Redis는 캐싱 및 크롤링 Lock에만 사용. DB처럼 영속 저장하지 않는다.

| 키 패턴 | 타입 | TTL | 용도 |
|---------|------|-----|------|
| `feed:news:{cursor}` | String (JSON) | 300초 (5분) | 뉴스 탭 피드 API 응답 캐시 |
| `feed:vc_blog:{cursor}` | String (JSON) | 300초 (5분) | VC 블로그 탭 피드 API 응답 캐시 |
| `search:{q_hash}` | String (JSON) | 60초 (1분) | 검색 결과 캐시 |
| `crawl_lock:{source_id}` | String | 크롤링 예상 소요 시간 | 중복 크롤링 방지 Lock |
| `feed_status` | String (JSON) | 60초 (1분) | 마지막 크롤링 시각 캐시 (StatusBadge용) |

---

## 마이그레이션 전략

- 마이그레이션 도구: **Alembic** (FastAPI + SQLAlchemy 표준 조합)
- 파일 위치: `backend/alembic/versions/`
- 초기 마이그레이션: 위 5개 테이블 생성 + 시드 데이터 (sources)
- 컨벤션: `{revision}_{슬러그_설명}.py` (예: `0001_create_initial_tables.py`)

---

## ERD (텍스트)

```
sources (1) ────< feed_items (N)
    id ─────────── source_id

sources (1) ────< crawl_logs (N)
    id ─────────── source_id

persons (v2 예약, 현재 독립)

users (v2 예약, 현재 독립)
```

---

*Tech Lead 에이전트 작성 | 2026-02-21 | 다음 갱신: v2 구독 기능 추가 시 (users, subscriptions 테이블 확장)*
