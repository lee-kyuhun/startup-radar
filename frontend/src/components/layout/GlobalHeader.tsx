'use client';

import { useState } from 'react';
import { Logo } from './Logo';
import { SearchBar } from './SearchBar';
import { FeedStatusBadge } from './FeedStatusBadge';

// UI Spec 3-1: sticky 헤더 (높이 56px desktop, 52px mobile)
// 모바일: 검색 아이콘 탭 → 2행 SearchBar 펼침 (FE-1)
export function GlobalHeader() {
  const [mobileSearchOpen, setMobileSearchOpen] = useState(false);

  return (
    <header className="sticky top-0 z-20 bg-dark-800 border-b border-dark-600">
      {/* 1행: Logo / SearchBar / StatusBadge */}
      <div className="h-14 flex items-center px-4 sm:px-6 gap-4">
        {/* Logo */}
        <div className="flex-shrink-0">
          <Logo />
        </div>

        {/* SearchBar — desktop: 중앙, max-480px */}
        <div className="hidden sm:flex flex-1 justify-center">
          <SearchBar className="w-full max-w-[480px]" />
        </div>

        {/* 우측: 모바일 검색 버튼 + StatusBadge */}
        <div className="flex items-center gap-3 ml-auto sm:ml-0">
          {/* 모바일 검색 아이콘 버튼 */}
          <button
            className="sm:hidden text-sr-gray-500 hover:text-white transition-colors"
            onClick={() => setMobileSearchOpen((prev) => !prev)}
            aria-label="검색창 열기"
            aria-expanded={mobileSearchOpen}
          >
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
              <circle cx="9" cy="9" r="6" stroke="currentColor" strokeWidth="1.5" />
              <path d="M14 14L18 18" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
            </svg>
          </button>

          <FeedStatusBadge />
        </div>
      </div>

      {/* 2행: 모바일 SearchBar (펼쳐졌을 때) */}
      {mobileSearchOpen && (
        <div className="sm:hidden px-4 pb-3">
          <SearchBar className="w-full" />
        </div>
      )}
    </header>
  );
}
