'use client';

import { useState, useRef, type FormEvent } from 'react';
import { useRouter } from 'next/navigation';

// UI Spec 3-1: 검색 입력창
// - Enter / 돋보기 클릭 → /search?q={입력값}
// - 내용 있을 때 우측 X 버튼 표시
// - 모바일: 부모에서 show prop으로 표시/숨김 제어
interface SearchBarProps {
  className?: string;
  defaultValue?: string;
}

export function SearchBar({ className = '', defaultValue = '' }: SearchBarProps) {
  const router = useRouter();
  const [value, setValue] = useState(defaultValue);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const trimmed = value.trim();
    if (trimmed) {
      router.push(`/search?q=${encodeURIComponent(trimmed)}`);
    }
  };

  const handleClear = () => {
    setValue('');
    inputRef.current?.focus();
  };

  return (
    <form
      onSubmit={handleSubmit}
      className={`relative flex items-center ${className}`}
      role="search"
    >
      {/* 돋보기 아이콘 (좌측) */}
      <button
        type="submit"
        className="absolute left-3 text-sr-gray-500 hover:text-sr-gray-300 transition-colors"
        aria-label="검색"
      >
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
          <circle cx="7" cy="7" r="5" stroke="currentColor" strokeWidth="1.5" />
          <path d="M11 11L14 14" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
      </button>

      <input
        ref={inputRef}
        type="text"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder="뉴스, VC 블로그 검색..."
        className="
          w-full h-9 pl-8 pr-8
          bg-dark-700 border border-dark-600
          rounded-md text-sm text-sr-gray-300 placeholder:text-sr-gray-500
          focus:outline-none focus:border-accent-blue
          transition-colors duration-150
        "
        aria-label="검색어 입력"
      />

      {/* X 클리어 버튼 (내용 있을 때만) */}
      {value && (
        <button
          type="button"
          onClick={handleClear}
          className="absolute right-3 text-sr-gray-500 hover:text-white transition-colors"
          aria-label="검색어 지우기"
        >
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
            <path d="M2 2L12 12M12 2L2 12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
        </button>
      )}
    </form>
  );
}
