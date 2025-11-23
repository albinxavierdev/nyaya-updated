'use client';

import Link from 'next/link';
import { siteConfig } from '@/config/site';
import { cn } from '@/lib/utils';
import { buttonVariants } from '@/components/ui/button';
import { HoverEffect } from '@/components/ui/card-hover-effect';
import { Features } from '@/config/features';
import NumberTicker from '@/components/magicui/number-ticker';
// import { Github, StarIcon } from 'lucide-react';
// import useGitHubStars from '@/hooks/useGitHubStars';
import { ScrollArea } from '@/components/ui/scroll-area';
import Loading from '@/components/loading';
import { Suspense } from 'react';

// eslint-disable-next-line @next/next/no-async-client-component
const IndexPageContent = () => {
  // GitHub stars feature removed
  return (
    <>
      <ScrollArea className="w-full h-full">
        <section className="space-y-6 pb-8 pt-6 md:pb-12 md:pt-10 lg:py-32 min-h-screen md:h-fit flex flex-col justify-center">
          <div className="container flex max-w-[64rem] flex-col items-center gap-4 text-center">
            <h1 className="font-heading text-3xl sm:text-5xl md:text-6xl lg:text-7xl">
              Nyayantar AI Features
            </h1>
            <p className="max-w-[42rem] leading-normal text-muted-foreground sm:text-lg sm:leading-7">
              Your Legal Guide, Powered by AI - helping you with legal questions and tasks.
              Built with modern technology to provide accurate and helpful legal responses.
            </p>
            <div className="space-x-4 flex">
              <Link
                href="/signin"
                className={cn(
                  buttonVariants(),
                  'w-fit gap-2 overflow-hidden whitespace-pre md:flex',
                  'group relative w-fit justify-center gap-2 rounded-md transition-all duration-300 ease-out hover:ring-2 hover:ring-primary hover:ring-offset-2'
                )}
              >
                Get Started
              </Link>
            </div>
          </div>
        </section>
        <section
          id="features"
          className="container space-y-6 bg-slate-50 py-8 dark:bg-transparent md:py-12 lg:py-24"
        >
          <div className="mx-auto flex max-w-[58rem] flex-col items-center space-y-4 text-center">
            <h2 className="font-heading text-3xl leading-[1.1] sm:text-3xl md:text-6xl">
              Features
            </h2>
          </div>
          <HoverEffect items={Features} />
        </section>
        <section id="open-source" className="container py-8 md:py-12 lg:py-24 ">
          <div className="container mx-auto px-4 py-8 flex flex-col justify-center items-center">
            <h2 className="text-3xl font-bold mb-4">Powered by Modern Technology</h2>
            <p className="max-w-[85%] leading-normal text-muted-foreground sm:text-lg sm:leading-7 mb-4">
              Built with modern, open-source technologies for reliability and performance.
            </p>
            <ul className="list-none space-y-2 mb-4">
              <li>
                <span className="mr-2">🤖</span>
                <strong>AI Technology:</strong> Advanced artificial intelligence for intelligent responses
              </li>
              <li>
                <span className="mr-2">📦</span>
                <strong>MongoDB:</strong> Used as both a normal database and a
                vector database
              </li>
              <li>
                <span className="mr-2">⚡</span>
                <strong>FastAPI:</strong> Backend API framework
              </li>
              <li>
                <span className="mr-2">⚛️</span>
                <strong>Next.js:</strong> Frontend framework
              </li>
            </ul>
            <p className="text-muted-foreground sm:text-lg sm:leading-7">
              Built with modern AI technology for the best user experience.
            </p>
          </div>
        </section>
      </ScrollArea>
    </>
  );
};

export default function IndexPage() {
  return (
    <Suspense fallback={<Loading />}>
      <IndexPageContent />
    </Suspense>
  );
}
