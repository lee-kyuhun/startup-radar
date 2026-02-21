import type { Metadata } from 'next';
import './globals.css';
import { Providers } from './providers';
import { GlobalHeader } from '@/components/layout/GlobalHeader';

export const metadata: Metadata = {
  title: 'Startup Radar',
  description: '한국 VC/스타트업 생태계 종사자를 위한 인물·기관 중심 정보 허브',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko" suppressHydrationWarning>
      <body className="bg-dark-900 text-sr-gray-100 font-pretendard antialiased">
        <script
          dangerouslySetInnerHTML={{
            __html: `try{var t=localStorage.getItem('sr-theme')||'dark';document.documentElement.dataset.theme=t;}catch(e){}`,
          }}
        />
        <Providers>
          <GlobalHeader />
          <main className="min-h-screen pt-14">
            {children}
          </main>
        </Providers>
      </body>
    </html>
  );
}
