// published_at (ISO 8601 UTC) → 상대 시간 문자열 변환
// API Contract D-4 결정: 1시간 이내 "N분 전", 1~24시간 "N시간 전", 초과 "MM월 DD일"

export function formatRelativeDate(isoString: string): string {
  const published = new Date(isoString);
  const now = new Date();
  const diffMs = now.getTime() - published.getTime();
  const diffMinutes = Math.floor(diffMs / (1000 * 60));
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));

  if (diffMinutes < 1) {
    return '방금 전';
  }

  if (diffMinutes < 60) {
    return `${diffMinutes}분 전`;
  }

  if (diffHours < 24) {
    return `${diffHours}시간 전`;
  }

  // 24시간 초과: "MM월 DD일"
  const month = published.getMonth() + 1;
  const day = published.getDate();
  return `${month}월 ${day}일`;
}

// FeedStatusBadge용: last_updated_at → "N분 전" (항상 분 단위)
export function formatLastUpdated(isoString: string): string {
  const updated = new Date(isoString);
  const now = new Date();
  const diffMs = now.getTime() - updated.getTime();
  const diffMinutes = Math.floor(diffMs / (1000 * 60));

  if (diffMinutes < 1) return '방금 업데이트';
  if (diffMinutes < 60) return `${diffMinutes}분 전 업데이트`;

  const diffHours = Math.floor(diffMinutes / 60);
  return `${diffHours}시간 전 업데이트`;
}
