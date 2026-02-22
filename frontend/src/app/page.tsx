'use client';

import { Suspense, useCallback } from 'react';
import { useSearchParams, useRouter, usePathname } from 'next/navigation';
import { TabNav } from '@/components/feed/TabNav';
import { FeedList } from '@/components/feed/FeedList';
import { FilterBar } from '@/components/filter/FilterBar';
import type { TabType } from '@/types/api';
import { DEFAULT_TAB } from '@/lib/constants';

// 메인 피드 페이지 (/)
// URL 파라미터: ?tab=news&page=3&keyword=AI,시리즈A (D-7)
export default function MainPage() {
  return (
    <Suspense>
      <MainPageContent />
    </Suspense>
  );
}

function MainPageContent() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  // --- URL 파라미터 파싱 ---
  const rawTab = searchParams.get('tab') as TabType | null;
  const activeTab: TabType =
    rawTab === 'news' || rawTab === 'vc_blog' ? rawTab : DEFAULT_TAB;

  const rawPage = searchParams.get('page');
  const parsedPage = rawPage ? parseInt(rawPage, 10) : 1;
  // 유효하지 않은 페이지 번호: 1페이지로 폴백 (0, 음수, NaN)
  const currentPage = Number.isFinite(parsedPage) && parsedPage >= 1 ? parsedPage : 1;

  const rawKeyword = searchParams.get('keyword') ?? '';
  const keywords = rawKeyword
    ? rawKeyword.split(',').filter(Boolean)
    : [];

  // --- URL 업데이트 헬퍼 ---
  const buildUrl = useCallback(
    (tab: TabType, page: number, kw: string[]) => {
      const params = new URLSearchParams();
      params.set('tab', tab);
      if (page > 1) params.set('page', String(page));
      if (kw.length > 0) params.set('keyword', kw.join(','));
      return `${pathname}?${params.toString()}`;
    },
    [pathname],
  );

  // --- 탭 전환: 1페이지로 리셋, 키워드 초기화 (UI Spec D-7, 4-1) ---
  const handleTabChange = (tab: TabType) => {
    router.push(buildUrl(tab, 1, []), { scroll: false });
  };

  // --- 키워드 변경: 1페이지로 리셋 (UI Spec 4-1) ---
  const handleKeywordsChange = (newKeywords: string[]) => {
    router.push(buildUrl(activeTab, 1, newKeywords), { scroll: false });
  };

  // --- 페이지 변경: URL 업데이트 ---
  const handlePageChange = (page: number) => {
    router.push(buildUrl(activeTab, page, keywords), { scroll: false });
  };

  return (
    <div>
      <TabNav activeTab={activeTab} onTabChange={handleTabChange} />
      <FilterBar
        keywords={keywords}
        onKeywordsChange={handleKeywordsChange}
      />
      <div className="max-w-feed mx-auto px-4 sm:px-6 py-6 pb-8">
        <FeedList
          tab={activeTab}
          page={currentPage}
          keyword={keywords.length > 0 ? keywords.join(',') : undefined}
          onPageChange={handlePageChange}
        />
      </div>
    </div>
  );
}
