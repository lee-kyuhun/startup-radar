'use client';

import { useEffect, useRef } from 'react';
import type { TabType } from '@/types/api';
import { useFeedQuery } from '@/lib/queries';
import { FeedItem } from './FeedItem';
import { FeedSkeleton } from './FeedSkeleton';
import { FeedEmpty } from './FeedEmpty';
import { FeedError } from './FeedError';
import { Pagination } from './Pagination';

interface FeedListProps {
  tab: TabType;
  page: number;
  keyword?: string;
  onPageChange: (page: number) => void;
}

// UI Spec 3-2: 페이지네이션 피드 컨테이너 (D-7)
// useQuery + keepPreviousData, 무한 스크롤 제거
export function FeedList({ tab, page, keyword, onPageChange }: FeedListProps) {
  const listTopRef = useRef<HTMLDivElement>(null);
  const prevPageRef = useRef(page);

  const {
    data,
    isLoading,
    isError,
    isPlaceholderData,
    refetch,
  } = useFeedQuery(tab, page, keyword);

  // 페이지 전환 시 스크롤 상단 이동
  useEffect(() => {
    if (prevPageRef.current !== page) {
      prevPageRef.current = page;
      listTopRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }, [page]);

  const items = data?.items ?? [];
  const meta = data?.meta;
  const totalPages = meta?.total_pages ?? 0;

  // 로딩 중 (첫 로드, placeholder 없음)
  if (isLoading && !data) {
    return (
      <div ref={listTopRef}>
        <FeedSkeleton />
      </div>
    );
  }

  // 에러
  if (isError) {
    return (
      <div ref={listTopRef}>
        <FeedError onRetry={() => refetch()} />
      </div>
    );
  }

  // 빈 상태
  if (items.length === 0 && !isPlaceholderData) {
    return (
      <div ref={listTopRef}>
        <FeedEmpty tab={tab} />
      </div>
    );
  }

  return (
    <div ref={listTopRef}>
      {/* 페이지 전환 중 스켈레톤 (placeholder data가 표시되는 동안) */}
      {isPlaceholderData ? (
        <FeedSkeleton />
      ) : (
        items.map((item) => (
          <FeedItem key={item.id} item={item} />
        ))
      )}

      {/* 페이지네이션: 20개 이하(1페이지)/0개/에러 시 숨김 */}
      {totalPages > 1 && (
        <Pagination
          currentPage={page}
          totalPages={totalPages}
          isLoading={isPlaceholderData}
          onPageChange={onPageChange}
        />
      )}
    </div>
  );
}
