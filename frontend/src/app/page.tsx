'use client';

import { useState, useCallback } from 'react';
import { useSearchParams, useRouter, usePathname } from 'next/navigation';
import { TabNav } from '@/components/feed/TabNav';
import { FeedList } from '@/components/feed/FeedList';
import { FilterBar } from '@/components/filter/FilterBar';
import type { TabType } from '@/types/api';
import { DEFAULT_TAB } from '@/lib/constants';

// 메인 피드 페이지 (/)
// URL 파라미터: ?tab=news&keyword=AI,시리즈A
export default function MainPage() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const rawTab = searchParams.get('tab') as TabType | null;
  const activeTab: TabType =
    rawTab === 'news' || rawTab === 'vc_blog' ? rawTab : DEFAULT_TAB;

  const rawKeyword = searchParams.get('keyword') ?? '';
  const keywords = rawKeyword
    ? rawKeyword.split(',').filter(Boolean)
    : [];

  const updateParams = useCallback(
    (tab: TabType, newKeywords: string[]) => {
      const params = new URLSearchParams();
      params.set('tab', tab);
      if (newKeywords.length > 0) {
        params.set('keyword', newKeywords.join(','));
      }
      router.replace(`${pathname}?${params.toString()}`, { scroll: false });
    },
    [router, pathname],
  );

  const handleTabChange = (tab: TabType) => {
    // 탭 전환 시 키워드 초기화 (UI Spec 4-1)
    updateParams(tab, []);
  };

  const handleKeywordsChange = (newKeywords: string[]) => {
    updateParams(activeTab, newKeywords);
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
          keyword={keywords.length > 0 ? keywords.join(',') : undefined}
        />
      </div>
    </div>
  );
}
