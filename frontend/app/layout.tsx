import type { Metadata } from 'next';
// import { Inter } from 'next/font/google';
import { Roboto } from 'next/font/google';
import { AuthProvider } from '@/app/authProvider';
import { ConversationProvider } from '@/app/ConversationContext';
import { QueryLimitProvider } from '@/app/QueryLimitContext';
import { Analytics } from '@/components/analytics';
import { siteConfig } from '@/config/site';
import { ThemeProvider } from '@/components/theme-provider';
import { Toaster } from '@/components/ui/sonner';
import './globals.css';
import { Header } from '@/components/header';
import Sidebar from '@/components/sidebar';
import ClientOnly from '@/components/client-only';

const roboto = Roboto({
  weight: ['400', '700'],
  subsets: ['latin'],
  display: 'swap',
});

export const metadata: Metadata = {
  metadataBase: new URL(`${siteConfig.url}`),
  title: {
    default: siteConfig.name,
    template: `%s | ${siteConfig.name}`,
  },
  description: siteConfig.description,
  keywords: ['AI', 'Legal', 'Agent', 'Nyayantar AI', 'Legal AI', 'India Legal AI'],
  authors: [
    {
      name: 'Nyayantar AI',
      url: 'http://localhost:3000',
    },
  ],
  creator: 'Nyayantar AI',
  icons: {
    icon: [
      { url: '/favicon.ico', sizes: 'any' },
      { url: '/favicon-16x16.png', sizes: '16x16', type: 'image/png' },
      { url: '/favicon-32x32.png', sizes: '32x32', type: 'image/png' },
      { url: '/favicon-48x48.png', sizes: '48x48', type: 'image/png' },
    ],
    apple: [
      { url: '/apple-touch-icon.png', sizes: '180x180', type: 'image/png' },
    ],
    other: [
      { rel: 'icon', url: '/favicon.ico' },
    ],
  },
};

export const viewport = {
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: 'white' },
    { media: '(prefers-color-scheme: dark)', color: 'black' },
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <Analytics />
      </head>
      <body className={`${roboto.className} flex flex-col h-screen`} suppressHydrationWarning>
        <ClientOnly>
          <ThemeProvider
            attribute="class"
            defaultTheme="light"
            enableSystem
            disableTransitionOnChange
          >
            <AuthProvider>
              <QueryLimitProvider>
                <ConversationProvider>
                  <Toaster position="top-right" />
                  <Header />
                  <div className="flex flex-1 overflow-y-hidden">
                    <Sidebar />
                    <main className="w-full h-full overflow-y-hidden">
                      {children}
                    </main>
                  </div>
                </ConversationProvider>
              </QueryLimitProvider>
            </AuthProvider>
          </ThemeProvider>
        </ClientOnly>
      </body>
    </html>
  );
}
