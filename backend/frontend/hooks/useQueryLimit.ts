import { useState, useEffect, useCallback } from 'react';

const QUERY_LIMIT = 20;
const STORAGE_KEY = 'nyayantar_query_count';

interface QueryLimitState {
    queryCount: number;
    remainingQueries: number;
    hasExceededLimit: boolean;
    incrementCount: () => void;
    resetCount: () => void;
    canMakeQuery: boolean;
}

export function useQueryLimit(): QueryLimitState {
    const [queryCount, setQueryCount] = useState<number>(0);

    // Initialize count from localStorage on mount
    useEffect(() => {
        try {
            const stored = localStorage.getItem(STORAGE_KEY);
            if (stored) {
                const count = parseInt(stored, 10);
                if (!isNaN(count) && count >= 0) {
                    setQueryCount(count);
                }
            }
        } catch (error) {
            console.error('Failed to read query count from localStorage:', error);
        }
    }, []);

    // Persist count to localStorage whenever it changes
    useEffect(() => {
        try {
            localStorage.setItem(STORAGE_KEY, queryCount.toString());
        } catch (error) {
            console.error('Failed to save query count to localStorage:', error);
        }
    }, [queryCount]);

    const incrementCount = useCallback(() => {
        setQueryCount((prev) => prev + 1);
    }, []);

    const resetCount = useCallback(() => {
        setQueryCount(0);
        try {
            localStorage.removeItem(STORAGE_KEY);
        } catch (error) {
            console.error('Failed to clear query count from localStorage:', error);
        }
    }, []);

    const remainingQueries = Math.max(0, QUERY_LIMIT - queryCount);
    const hasExceededLimit = queryCount >= QUERY_LIMIT;
    const canMakeQuery = queryCount < QUERY_LIMIT;

    return {
        queryCount,
        remainingQueries,
        hasExceededLimit,
        incrementCount,
        resetCount,
        canMakeQuery,
    };
}
