'use client';

interface FeedErrorProps {
  onRetry?: () => void;
}

// UI Spec 3-2-F: 에러 상태 컴포넌트
export function FeedError({ onRetry }: FeedErrorProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
      {/* 경고 아이콘 48x48, accent-amber */}
      <svg
        width="48"
        height="48"
        viewBox="0 0 48 48"
        fill="none"
        aria-hidden="true"
        className="text-accent-amber mb-4"
      >
        <path
          d="M24 6L44 42H4L24 6Z"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinejoin="round"
        />
        <line x1="24" y1="20" x2="24" y2="30" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
        <circle cx="24" cy="36" r="1.5" fill="currentColor" />
      </svg>
      <p className="text-sm text-sr-gray-300 mb-1">피드를 불러오지 못했습니다.</p>
      <p className="text-sm text-sr-gray-500 mb-4">잠시 후 다시 시도해주세요.</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="
            px-4 py-2 rounded-md text-sm text-sr-gray-100
            bg-dark-700 border border-dark-600
            hover:bg-dark-600 transition-colors duration-100
          "
        >
          다시 시도
        </button>
      )}
    </div>
  );
}
