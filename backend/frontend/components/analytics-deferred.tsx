'use client';

import { useEffect, useState } from 'react';

/**
 * Loads Analytics after mount so the layout chunk never blocks on the analytics chunk.
 * Avoids ChunkLoadError (timeout) when @vercel/analytics or its chunk is slow.
 */
export function AnalyticsDeferred() {
  const [Analytics, setAnalytics] = useState<React.ComponentType | null>(null);

  useEffect(() => {
    import('@/components/analytics-dynamic')
      .then((m) => setAnalytics(() => m.AnalyticsDynamic))
      .catch(() => {});
  }, []);

  if (!Analytics) return null;
  return <Analytics />;
}
