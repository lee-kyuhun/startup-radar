// UI Spec 3-2-D: shimmer 로딩 스켈레톤 (5개)
// shimmer 애니메이션은 globals.css의 .shimmer 클래스 사용

function SkeletonCard() {
  return (
    <div className="bg-dark-800 border border-dark-600 rounded-md p-4 mb-3">
      {/* 행 1: SourceTag + 출처명 + 날짜 */}
      <div className="flex items-center gap-2 mb-3">
        <div className="shimmer h-5 w-12 rounded-sm" />
        <div className="shimmer h-4 w-20 rounded-sm" />
        <div className="shimmer h-4 w-10 rounded-sm ml-auto" />
        <div className="shimmer h-4 w-4 rounded-sm" />
      </div>
      {/* 행 2: 제목 (2줄) */}
      <div className="shimmer h-4 w-4/5 rounded-sm mb-2" />
      <div className="shimmer h-4 w-3/5 rounded-sm mb-3" />
      {/* 행 3: 요약 (3줄) */}
      <div className="shimmer h-3.5 w-full rounded-sm mb-1.5" />
      <div className="shimmer h-3.5 w-full rounded-sm mb-1.5" />
      <div className="shimmer h-3.5 w-2/3 rounded-sm" />
    </div>
  );
}

export function FeedSkeleton() {
  return (
    <div aria-label="로딩 중" aria-busy="true">
      {Array.from({ length: 5 }).map((_, i) => (
        <SkeletonCard key={i} />
      ))}
    </div>
  );
}
