'use client';

interface FilterTagProps {
  keyword: string;
  active?: boolean;
  onRemove?: (keyword: string) => void;
  onClick?: (keyword: string) => void;
}

// UI Spec 3-2-B: 개별 키워드 태그
// - 활성: accent-blue 배경/보더
// - X 버튼으로 삭제
export function FilterTag({ keyword, active = true, onRemove, onClick }: FilterTagProps) {
  return (
    <span
      className={`
        inline-flex items-center gap-1
        h-7 px-2
        rounded-sm text-[11px] font-medium
        border transition-colors duration-150 cursor-pointer
        ${
          active
            ? 'bg-accent-blue/20 border-accent-blue text-sr-gray-100'
            : 'bg-dark-700 border-dark-600 text-sr-gray-100 hover:border-sr-gray-500'
        }
      `}
      onClick={() => onClick?.(keyword)}
    >
      <span>{keyword}</span>
      {onRemove && (
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            onRemove(keyword);
          }}
          className="text-sr-gray-500 hover:text-sr-gray-100 transition-colors ml-0.5"
          aria-label={`${keyword} 필터 제거`}
        >
          <svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true">
            <path d="M2 2L10 10M10 2L2 10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
        </button>
      )}
    </span>
  );
}
