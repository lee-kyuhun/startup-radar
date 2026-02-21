import type { FeedItem as FeedItemType } from '@/types/api';
import { SourceTag } from './SourceTag';
import { formatRelativeDate } from '@/lib/formatDate';

interface FeedItemProps {
  item: FeedItemType;
}

// UI Spec 3-2-C: 텍스트 전용 피드 카드 (D-6: 썸네일 없음)
// 클릭 시 외부 링크 새 탭 오픈, 키보드 접근성 포함
export function FeedItem({ item }: FeedItemProps) {
  const handleClick = () => {
    window.open(item.url, '_blank', 'noopener,noreferrer');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleClick();
    }
  };

  return (
    <article
      role="article"
      tabIndex={0}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      className="
        bg-dark-800 border border-dark-600 rounded-md
        p-4 mb-3 cursor-pointer
        hover:bg-dark-700 transition-colors duration-150 ease-out
        focus:outline-none focus:ring-1 focus:ring-accent-blue
      "
      aria-label={item.title}
    >
      {/* 행 1: SourceTag + 출처명 + 날짜 + 외부링크 아이콘 */}
      <div className="flex items-center gap-2 mb-3">
        <SourceTag sourceType={item.source.source_type} sourceName={item.source.name} />
        {item.author && (
          <span className="text-xs text-sr-gray-300 truncate max-w-[120px]">{item.author}</span>
        )}
        <div className="flex items-center gap-2 ml-auto flex-shrink-0">
          <time
            dateTime={item.published_at}
            className="text-xs text-sr-gray-500 whitespace-nowrap"
          >
            {formatRelativeDate(item.published_at)}
          </time>
          {/* 외부 링크 아이콘 16x16 */}
          <svg
            width="16"
            height="16"
            viewBox="0 0 16 16"
            fill="none"
            aria-hidden="true"
            className="text-sr-gray-500 hover:text-accent-blue transition-colors flex-shrink-0"
          >
            <path
              d="M6 3H3C2.44772 3 2 3.44772 2 4V13C2 13.5523 2.44772 14 3 14H12C12.5523 14 13 13.5523 13 13V10M10 2H14M14 2V6M14 2L7 9"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </div>
      </div>

      {/* 행 2: 제목 (최대 2줄) */}
      <h2 className="text-base font-semibold text-sr-gray-100 mb-2 line-clamp-2 leading-snug">
        {item.title}
      </h2>

      {/* 행 3: 요약 (D-3: null이면 숨김, 최대 3줄) */}
      {item.summary && (
        <p className="text-sm text-sr-gray-300 line-clamp-3 leading-relaxed">
          {item.summary}
        </p>
      )}
    </article>
  );
}
