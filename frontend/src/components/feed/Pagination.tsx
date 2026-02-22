'use client';

import { useMemo } from 'react';

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  isLoading?: boolean;
  onPageChange: (page: number) => void;
}

// UI Spec 3-2-G: Pagination 컴포넌트 (D-7)
// Desktop: 최대 10슬롯, Mobile: 최대 7슬롯
// Truncation 규칙: 10페이지 초과 시 말줄임(...), 앞 2개/뒤 2개 항상 고정
export function Pagination({
  currentPage,
  totalPages,
  isLoading = false,
  onPageChange,
}: PaginationProps) {
  // 1페이지 이하면 Pagination 숨김
  if (totalPages <= 1) return null;

  return (
    <nav
      aria-label="페이지 탐색"
      className={`flex items-center justify-center gap-1 pt-6 pb-4 ${
        isLoading ? 'opacity-50 pointer-events-none' : ''
      }`}
    >
      {/* 이전 버튼 */}
      <PrevButton
        disabled={!currentPage || currentPage <= 1}
        onClick={() => onPageChange(currentPage - 1)}
      />

      {/* 페이지 번호 - Desktop */}
      <DesktopPageNumbers
        currentPage={currentPage}
        totalPages={totalPages}
        onPageChange={onPageChange}
      />

      {/* 페이지 번호 - Mobile */}
      <MobilePageNumbers
        currentPage={currentPage}
        totalPages={totalPages}
        onPageChange={onPageChange}
      />

      {/* 다음 버튼 */}
      <NextButton
        disabled={currentPage >= totalPages}
        onClick={() => onPageChange(currentPage + 1)}
      />
    </nav>
  );
}

// --- 이전 버튼 ---
function PrevButton({
  disabled,
  onClick,
}: {
  disabled: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      aria-label="이전 페이지"
      className={`
        flex items-center justify-center w-9 h-9 rounded-md
        transition-colors duration-150
        ${
          disabled
            ? 'text-dark-500 cursor-not-allowed'
            : 'text-sr-gray-300 hover:bg-dark-700 hover:text-white active:bg-dark-600'
        }
      `}
    >
      <svg
        width="16"
        height="16"
        viewBox="0 0 16 16"
        fill="none"
        aria-hidden="true"
      >
        <path
          d="M10 12L6 8L10 4"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    </button>
  );
}

// --- 다음 버튼 ---
function NextButton({
  disabled,
  onClick,
}: {
  disabled: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      aria-label="다음 페이지"
      className={`
        flex items-center justify-center w-9 h-9 rounded-md
        transition-colors duration-150
        ${
          disabled
            ? 'text-dark-500 cursor-not-allowed'
            : 'text-sr-gray-300 hover:bg-dark-700 hover:text-white active:bg-dark-600'
        }
      `}
    >
      <svg
        width="16"
        height="16"
        viewBox="0 0 16 16"
        fill="none"
        aria-hidden="true"
      >
        <path
          d="M6 4L10 8L6 12"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    </button>
  );
}

// --- Desktop 페이지 번호 (최대 10슬롯) ---
function DesktopPageNumbers({
  currentPage,
  totalPages,
  onPageChange,
}: {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}) {
  const slots = useMemo(
    () => buildPageSlots(currentPage, totalPages, 10, 2),
    [currentPage, totalPages],
  );

  return (
    <div className="hidden sm:flex items-center gap-1">
      {slots.map((slot, i) =>
        slot.type === 'ellipsis' ? (
          <Ellipsis key={`e-${i}`} />
        ) : (
          <PageButton
            key={slot.page}
            page={slot.page!}
            isActive={slot.page === currentPage}
            onClick={() => onPageChange(slot.page!)}
          />
        ),
      )}
    </div>
  );
}

// --- Mobile 페이지 번호 (최대 7슬롯) ---
function MobilePageNumbers({
  currentPage,
  totalPages,
  onPageChange,
}: {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}) {
  const slots = useMemo(
    () => buildPageSlots(currentPage, totalPages, 7, 1),
    [currentPage, totalPages],
  );

  return (
    <div className="flex sm:hidden items-center gap-0.5">
      {slots.map((slot, i) =>
        slot.type === 'ellipsis' ? (
          <Ellipsis key={`me-${i}`} size="sm" />
        ) : (
          <PageButton
            key={slot.page}
            page={slot.page!}
            isActive={slot.page === currentPage}
            onClick={() => onPageChange(slot.page!)}
            size="sm"
          />
        ),
      )}
    </div>
  );
}

// --- 페이지 번호 버튼 ---
function PageButton({
  page,
  isActive,
  onClick,
  size = 'md',
}: {
  page: number;
  isActive: boolean;
  onClick: () => void;
  size?: 'sm' | 'md';
}) {
  const sizeClass = size === 'sm' ? 'min-w-8 h-8 text-xs' : 'min-w-9 h-9 text-sm';

  if (isActive) {
    return (
      <span
        aria-current="page"
        className={`
          flex items-center justify-center rounded-md px-2
          bg-accent-blue text-white font-medium cursor-default
          ${sizeClass}
        `}
      >
        {page}
      </span>
    );
  }

  return (
    <button
      onClick={onClick}
      aria-label={`${page} 페이지로 이동`}
      className={`
        flex items-center justify-center rounded-md px-2
        text-sr-gray-500 font-medium
        hover:bg-dark-700 hover:text-sr-gray-100
        transition-colors duration-150
        ${sizeClass}
      `}
    >
      {page}
    </button>
  );
}

