'use client';

import { TABS } from '@/lib/constants';
import type { TabType } from '@/types/api';

interface TabNavProps {
  activeTab: TabType;
  onTabChange: (tab: TabType) => void;
}

// UI Spec 3-2-A: 뉴스 / VC 블로그 2탭 (D-2: 인물 탭 없음)
// sticky: top-14 (GlobalHeader 아래 고정)
export function TabNav({ activeTab, onTabChange }: TabNavProps) {
  return (
    <nav
      className="sticky top-14 z-10 bg-dark-900 border-b border-dark-600"
      aria-label="피드 탭 네비게이션"
    >
      <div className="max-w-feed mx-auto px-4 sm:px-6">
        <div className="flex gap-1">
          {TABS.map((tab) => {
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => onTabChange(tab.id)}
                role="tab"
                aria-selected={isActive}
                className={`
                  px-4 py-3 text-sm leading-none
                  border-b-2 transition-colors duration-200 ease-out
                  ${
                    isActive
                      ? 'text-sr-gray-100 border-accent-blue'
                      : 'text-sr-gray-500 border-transparent hover:text-sr-gray-300'
                  }
                `}
              >
                {tab.label}
              </button>
            );
          })}
        </div>
      </div>
    </nav>
  );
}
