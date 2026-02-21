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
        // CSS 변수 참조 — rgb(r g b / alpha) 형태로 opacity 지원
        'dark-900': 'rgb(var(--color-dark-900) / <alpha-value>)',
        'dark-800': 'rgb(var(--color-dark-800) / <alpha-value>)',
        'dark-700': 'rgb(var(--color-dark-700) / <alpha-value>)',
        'dark-600': 'rgb(var(--color-dark-600) / <alpha-value>)',
        'dark-500': 'rgb(var(--color-dark-500) / <alpha-value>)',
        'sr-gray-100': 'rgb(var(--color-sr-gray-100) / <alpha-value>)',
        'sr-gray-300': 'rgb(var(--color-sr-gray-300) / <alpha-value>)',
        'sr-gray-500': 'rgb(var(--color-sr-gray-500) / <alpha-value>)',
        'accent-blue':   'rgb(var(--color-accent-blue) / <alpha-value>)',
        'accent-blue-h': 'rgb(var(--color-accent-blue-h) / <alpha-value>)',
        'accent-green':  'rgb(var(--color-accent-green) / <alpha-value>)',
        'accent-amber':  'rgb(var(--color-accent-amber) / <alpha-value>)',
        'accent-red':    'rgb(var(--color-accent-red) / <alpha-value>)',
        'tag-news-bg':   'rgb(var(--color-tag-news-bg) / <alpha-value>)',
        'tag-news-text': 'rgb(var(--color-tag-news-text) / <alpha-value>)',
        'tag-vc-bg':     'rgb(var(--color-tag-vc-bg) / <alpha-value>)',
        'tag-vc-text':   'rgb(var(--color-tag-vc-text) / <alpha-value>)',
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
