'use client';

import { redirect } from 'next/navigation';
import { useSearchParams } from 'next/navigation';
import { useSearchQuery } from '@/lib/queries';
import { FeedItem } from '@/components/feed/FeedItem';
import { FeedSkeleton } from '@/components/feed/FeedSkeleton';
import { FeedError } from '@/components/feed/FeedError';
import { useEffect, useRef, useCallback } from 'react';

// UI Spec 4-2: 검색 결과 페이지
// 빈 q → / 리다이렉트
export default function SearchPage() {
  const searchParams = useSearchParams();
  const query = searchParams.get('q') ?? '';

  // 빈 쿼리 접근 시 / 리다이렉트
  if (!query.trim()) {
    redirect('/');
  }

  return <SearchContent query={query} />;
}

function SearchContent({ query }: { query: string }) {
  const sentinelRef = useRef<HTMLDivElement>(null);
  const {
    data,
    isLoading,
    isError,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    refetch,
  } = useSearchQuery(query);

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
    const observer = new IntersectionObserver(handleIntersect, { rootMargin: '200px' });
    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [handleIntersect]);

  const allItems = data?.pages.flatMap((p) => p.items) ?? [];
  const totalCount = data?.pages[0]?.meta.total_count ?? null;

  return (
    <div className="max-w-feed mx-auto px-4 sm:px-6 py-6 pb-8">
      {/* SearchHeader */}
      {!isLoading && (
        <div className="mb-4">
          <span className="text-base font-semibold text-white">"{query}"</span>
          {totalCount !== null && (
            <span className="text-sm text-sr-gray-500 ml-2">
              {totalCount}개 결과
            </span>
          )}
        </div>
      )}

      {isLoading && <FeedSkeleton />}

      {isError && <FeedError onRetry={() => refetch()} />}

      {!isLoading && !isError && allItems.length === 0 && (
        <SearchEmpty query={query} />
      )}

      {!isLoading && !isError && allItems.map((item) => (
        <FeedItem key={item.id} item={item} />
      ))}

      <div ref={sentinelRef} className="h-px" aria-hidden="true" />

      {isFetchingNextPage && (
        <div className="mt-2">
          <FeedSkeleton />
        </div>
      )}
    </div>
  );
}

function SearchEmpty({ query }: { query: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
      {/* 돋보기 아이콘 48x48, dark-600 */}
      <svg
        width="48"
        height="48"
        viewBox="0 0 48 48"
        fill="none"
        aria-hidden="true"
        className="text-dark-600 mb-4"
      >
        <circle cx="21" cy="21" r="15" stroke="currentColor" strokeWidth="2" />
        <path d="M33 33L44 44" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      </svg>
      <p className="text-sm text-sr-gray-500 mb-1">
        <span className="text-sr-gray-300">"{query}"</span>에 대한 결과가 없습니다.
      </p>
      <p className="text-sm text-sr-gray-500">
        다른 키워드로 검색하거나, 더 짧은 키워드를 사용해 보세요.
      </p>
    </div>
  );
}
