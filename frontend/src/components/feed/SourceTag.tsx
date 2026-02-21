import type { SourceType } from '@/types/api';
import { SOURCE_TAG_STYLES } from '@/lib/constants';

interface SourceTagProps {
  sourceType: SourceType;
  sourceName: string;
}

// UI Spec 3-2-C: 출처 배지 (tag-news / tag-vc)
export function SourceTag({ sourceType, sourceName }: SourceTagProps) {
  const style = SOURCE_TAG_STYLES[sourceType];

  return (
    <span
      className={`
        inline-flex items-center
        px-2 py-0.5
        rounded-sm
        text-[11px] font-medium leading-tight
        ${style.bg} ${style.text}
      `}
    >
      {sourceName}
    </span>
  );
}
