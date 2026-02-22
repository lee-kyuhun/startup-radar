// TanStack Query queryFn 정의
// 기준: API_Contract.md v1.1 (오프셋 기반 페이지네이션)

import {
  useQuery,
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
  feed: (tab: TabType, page: number, keyword?: string) =>
    ['feed', tab, page, keyword ?? ''] as const,
  search: (query: string, page: number) => ['search', query, page] as const,
  status: () => ['status'] as const,
  sources: () => ['sources'] as const,
};

// --- Feed 페이지네이션 쿼리 (v1.1: useInfiniteQuery -> useQuery) ---

export function useFeedQuery(tab: TabType, page: number, keyword?: string) {
  return useQuery<FeedResponse>({
    queryKey: queryKeys.feed(tab, page, keyword),
    queryFn: () =>
      fetchFeed({
        tab,
        page,
        limit: FEED_DEFAULT_LIMIT,
        keyword,
      }),
    staleTime: FEED_STALE_TIME,
    placeholderData: (previousData) => previousData, // keepPreviousData equivalent in v5
  });
}

// --- 검색 페이지네이션 쿼리 (v1.1: useInfiniteQuery -> useQuery) ---

export function useSearchQuery(query: string, page: number) {
  return useQuery<FeedResponse>({
    queryKey: queryKeys.search(query, page),
    queryFn: () =>
      fetchSearch({
        q: query,
        page,
        limit: SEARCH_DEFAULT_LIMIT,
      }),
    enabled: query.length > 0,
    staleTime: FEED_STALE_TIME,
    placeholderData: (previousData) => previousData,
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
