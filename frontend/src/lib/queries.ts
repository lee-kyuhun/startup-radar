// TanStack Query queryFn 정의
// 기준: API_Contract.md, Frontend_Spec.md 섹션 5

import {
  useInfiniteQuery,
  useQuery,
  type InfiniteData,
  type UseInfiniteQueryOptions,
  type UseQueryOptions,
} from '@tanstack/react-query';
import {
  fetchFeed,
  fetchSearch,
  fetchStatus,
  fetchSources,
  type FeedResponse,
} from './api';
import type { StatusData, SourceWithStatus, TabType } from '@/types/api';
import {
  FEED_STALE_TIME,
  STATUS_POLL_INTERVAL,
  FEED_DEFAULT_LIMIT,
  SEARCH_DEFAULT_LIMIT,
} from './constants';

// --- Query Keys ---

export const queryKeys = {
  feed: (tab: TabType, keyword?: string) =>
    ['feed', tab, keyword ?? ''] as const,
  search: (query: string) => ['search', query] as const,
  status: () => ['status'] as const,
  sources: () => ['sources'] as const,
};

// --- Feed 무한 스크롤 쿼리 ---

export function useFeedQuery(tab: TabType, keyword?: string) {
  return useInfiniteQuery({
    queryKey: queryKeys.feed(tab, keyword),
    queryFn: ({ pageParam }) =>
      fetchFeed({
        tab,
        cursor: pageParam as string | undefined,
        limit: FEED_DEFAULT_LIMIT,
        keyword,
      }),
    initialPageParam: undefined as string | undefined,
    getNextPageParam: (lastPage: FeedResponse) =>
      lastPage.meta.next_cursor ?? undefined,
    staleTime: FEED_STALE_TIME,
  });
}

// --- 검색 무한 스크롤 쿼리 ---

export function useSearchQuery(query: string) {
  return useInfiniteQuery({
    queryKey: queryKeys.search(query),
    queryFn: ({ pageParam }) =>
      fetchSearch({
        q: query,
        cursor: pageParam as string | undefined,
        limit: SEARCH_DEFAULT_LIMIT,
      }),
    initialPageParam: undefined as string | undefined,
    getNextPageParam: (lastPage: FeedResponse) =>
      lastPage.meta.next_cursor ?? undefined,
    enabled: query.length > 0,
    staleTime: FEED_STALE_TIME,
  });
}

// --- 크롤링 상태 폴링 쿼리 (60초) ---

export function useStatusQuery() {
  return useQuery<StatusData>({
    queryKey: queryKeys.status(),
    queryFn: fetchStatus,
    refetchInterval: STATUS_POLL_INTERVAL,
    refetchIntervalInBackground: true,
    staleTime: STATUS_POLL_INTERVAL,
  });
}

// --- 소스 목록 쿼리 (정적, 길게 캐시) ---

export function useSourcesQuery() {
  return useQuery<SourceWithStatus[]>({
    queryKey: queryKeys.sources(),
    queryFn: fetchSources,
    staleTime: 30 * 60 * 1000, // 30분
  });
}
