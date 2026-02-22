'use client';

import { Suspense, useCallback, useEffect, useRef } from 'react';
import { redirect, useRouter, usePathname } from 'next/navigation';
import { useSearchParams } from 'next/navigation';
import { useSearchQuery } from '@/lib/queries';
import { FeedItem } from '@/components/feed/FeedItem';
import { FeedSkeleton } from '@/components/feed/FeedSkeleton';
import { FeedError } from '@/components/feed/FeedError';
import { Pagination } from '@/components/feed/Pagination';

// UI Spec 4-2: 검색 결과 페이지
// URL: /search?q=AI&page=2 (D-7 페이지네이션)
// 빈 q -> / 리다이렉트
export default function SearchPage() {
  return (
    <Suspense>
      <SearchPageContent />
    </Suspense>
  );
}

function SearchPageContent() {
  const searchParams = useSearchParams();
  const query = searchParams.get('q') ?? '';

  // 빈 쿼리 접근 시 / 리다이렉트
  if (!query.trim()) {
    redirect('/');
  }

  const rawPage = searchParams.get('page');
  const parsedPage = rawPage ? parseInt(rawPage, 10) : 1;
  const currentPage = Number.isFinite(parsedPage) && parsedPage >= 1 ? parsedPage : 1;

  return <SearchContent query={query} page={currentPage} />;
}

function SearchContent({ query, page }: { query: string; page: number }) {
  const router = useRouter();
  const pathname = usePathname();
  const listTopRef = useRef<HTMLDivElement>(null);
  const prevPageRef = useRef(page);

  const {
    data,
    isLoading,
    isError,
    isPlaceholderData,
    refetch,
  } = useSearchQuery(query, page);

  // 페이지 전환 시 스크롤 상단 이동
  useEffect(() => {
    if (prevPageRef.current !== page) {
      prevPageRef.current = page;
      listTopRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }, [page]);

  const handlePageChange = useCallback(
    (newPage: number) => {
      const params = new URLSearchParams();
      params.set('q', query);
      if (newPage > 1) params.set('page', String(newPage));
      router.push(`${pathname}?${params.toString()}`, { scroll: false });
    },
    [router, pathname, query],
  );

  const items = data?.items ?? [];
  const meta = data?.meta;
  const totalPages = meta?.total_pages ?? 0;
  const totalCount = meta?.total_count ?? 0;

  return (
    <div className="max-w-feed mx-auto px-4 sm:px-6 py-6 pb-8" ref={listTopRef}>
      {/* SearchHeader */}
      {!isLoading && (
        <div className="mb-4">
          <span className="text-base font-semibold text-sr-gray-100">&ldquo;{query}&rdquo;</span>
          <span className="text-sm text-sr-gray-500 ml-2">
            {totalCount}개 결과
          </span>
        </div>
      )}

      {/* 로딩 */}
      {isLoading && !data && <FeedSkeleton />}

      {/* 에러 */}
      {isError && <FeedError onRetry={() => refetch()} />}

      {/* 빈 결과 */}
      {!isLoading && !isError && items.length === 0 && !isPlaceholderData && (
        <SearchEmpty query={query} />
      )}

      {/* 결과 목록 */}
      {!isError && items.length > 0 && (
        isPlaceholderData ? (
          <FeedSkeleton />
        ) : (
          items.map((item) => (
            <FeedItem key={item.id} item={item} />
          ))
        )
      )}

      {/* 페이지네이션: 1페이지 이하/0개/에러 시 숨김 */}
      {!isError && totalPages > 1 && (
        <Pagination
          currentPage={page}
          totalPages={totalPages}
          isLoading={isPlaceholderData}
          onPageChange={handlePageChange}
        />
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
        <span className="text-sr-gray-300">&ldquo;{query}&rdquo;</span>에 대한 결과가 없습니다.
      </p>
      <p className="text-sm text-sr-gray-500">
        다른 키워드로 검색하거나, 더 짧은 키워드를 사용해 보세요.
      </p>
    </div>
  );
}
