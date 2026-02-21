'use client';

import { useState, useRef, type KeyboardEvent } from 'react';
import { FilterTag } from './FilterTag';
import { KEYWORD_PRESETS, MAX_FILTER_KEYWORDS } from '@/lib/constants';

interface FilterBarProps {
  keywords: string[];
  onKeywordsChange: (keywords: string[]) => void;
}

// UI Spec 3-2-B: 키워드 필터 바
// D-5 확정: 인기 키워드 프리셋 5개 초기 제공
// 최대 5개, 초과 시 입력창 비활성화
export function FilterBar({ keywords, onKeywordsChange }: FilterBarProps) {
  const [inputActive, setInputActive] = useState(false);
  const [inputValue, setInputValue] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  const atMax = keywords.length >= MAX_FILTER_KEYWORDS;

  const addKeyword = (kw: string) => {
    const trimmed = kw.trim();
    if (!trimmed || keywords.includes(trimmed) || atMax) return;
    onKeywordsChange([...keywords, trimmed]);
    setInputValue('');
    setInputActive(false);
  };

  const removeKeyword = (kw: string) => {
    onKeywordsChange(keywords.filter((k) => k !== kw));
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      addKeyword(inputValue);
    } else if (e.key === 'Escape') {
      setInputActive(false);
      setInputValue('');
    }
  };

  const handleBlur = () => {
    if (inputValue.trim()) {
      addKeyword(inputValue);
    } else {
      setInputActive(false);
      setInputValue('');
    }
  };

  // 프리셋: 아직 추가되지 않은 것만 표시
  const availablePresets = KEYWORD_PRESETS.filter((p) => !keywords.includes(p));

  return (
    <div className="max-w-feed mx-auto px-4 sm:px-6">
      <div className="py-3 flex flex-wrap items-center gap-2 overflow-x-auto scrollbar-hide">
        {/* 활성 태그들 */}
        {keywords.map((kw) => (
          <FilterTag key={kw} keyword={kw} active onRemove={removeKeyword} />
        ))}

        {/* 프리셋 태그들 (비활성) */}
        {availablePresets.map((kw) => (
          <FilterTag
            key={kw}
            keyword={kw}
            active={false}
            onClick={(k) => !atMax && addKeyword(k)}
          />
        ))}

        {/* + 키워드 추가 버튼 / 인라인 입력 */}
        {!atMax && (
          inputActive ? (
            <input
              ref={inputRef}
              autoFocus
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              onBlur={handleBlur}
              placeholder="키워드 입력..."
              className="
                min-w-[80px] h-7 px-2
                bg-dark-700 border border-accent-blue rounded-sm
                text-[11px] text-sr-gray-100 placeholder:text-sr-gray-500
                focus:outline-none
              "
            />
          ) : (
            <button
              type="button"
              onClick={() => setInputActive(true)}
              className="flex items-center gap-1 text-[11px] text-sr-gray-500 hover:text-sr-gray-300 transition-colors"
            >
              <svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true">
                <path d="M6 2V10M2 6H10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
              </svg>
              키워드 추가
            </button>
          )
        )}

        {atMax && (
          <span className="text-[11px] text-sr-gray-500">최대 {MAX_FILTER_KEYWORDS}개</span>
        )}
      </div>
    </div>
  );
}
