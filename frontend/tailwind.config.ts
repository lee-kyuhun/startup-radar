import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Foundation palette (UI Spec 1-2)
        'dark-900': '#111118',   // 메인 배경
        'dark-800': '#1A1A24',   // 카드 배경
        'dark-700': '#22222F',   // hover 상태 배경
        'dark-600': '#2E2E3E',   // 보더, 구분선
        'dark-500': '#3E3E52',   // 비활성 아이콘
        'sr-gray-100': '#E8E8F0', // 제목 텍스트
        'sr-gray-300': '#A0A0B8', // 본문/설명 텍스트
        'sr-gray-500': '#60607A', // 메타 정보 (날짜 등)

        // Accent palette
        'accent-blue':   '#4B6EF5',
        'accent-blue-h': '#6B8EFF',
        'accent-green':  '#22C55E',
        'accent-amber':  '#F59E0B',
        'accent-red':    '#EF4444',

        // Source tag colors
        'tag-news-bg':   '#1E3A2F',
        'tag-news-text': '#22C55E',
        'tag-vc-bg':     '#1A2A4A',
        'tag-vc-text':   '#4B6EF5',
      },
      fontFamily: {
        pretendard: [
          'var(--font-pretendard)',
          'system-ui',
          '-apple-system',
          'sans-serif',
        ],
      },
      borderRadius: {
        sm: '4px',
        md: '8px',
        lg: '12px',
      },
      maxWidth: {
        feed: '720px',
      },
      height: {
        header: '56px',
        'header-mobile': '52px',
      },
    },
  },
  plugins: [],
}

export default config
