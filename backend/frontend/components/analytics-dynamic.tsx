'use client';

import dynamic from 'next/dynamic';

const Analytics = dynamic(
  () =>
    import('@/components/analytics')
      .then((m) => m.Analytics)
      .catch(() => () => null),
  { ssr: false }
);

export function AnalyticsDynamic() {
  return <Analytics />;
}
