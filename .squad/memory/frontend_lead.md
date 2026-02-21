# Frontend Lead 에이전트 — PJ004 프로젝트 메모리

> 마지막 업데이트: 2026-02-21

---

## 현재 상태

- Frontend Spec 작성 완료: `.squad/03_architecture/Frontend_Spec.md`
- Tech Spec 승인 완료 (`tech_spec_approved: true`)
- **Wave 1~3 구현 완료 (2026-02-21)** — 전체 컴포넌트 구현 완료, `tsc --noEmit` 통과
- 다음 단계: `npm install` 후 `next dev` 실행 → 백엔드 연동

---

## 핵심 아키텍처 결정 (확정)

### 기술 선택

- **Next.js 14 App Router** — SSR로 LCP 목표 달성, Vercel 공식 지원
- **TanStack Query v5** — 서버 상태 전용. Zustand 등 전역 상태 라이브러리 불필요
- **클라이언트 상태** — React useState + URL query params (`useSearchParams`) 조합
- **Pretendard 폰트** — CSS 변수 `--font-pretendard` 방식으로 적용 (next/font 로컬 호스팅 대신 CSS variable)
- **QueryClientProvider** — 별도 `providers.tsx` 클라이언트 컴포넌트로 분리 (FE-2 해결)
- **IntersectionObserver** — 직접 사용 (라이브러리 미사용) (FE-3 해결)

### 상태 관리 원칙

- 서버 데이터 (피드, 검색, 상태) → TanStack Query
- UI 상태 (탭, 키워드 필터) → URL query param (`?tab=news&keyword=AI`)
- 로컬 UI 상태 (입력값 등) → React useState

### 라우팅

```
/ → 메인 피드 (TabNav + FeedList)
/search?q=... → 검색 결과
```

### 쿼리 키 체계

```typescript
['feed', tab, keyword]  // 피드 목록
['search', query]       // 검색 결과
['status']              // 크롤링 상태 (60초 폴링)
['sources']             // 소스 목록 (정적, 긴 캐시)
```

---

## UI Spec 확정 결정사항 반영 현황

| ID  | 결정 내용 | Frontend 반영 |
|-----|-----------|---------------|
| D-1 | 단일 컬럼 (max-width 720px) | `max-w-feed` Tailwind 커스텀 토큰, 모든 페이지에 반영 |
| D-2 | 인물 탭 제거 (뉴스/VC 2탭만) | `constants.ts` TABS 배열에 2개만, TabNav에서 렌더링 |
| D-3 | summary null → 요약 행 숨김 | FeedItem에서 `{item.summary && <p>...</p>}` |
| D-4 | 날짜 상대적 표시 (N분 전) | `lib/formatDate.ts` → `formatRelativeDate()` |
| D-5 | 인기 키워드 프리셋 5개 | `constants.ts` KEYWORD_PRESETS, FilterBar에서 비활성 태그로 표시 |
| D-6 | 썸네일 없음 (텍스트 전용) | FeedItem 이미지 영역 없음 |

---

## 컴포넌트 구현 현황

| 컴포넌트 | 상태 | 경로 |
|---------|------|------|
| package.json | done | `frontend/package.json` |
| tsconfig.json | done | `frontend/tsconfig.json` |
| next.config.js | done | `frontend/next.config.js` |
| postcss.config.js | done | `frontend/postcss.config.js` |
| tailwind.config.ts | done | `frontend/tailwind.config.ts` |
| globals.css | done | `frontend/src/app/globals.css` |
| types/api.ts | done | `frontend/src/types/api.ts` |
| lib/api.ts | done | `frontend/src/lib/api.ts` |
| lib/queries.ts | done | `frontend/src/lib/queries.ts` |
| lib/formatDate.ts | done | `frontend/src/lib/formatDate.ts` |
| lib/constants.ts | done | `frontend/src/lib/constants.ts` |
| app/providers.tsx | done | `frontend/src/app/providers.tsx` |
| app/layout.tsx | done | `frontend/src/app/layout.tsx` |
| GlobalHeader.tsx | done | `frontend/src/components/layout/GlobalHeader.tsx` |
| Logo.tsx | done | `frontend/src/components/layout/Logo.tsx` |
| SearchBar.tsx | done | `frontend/src/components/layout/SearchBar.tsx` |
| FeedStatusBadge.tsx | done | `frontend/src/components/layout/FeedStatusBadge.tsx` |
| TabNav.tsx | done | `frontend/src/components/feed/TabNav.tsx` |
| FeedList.tsx | done | `frontend/src/components/feed/FeedList.tsx` |
| FeedItem.tsx | done | `frontend/src/components/feed/FeedItem.tsx` |
| SourceTag.tsx | done | `frontend/src/components/feed/SourceTag.tsx` |
| FeedSkeleton.tsx | done | `frontend/src/components/feed/FeedSkeleton.tsx` |
| FeedEmpty.tsx | done | `frontend/src/components/feed/FeedEmpty.tsx` |
| FeedError.tsx | done | `frontend/src/components/feed/FeedError.tsx` |
| FilterBar.tsx [P1] | done | `frontend/src/components/filter/FilterBar.tsx` |
| FilterTag.tsx [P1] | done | `frontend/src/components/filter/FilterTag.tsx` |
| app/page.tsx | done | `frontend/src/app/page.tsx` |
| app/search/page.tsx [P1] | done | `frontend/src/app/search/page.tsx` |

---

## 해결된 결정 사항

| # | 항목 | 결정 내용 |
|---|------|---------|
| D-3 | summary null 처리 | FeedItem에서 null이면 요약 행 숨김 |
| D-5 | 키워드 필터 초기 상태 | 인기 키워드 프리셋 5개 (AI, 시리즈A, 핀테크, 헬스케어, 투자) |
| FE-1 | 모바일 SearchBar | 검색 아이콘 탭 → 헤더 아래 2행으로 펼침 |
| FE-2 | QueryClient Provider | `providers.tsx` 클라이언트 컴포넌트로 분리 |
| FE-3 | IntersectionObserver | 직접 사용 (rootMargin: 200px 선행 로드) |

---

## 패턴 메모

- Tailwind 커스텀 토큰 `sr-gray-*` 사용 (기본 gray와 충돌 방지)
- `max-w-feed` 커스텀 토큰 = 720px (UI Spec D-1)
- FeedList와 SearchPage 모두 동일한 IntersectionObserver 패턴 사용
- FilterBar: 활성 태그(삭제 X 포함) + 비활성 프리셋 태그(클릭으로 활성화) 구분
- `shimmer` CSS 클래스 → globals.css에서 정의, FeedSkeleton에서 재사용

---

## 다음 세션에서 할 것

1. `cd frontend && npm install && npm run dev` 실행하여 빌드 확인
2. 백엔드 API 준비 완료 후 `.env.local` 설정 (`NEXT_PUBLIC_API_BASE_URL`)
3. 실제 연동 테스트 (피드 로딩, 탭 전환, 검색, StatusBadge 폴링)
4. Vercel 배포 설정 (CI/CD)
