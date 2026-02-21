// 프론트엔드 상수 정의
// 기준: UI_Specs.md, API_Contract.md

import type { TabType, SourceType } from '@/types/api';

// 탭 정의 (D-2: 인물 탭 제거, 뉴스/VC블로그 2탭만)
export const TABS: { id: TabType; label: string }[] = [
  { id: 'news', label: '뉴스' },
  { id: 'vc_blog', label: 'VC 블로그' },
];

export const DEFAULT_TAB: TabType = 'news';

// Source type → SourceTag 스타일 매핑
export const SOURCE_TAG_STYLES: Record<
  SourceType,
  { bg: string; text: string; label: string }
> = {
  news: {
    bg: 'bg-tag-news-bg',
    text: 'text-tag-news-text',
    label: '뉴스',
  },
  vc_blog: {
    bg: 'bg-tag-vc-bg',
    text: 'text-tag-vc-text',
    label: 'VC',
  },
};

// FeedStatusBadge 색상 매핑
export const STATUS_COLORS = {
  ok: 'text-accent-green',
  warning: 'text-accent-amber',
  error: 'text-accent-red',
} as const;

// D-5 확정: 인기 키워드 프리셋 5개
export const KEYWORD_PRESETS: string[] = [
  'AI',
  '시리즈A',
  '핀테크',
  '헬스케어',
  '투자',
];

// FilterBar 최대 키워드 수
export const MAX_FILTER_KEYWORDS = 5;

// TanStack Query staleTime (5분)
export const FEED_STALE_TIME = 5 * 60 * 1000;

// FeedStatusBadge 폴링 주기 (60초)
export const STATUS_POLL_INTERVAL = 60 * 1000;

// 피드 기본 limit
export const FEED_DEFAULT_LIMIT = 20;

// 검색 결과 기본 limit
export const SEARCH_DEFAULT_LIMIT = 20;
