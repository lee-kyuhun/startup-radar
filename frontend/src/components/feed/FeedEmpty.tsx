import type { TabType } from '@/types/api';

interface FeedEmptyProps {
  tab?: TabType;
}

const MESSAGES: Record<TabType, { title: string; subtitle: string }> = {
  news: {
    title: '수집된 뉴스 기사가 아직 없습니다.',
    subtitle: '크롤링이 완료되면 자동으로 업데이트됩니다.',
  },
  vc_blog: {
    title: '수집된 VC 블로그 포스트가 아직 없습니다.',
    subtitle: '크롤링이 완료되면 자동으로 업데이트됩니다.',
  },
};

// UI Spec 3-2-E: 빈 상태 컴포넌트
export function FeedEmpty({ tab = 'news' }: FeedEmptyProps) {
  const msg = MESSAGES[tab];

  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
      {/* 레이더 아이콘 48x48, dark-600 */}
      <svg
        width="48"
        height="48"
        viewBox="0 0 48 48"
        fill="none"
        aria-hidden="true"
        className="text-dark-600 mb-4"
      >
        <circle cx="24" cy="24" r="21" stroke="currentColor" strokeWidth="2" />
        <circle cx="24" cy="24" r="13" stroke="currentColor" strokeWidth="2" />
        <circle cx="24" cy="24" r="5" fill="currentColor" />
        <line x1="24" y1="24" x2="40" y2="10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      </svg>
      <p className="text-sm text-sr-gray-500 mb-1">{msg.title}</p>
      <p className="text-sm text-sr-gray-500">{msg.subtitle}</p>
    </div>
  );
}
