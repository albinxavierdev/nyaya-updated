'use client';

import * as React from 'react';
import { Button } from '@/components/ui/button';
import { Sun } from 'lucide-react';

export function ThemeToggle() {
  return (
    <Button
      variant="ghost"
      size="icon"
      disabled
    >
      <Sun className="h-5 w-5" />
      <span className="sr-only">Light theme only</span>
    </Button>
  );
}
