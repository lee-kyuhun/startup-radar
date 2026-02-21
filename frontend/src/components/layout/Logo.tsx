import Link from 'next/link';

// UI Spec 3-1: 레이더 아이콘 + "Startup Radar" 텍스트, / 링크
export function Logo() {
  return (
    <Link
      href="/"
      className="flex items-center gap-2 text-white hover:opacity-90 transition-opacity"
    >
      {/* 레이더 아이콘 (SVG, 20x20, accent-blue) */}
      <svg
        width="20"
        height="20"
        viewBox="0 0 20 20"
        fill="none"
        aria-hidden="true"
        className="text-accent-blue flex-shrink-0"
      >
        <circle cx="10" cy="10" r="9" stroke="currentColor" strokeWidth="1.5" />
        <circle cx="10" cy="10" r="5.5" stroke="currentColor" strokeWidth="1.5" />
        <circle cx="10" cy="10" r="2" fill="currentColor" />
        {/* 레이더 스위프 라인 */}
        <line x1="10" y1="10" x2="17" y2="4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      </svg>
      <span className="text-xl font-bold leading-none">Startup Radar</span>
    </Link>
  );
}
