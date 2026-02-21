'use client';

import { useStatusQuery } from '@/lib/queries';
import { STATUS_COLORS } from '@/lib/constants';
import { formatLastUpdated } from '@/lib/formatDate';

// UI Spec 3-1: 크롤링 상태 배지 — 색상 점 + "N분 전 업데이트"
// 60초 폴링으로 자동 갱신
export function FeedStatusBadge() {
  const { data, isError } = useStatusQuery();

  if (isError || !data) {
    return (
      <div className="flex items-center gap-1.5 text-xs text-sr-gray-500">
        <span className="w-2 h-2 rounded-full bg-accent-red flex-shrink-0" />
        <span className="hidden sm:inline">상태 확인 불가</span>
      </div>
    );
  }

  const colorClass = STATUS_COLORS[data.status];
  const label = formatLastUpdated(data.last_updated_at);

  return (
    <div className="flex items-center gap-1.5 text-xs text-sr-gray-500">
      <span
        className={`w-2 h-2 rounded-full flex-shrink-0 ${colorClass}`}
        style={{ backgroundColor: 'currentColor' }}
      />
      <span className="hidden sm:inline whitespace-nowrap">{label}</span>
    </div>
  );
}