// --- 말줄임 (...) ---
function Ellipsis({ size = 'md' }: { size?: 'sm' | 'md' }) {
  const sizeClass = size === 'sm' ? 'w-8 h-8 text-xs' : 'w-9 h-9 text-sm';
  return (
    <span
      className={`flex items-center justify-center text-dark-500 cursor-default ${sizeClass}`}
      aria-hidden="true"
      tabIndex={-1}
    >
      ...
    </span>
  );
}

// --- Truncation 알고리즘 ---
// UI Spec 페이지 번호 표시 규칙:
// maxSlots: desktop=10, mobile=7
// fixedEdge: desktop=2 (앞뒤 고정 개수), mobile=1

type PageSlot = { type: 'page'; page: number } | { type: 'ellipsis' };

function buildPageSlots(
  current: number,
  total: number,
  maxSlots: number,
  fixedEdge: number,
): PageSlot[] {
  // 전체 페이지가 maxSlots 이하면 전부 표시
  if (total <= maxSlots) {
    return Array.from({ length: total }, (_, i) => ({
      type: 'page' as const,
      page: i + 1,
    }));
  }

  const slots: PageSlot[] = [];

  // 앞쪽 고정 페이지
  const startFixed: number[] = [];
  for (let i = 1; i <= fixedEdge; i++) startFixed.push(i);

  // 뒤쪽 고정 페이지
  const endFixed: number[] = [];
  for (let i = total - fixedEdge + 1; i <= total; i++) endFixed.push(i);

  // 중간 윈도우에 사용 가능한 슬롯 수 계산
  // fixedEdge(앞) + fixedEdge(뒤) + 최대 2개 말줄임 = fixedEdge*2 + 2
  // 중간 가용 = maxSlots - fixedEdge*2 - (말줄임 수)
  // 말줄임 수는 상황에 따라 0, 1, 2개

  // "앞쪽 가까이" 판단: 중간 윈도우가 앞 고정과 붙을 수 있는가?
  // 앞 고정의 마지막: fixedEdge
  // 필요 중간 슬롯: maxSlots - fixedEdge*2 - 1(뒤 말줄임) = 가용
  const middleSlotsWithOneEllipsis = maxSlots - fixedEdge * 2 - 1;

  // 케이스 1: 현재 페이지가 앞쪽 가까이 (앞 고정과 중간이 연결됨)
  // 앞에서 연속으로 보여줄 수 있는 최대 범위 = fixedEdge + middleSlotsWithOneEllipsis
  const nearStartThreshold = fixedEdge + middleSlotsWithOneEllipsis;
  if (current <= nearStartThreshold) {
    // 앞부터 연속 표시, 뒤에만 ... + endFixed
    const showCount = maxSlots - fixedEdge - 1; // 앞에서 보여줄 개수 (뒤 고정 + 말줄임 제외)
    for (let i = 1; i <= showCount; i++) {
      slots.push({ type: 'page', page: i });
    }
    // 연속되는지 확인
    if (showCount + 1 < endFixed[0]) {
      slots.push({ type: 'ellipsis' });
    }
    for (const p of endFixed) {
      if (!slots.some((s) => s.type === 'page' && s.page === p)) {
        slots.push({ type: 'page', page: p });
      }
    }
    return slots;
  }

  // 케이스 2: 현재 페이지가 뒤쪽 가까이 (뒤 고정과 중간이 연결됨)
  const nearEndThreshold = total - fixedEdge - middleSlotsWithOneEllipsis + 1;
  if (current >= nearEndThreshold) {
    const showCount = maxSlots - fixedEdge - 1; // 뒤에서 보여줄 개수
    for (const p of startFixed) {
      slots.push({ type: 'page', page: p });
    }
    const firstBackPage = total - showCount + 1;
    if (startFixed[startFixed.length - 1] + 1 < firstBackPage) {
      slots.push({ type: 'ellipsis' });
    }
    for (let i = firstBackPage; i <= total; i++) {
      if (!slots.some((s) => s.type === 'page' && s.page === i)) {
        slots.push({ type: 'page', page: i });
      }
    }
    return slots;
  }

  // 케이스 3: 중간 (양쪽 말줄임)
  // 중간에 사용 가능한 슬롯: maxSlots - fixedEdge*2 - 2(양쪽 말줄임)
  const middleSlots = maxSlots - fixedEdge * 2 - 2;
  const halfMiddle = Math.floor(middleSlots / 2);
  const middleStart = current - halfMiddle;
  const middleEnd = middleStart + middleSlots - 1;

  for (const p of startFixed) {
    slots.push({ type: 'page', page: p });
  }
  slots.push({ type: 'ellipsis' });
  for (let i = middleStart; i <= middleEnd; i++) {
    slots.push({ type: 'page', page: i });
  }
  slots.push({ type: 'ellipsis' });
  for (const p of endFixed) {
    slots.push({ type: 'page', page: p });
  }

  return slots;
}
