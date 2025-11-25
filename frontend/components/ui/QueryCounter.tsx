'use client';

import React from 'react';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Info } from 'lucide-react';

interface QueryCounterProps {
    remainingQueries: number;
    totalQueries?: number;
}

export function QueryCounter({ remainingQueries, totalQueries = 20 }: QueryCounterProps) {
    const usedQueries = totalQueries - remainingQueries;
    const progressPercentage = (usedQueries / totalQueries) * 100;

    // Determine color based on remaining queries
    const getVariant = () => {
        if (remainingQueries > 10) return 'secondary';
        if (remainingQueries > 5) return 'default';
        return 'destructive';
    };

    return (
        <div className="flex items-center gap-3 px-4 py-2 bg-muted/50 rounded-lg border">
            <Info className="h-4 w-4 text-muted-foreground flex-shrink-0" />
            <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2 mb-1">
                    <span className="text-sm font-medium">Free Trial</span>
                    <Badge variant={getVariant()} className="text-xs">
                        {remainingQueries} {remainingQueries === 1 ? 'query' : 'queries'} left
                    </Badge>
                </div>
                <Progress value={progressPercentage} className="h-1.5" />
            </div>
        </div>
    );
}
