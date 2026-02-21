'use client';

import { useEffect, useRef, useCallback } from 'react';
import type { TabType } from '@/types/api';
import { useFeedQuery } from '@/lib/queries';
import { FeedItem } from './FeedItem';
import { FeedSkeleton } from './FeedSkeleton';
import { FeedEmpty } from './FeedEmpty';
import { FeedError } from './FeedError';

interface FeedListProps {
  tab: TabType;
  keyword?: string;
}

// UI Spec: 무한 스크롤 피드 컨테이너
// IntersectionObserver로 하단 sentinel 감지 → fetchNextPage
export function FeedList({ tab, keyword }: FeedListProps) {
  const sentinelRef = useRef<HTMLDivElement>(null);
  const {
    data,
    isLoading,
    isError,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    refetch,
  } = useFeedQuery(tab, keyword);

  const handleIntersect = useCallback(
    (entries: IntersectionObserverEntry[]) => {
      if (entries[0].isIntersecting && hasNextPage && !isFetchingNextPage) {
        fetchNextPage();
      }
    },
    [fetchNextPage, hasNextPage, isFetchingNextPage],
  );

  useEffect(() => {
    const sentinel = sentinelRef.current;
    if (!sentinel) return;

    const observer = new IntersectionObserver(handleIntersect, {
      rootMargin: '200px', // 하단 200px 전에 미리 로드
    });
    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [handleIntersect]);

  if (isLoading) return <FeedSkeleton />;
  if (isError) return <FeedError onRetry={() => refetch()} />;

  const allItems = data?.pages.flatMap((page) => page.items) ?? [];

  if (allItems.length === 0) return <FeedEmpty tab={tab} />;

  return (
    <div>
      {allItems.map((item) => (
        <FeedItem key={item.id} item={item} />
      ))}

      {/* 무한 스크롤 sentinel */}
      <div ref={sentinelRef} className="h-px" aria-hidden="true" />

      {/* 추가 로딩 스켈레톤 */}
      {isFetchingNextPage && (
        <div className="mt-2">
          <FeedSkeleton />
        </div>
      )}

      {/* 더 이상 피드 없음 */}
      {!hasNextPage && allItems.length > 0 && (
        <p className="text-center text-xs text-sr-gray-500 py-8">
          모든 피드를 불러왔습니다.
        </p>
      )}
    </div>
  );
}
