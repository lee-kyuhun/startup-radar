# Frontend Spec: Startup Radar — MVP v1.0

> 작성: Frontend Lead 에이전트 | 날짜: 2026-02-21 | 상태: 초안
> 기준 문서: `.squad/02_design/UI_Specs.md`, `.squad/03_architecture/API_Contract.md`, `.squad/03_architecture/Tech_Spec.md`

---

## 목차

1. [기술 스택 (확정)](#1-기술-스택-확정)
2. [디렉토리 구조](#2-디렉토리-구조)
3. [컴포넌트 목록 및 구현 계획](#3-컴포넌트-목록-및-구현-계획)
4. [상태 관리 전략](#4-상태-관리-전략)
5. [데이터 패칭 전략](#5-데이터-패칭-전략)
6. [Tailwind 커스텀 토큰 설정 계획](#6-tailwind-커스텀-토큰-설정-계획)
7. [타입 정의 계획](#7-타입-정의-계획)
8. [라우팅 구조](#8-라우팅-구조)
9. [구현 우선순위 및 위임 계획](#9-구현-우선순위-및-위임-계획)
10. [미결 결정 사항](#10-미결-결정-사항)

---

## 1. 기술 스택 (확정)

| 영역 | 기술 | 버전 | 비고 |
|------|------|------|------|
| Framework | Next.js | 14 (App Router) | SSR 지원, Vercel 공식 플랫폼 |
| Styling | Tailwind CSS | v3 | UI Spec 색상/간격 토큰 커스텀 확장 |
| 서버 상태 관리 | TanStack Query | v5 | 피드 캐싱, 무한스크롤, 로딩/에러 상태 |
| 클라이언트 상태 | React useState / useReducer | — | 탭 선택, 필터 키워드 등 로컬 UI 상태 |
| 폰트 | Pretendard | — | `next/font` 로컬 호스팅 (한글 최적화) |
| HTTP 클라이언트 | fetch (Web API) | — | 커스텀 래퍼로 Envelope 파싱 |
| 에러 모니터링 | Sentry | — | 프론트엔드 에러 자동 수집 |
| 배포 | Vercel | — | main 브랜치 push 시 자동 배포 |

---

## 2. 디렉토리 구조

```
frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx              # 루트 레이아웃: GlobalHeader 포함, Pretendard 폰트 적용
│   │   ├── page.tsx                # 메인 피드 페이지 (/)
│   │   └── search/
│   │       └── page.tsx            # 검색 결과 페이지 (/search?q=...)
│   │
│   ├── components/
│   │   ├── layout/
│   │   │   ├── GlobalHeader.tsx    # sticky 헤더: Logo + SearchBar + FeedStatusBadge
│   │   │   ├── Logo.tsx            # 레이더 아이콘 + "Startup Radar" 텍스트
│   │   │   ├── SearchBar.tsx       # 검색 입력창, Enter → /search?q=... 이동
│   │   │   └── FeedStatusBadge.tsx # 크롤링 상태 배지 (색상 점 + "N분 전")
│   │   │
│   │   ├── feed/
│   │   │   ├── TabNav.tsx          # 뉴스 / VC 블로그 탭 (D-2 반영: 인물 탭 없음)
│   │   │   ├── FeedList.tsx        # 무한 스크롤 피드 컨테이너
│   │   │   ├── FeedItem.tsx        # 피드 카드 (D-6 반영: 텍스트 전용)
│   │   │   ├── SourceTag.tsx       # 출처 배지 (tag-news / tag-vc)
│   │   │   ├── FeedSkeleton.tsx    # shimmer 로딩 스켈레톤 (5개)
│   │   │   ├── FeedEmpty.tsx       # 빈 상태 UI
│   │   │   └── FeedError.tsx       # 에러 상태 UI + 다시 시도 버튼
│   │   │
│   │   └── filter/
│   │       ├── FilterBar.tsx       # [P1] 키워드 필터 바
│   │       └── FilterTag.tsx       # [P1] 개별 키워드 태그 (삭제 X 버튼 포함)
│   │
│   ├── lib/
│   │   ├── api.ts                  # fetch 래퍼: Envelope 파싱, 에러 처리
│   │   ├── queries.ts              # TanStack Query queryFn 및 queryKey 정의
│   │   ├── formatDate.ts           # published_at (ISO 8601) → "N분 전" 변환 (D-4 반영)
│   │   └── constants.ts            # TAB_TYPES, SOURCE_TYPE_MAP, 색상 토큰 매핑
│   │
│   └── types/
│       └── api.ts                  # API Contract TypeScript 타입 정의
│
├── tailwind.config.ts              # UI Spec 색상/간격/보더 토큰 커스텀 확장
├── package.json
└── .env.local.example              # NEXT_PUBLIC_API_BASE_URL 등
```

---

## 3. 컴포넌트 목록 및 구현 계획

### 레이아웃 컴포넌트 (P0)

| 컴포넌트 | 설명 | 파일 경로 | 우선순위 | 상태 |
|---------|------|---------|---------|------|
| GlobalHeader | sticky 헤더, 3개 자식 포함 | `components/layout/GlobalHeader.tsx` | P0 | pending |
| Logo | 레이더 아이콘 + 텍스트, `/` 링크 | `components/layout/Logo.tsx` | P0 | pending |
| SearchBar | 검색 입력, 클리어 X 버튼, Enter 동작 | `components/layout/SearchBar.tsx` | P0 | pending |
| FeedStatusBadge | 60초 폴링, 상태별 색상 점 | `components/layout/FeedStatusBadge.tsx` | P0 | pending |

### 피드 컴포넌트 (P0)

| 컴포넌트 | 설명 | 파일 경로 | 우선순위 | 상태 |
|---------|------|---------|---------|------|
| TabNav | 뉴스/VC블로그 2탭, URL 파라미터 연동 | `components/feed/TabNav.tsx` | P0 | pending |
| FeedList | useInfiniteQuery + IntersectionObserver 무한 스크롤 | `components/feed/FeedList.tsx` | P0 | pending |
| FeedItem | 텍스트 전용 카드, 외부 링크 새 탭 | `components/feed/FeedItem.tsx` | P0 | pending |
| SourceTag | source_type별 컬러 배지 | `components/feed/SourceTag.tsx` | P0 | pending |
| FeedSkeleton | shimmer 애니메이션, 5개 반복 | `components/feed/FeedSkeleton.tsx` | P0 | pending |
| FeedEmpty | 탭별 메시지, 레이더 아이콘 | `components/feed/FeedEmpty.tsx` | P0 | pending |
| FeedError | 에러 메시지, 다시 시도 버튼 | `components/feed/FeedError.tsx` | P0 | pending |

### 필터 컴포넌트 (P1)

| 컴포넌트 | 설명 | 파일 경로 | 우선순위 | 상태 |
|---------|------|---------|---------|------|
| FilterBar | 키워드 태그 목록, + 추가 버튼, URL 파라미터 연동 | `components/filter/FilterBar.tsx` | P1 | pending |
| FilterTag | 개별 태그, 활성/비활성 상태, X 삭제 | `components/filter/FilterTag.tsx` | P1 | pending |

### 페이지 (P0/P1)

| 파일 | 설명 | 우선순위 | 상태 |
|------|------|---------|------|
| `app/layout.tsx` | 루트 레이아웃: GlobalHeader, Pretendard 폰트 | P0 | pending |
| `app/page.tsx` | 메인 피드: TabNav + FilterBar + FeedList | P0 | pending |
| `app/search/page.tsx` | 검색 결과: SearchHeader + FeedList | P1 | pending |

---

## 4. 상태 관리 전략

### 원칙

- **서버 상태 (API 데이터):** TanStack Query로 관리. 캐싱, 재시도, 로딩/에러 상태 일임.
- **클라이언트 UI 상태:** React 로컬 state 사용. URL 파라미터와 동기화 필요한 것만 `useSearchParams` 활용.
- **전역 상태 관리 라이브러리 미사용:** Zustand, Redux 등 불필요. 상태 단순.

### 상태별 관리 방식

| 상태 | 관리 방법 | 위치 |
|------|---------|------|
| 활성 탭 (`tab`) | URL query param `?tab=news` | `app/page.tsx` (`useSearchParams`) |
| 키워드 필터 (`keyword`) | URL query param `?keyword=AI,시리즈A` | `app/page.tsx` (`useSearchParams`) |
| 피드 데이터 (목록, 페이지네이션) | TanStack Query `useInfiniteQuery` | `FeedList.tsx` |
| 검색 쿼리 | URL query param `?q=AI` | `app/search/page.tsx` |
| 검색 결과 | TanStack Query `useInfiniteQuery` | `app/search/page.tsx` → `FeedList.tsx` |
| 크롤링 상태 | TanStack Query `useQuery` (60초 폴링) | `FeedStatusBadge.tsx` |
| SearchBar 입력값 | React `useState` | `SearchBar.tsx` |
| FilterBar 인라인 입력 활성화 | React `useState` | `FilterBar.tsx` |

### URL 파라미터 설계

```
메인 피드: /?tab=news&keyword=AI,시리즈A
검색: /search?q=AI
```

- 탭 전환 시 keyword 파라미터 초기화 (탭별 독립 필터 — UI Spec 4-1)
- 빈 `q` 파라미터로 `/search` 접근 시 `/` 리다이렉트

---

## 5. 데이터 패칭 전략

### TanStack Query 설정

```
QueryClient 설정:
  staleTime: 5분 (서버 Redis TTL과 동일 기준)
  gcTime: 10분
  retry: 2회
  refetchOnWindowFocus: false (피드 특성상 의도적 새로고침 없음)
```

### 쿼리 키 설계

```typescript
// 피드 목록
['feed', tab, keyword]

// 검색 결과
['search', query]

// 크롤링 상태 (60초 폴링)
['status']

// 소스 목록 (정적 데이터, 긴 캐시)
['sources']
```

### 무한 스크롤 구현 방식

- `useInfiniteQuery` + `IntersectionObserver`
- FeedList 하단 sentinel 요소가 viewport에 진입하면 `fetchNextPage()` 호출
- `getNextPageParam`: `lastPage.meta.next_cursor` null이면 `undefined` 반환 (종료)

### FeedStatusBadge 폴링

- `useQuery({ refetchInterval: 60000 })`
- 백그라운드 탭에서도 폴링 유지 (`refetchIntervalInBackground: true`)

### API 클라이언트 (`lib/api.ts`)

- `NEXT_PUBLIC_API_BASE_URL` 환경변수 기준
- Envelope `{ data, error, meta }` 자동 언래핑
- `error` 필드 존재 시 `throw` → TanStack Query 에러 상태로 전달
- 개발 환경에서는 `http://localhost:8000` fallback

---

## 6. Tailwind 커스텀 토큰 설정 계획

`tailwind.config.ts`에서 UI Spec 1-2 ~ 1-5 색상/간격/보더 토큰을 CSS 커스텀 속성으로 확장.

### 색상 토큰 (UI Spec 1-2)

```typescript
// tailwind.config.ts (구조 예시 — 코드는 ephemeral agent가 작성)
theme.extend.colors = {
  'dark-900': '#111118',   // color-dark-900: 메인 배경
  'dark-800': '#1A1A24',   // color-dark-800: 카드 배경
  'dark-700': '#22222F',   // color-dark-700: hover 상태
  'dark-600': '#2E2E3E',   // color-dark-600: 보더/구분선
  'dark-500': '#3E3E52',   // color-dark-500: 비활성 아이콘
  'gray-100-custom': '#E8E8F0',  // 제목 텍스트
  'gray-300-custom': '#A0A0B8',  // 본문 텍스트
  'gray-500-custom': '#60607A',  // 메타 정보
  'accent-blue': '#4B6EF5',
  'accent-blue-h': '#6B8EFF',
  'accent-green': '#22C55E',
  'accent-amber': '#F59E0B',
  'accent-red': '#EF4444',
  // Source Tag 컬러
  'tag-news-bg': '#1E3A2F',
  'tag-news-text': '#22C55E',
  'tag-vc-bg': '#1A2A4A',
  'tag-vc-text': '#4B6EF5',
}
```

### 타이포그래피 (UI Spec 1-3)

Tailwind 기본 타입 스케일 그대로 사용. 별도 플러그인 불필요.
- `text-xl font-bold` → type-title-lg (20px 700)
- `text-base font-semibold` → type-title-md (16px 600)
- `text-sm font-normal` → type-body (14px 400)
- `text-xs font-normal` → type-meta (12px 400)
- `text-[11px] font-medium` → type-label (11px 500)

### 배경색 설정

```typescript
// globals.css
body { background-color: #111118; }  // color-dark-900
```

---

## 7. 타입 정의 계획

`src/types/api.ts`에 API Contract를 TypeScript 타입으로 정의.

### 핵심 타입

```typescript
// API Contract에서 도출되는 타입 (구조 — 코드는 ephemeral agent 작성)

interface ApiEnvelope<T> {
  data: T | null;
  error: { code: string; message: string } | null;
  meta: PaginationMeta | null;
}

interface PaginationMeta {
  next_cursor: string | null;
  has_more: boolean;
  total_count: number | null;
}

interface Source {
  id: number;
  name: string;
  slug: string;
  source_type: 'news' | 'vc_blog';
}

interface FeedItem {
  id: number;
  source: Source;
  title: string;
  url: string;
  summary: string | null;
  author: string | null;
  published_at: string;  // ISO 8601 UTC
}

interface StatusData {
  last_updated_at: string;
  status: 'ok' | 'warning' | 'error';
  sources: SourceStatus[];
}

interface SourceStatus {
  source_id: number;
  source_name: string;
  last_crawled_at: string;
  crawl_status: 'success' | 'failed' | 'running' | 'unknown';
}

type TabType = 'news' | 'vc_blog';
```

---

## 8. 라우팅 구조

Next.js 14 App Router 기준.

| 경로 | 파일 | 설명 |
|------|------|------|
| `/` | `app/page.tsx` | 통합 피드 메인. `?tab=news` 기본값 |
| `/search` | `app/search/page.tsx` | 검색 결과. `?q=` 필수, 없으면 `/` 리다이렉트 |
| `layout.tsx` | `app/layout.tsx` | GlobalHeader 공통 포함. QueryClientProvider 설정 |

### 레이아웃 구조

```
RootLayout (layout.tsx)
├── QueryClientProvider        ← TanStack Query 프로바이더
├── GlobalHeader               ← sticky 헤더 (공통)
└── {children}                 ← 페이지별 콘텐츠
    ├── MainPage (page.tsx)
    │   ├── TabNav
    │   ├── FilterBar [P1]
    │   └── FeedList
    └── SearchPage (search/page.tsx)
        ├── SearchHeader
        └── FeedList
```

---

## 9. 구현 우선순위 및 위임 계획

### Phase 1 — 프론트엔드 기반 (P0)

구현 순서와 ephemeral agent 위임 단위.

| 순서 | 위임 단위 | 파일 | 의존성 |
|------|---------|------|------|
| 1 | Next.js 프로젝트 초기화 + Tailwind 토큰 설정 | `tailwind.config.ts`, `globals.css`, `package.json` | 없음 |
| 2 | API 타입 정의 + 클라이언트 + 유틸 | `types/api.ts`, `lib/api.ts`, `lib/formatDate.ts`, `lib/constants.ts` | 없음 (API Contract 기준) |
| 3 | TanStack Query 설정 + queryFn 정의 | `lib/queries.ts`, QueryClientProvider 설정 | API 클라이언트 완료 |
| 4 | 루트 레이아웃 + Pretendard 폰트 | `app/layout.tsx` | 없음 |
| 5 | GlobalHeader 조립 | `GlobalHeader.tsx`, `Logo.tsx` | 레이아웃 완료 |
| 6 | SearchBar 구현 | `SearchBar.tsx` | GlobalHeader 완료 |
| 7 | FeedStatusBadge 구현 | `FeedStatusBadge.tsx` | queryFn 완료 |
| 8 | SourceTag 구현 | `SourceTag.tsx` | 타입 정의 완료 |
| 9 | FeedItem 구현 | `FeedItem.tsx` | SourceTag 완료 |
| 10 | FeedSkeleton / FeedEmpty / FeedError 구현 | 3개 파일 | 없음 |
| 11 | FeedList 구현 (무한 스크롤) | `FeedList.tsx` | FeedItem, FeedSkeleton, FeedEmpty, FeedError 완료 |
| 12 | TabNav 구현 | `TabNav.tsx` | 없음 |
| 13 | 메인 페이지 조립 | `app/page.tsx` | TabNav, FeedList 완료 |

### Phase 2 — 검색 + 필터 (P1)

| 순서 | 위임 단위 | 파일 | 의존성 |
|------|---------|------|------|
| 14 | FilterTag + FilterBar 구현 | `FilterTag.tsx`, `FilterBar.tsx` | 타입 정의 완료 |
| 15 | SearchPage 구현 | `app/search/page.tsx` | FeedList 완료 |

---

## 10. 미결 결정 사항

UI Spec에서 이관된 미결 항목 및 구현 시 결정이 필요한 사항.

| # | 항목 | 현재 방향 | 결정 시점 |
|---|------|---------|---------|
| D-3 | 요약 텍스트 null 처리 | 백엔드 제공 summary 사용. null이면 카드에서 요약 행 숨김 | FeedItem 구현 시 확정 |
| D-4 | 날짜 표시 형식 | API Contract에서 상대적 표시로 확정 (N분 전/N시간 전/MM월 DD일) | 확정 완료 |
| D-5 | 키워드 필터 초기 상태 | 빈 상태 (사용자가 직접 추가) — 서버 데이터 없이 단순 구현 우선 | FilterBar 구현 시 최종 확정 |
| FE-1 | 모바일 SearchBar 펼침 방식 | 검색 아이콘 클릭 → 헤더 아래 2행으로 SearchBar 표시 (UI Spec 5-2) | SearchBar 구현 시 |
| FE-2 | QueryClient Provider 위치 | `app/layout.tsx` 서버 컴포넌트 제약으로 별도 `providers.tsx` 클라이언트 컴포넌트 분리 | 레이아웃 구현 시 |
| FE-3 | 무한 스크롤 Intersection 방식 | `IntersectionObserver` 직접 사용 vs `react-intersection-observer` 라이브러리 | FeedList 구현 시 |

---

## 구현 게이트 체크리스트

- [ ] Next.js 프로젝트 초기화 완료
- [ ] Tailwind 색상 토큰 설정 완료
- [ ] TypeScript 타입 정의 완료
- [ ] API 클라이언트 구현 완료
- [ ] TanStack Query 설정 완료
- [ ] GlobalHeader (Logo + SearchBar + FeedStatusBadge) 구현 완료
- [ ] FeedItem + SourceTag 구현 완료
- [ ] FeedList 무한 스크롤 구현 완료
- [ ] TabNav 구현 완료
- [ ] 메인 페이지 (`/`) 동작 확인
- [ ] [P1] FilterBar + FilterTag 구현 완료
- [ ] [P1] SearchPage (`/search`) 동작 확인

---

*Frontend Lead 에이전트 작성 | 2026-02-21 | 기준: UI_Specs.md(승인 완료), API_Contract.md, Tech_Spec.md*
