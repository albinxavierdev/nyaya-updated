'use client';

import React, { createContext, useContext, useEffect } from 'react';
import { useQueryLimit } from '@/hooks/useQueryLimit';
import { useAuth } from './authProvider';

interface QueryLimitContextType {
    queryCount: number;
    remainingQueries: number;
    hasExceededLimit: boolean;
    incrementCount: () => void;
    resetCount: () => void;
    canMakeQuery: boolean;
    isGuestUser: boolean;
}

const QueryLimitContext = createContext<QueryLimitContextType | undefined>(undefined);

export function QueryLimitProvider({ children }: { children: React.ReactNode }) {
    const { isAuthenticated } = useAuth();
    const queryLimit = useQueryLimit();

    // Reset query count when user authenticates
    useEffect(() => {
        if (isAuthenticated) {
            queryLimit.resetCount();
        }
    }, [isAuthenticated]);

    const isGuestUser = !isAuthenticated;

    return (
        <QueryLimitContext.Provider
            value={{
                ...queryLimit,
                isGuestUser,
            }}
        >
            {children}
        </QueryLimitContext.Provider>
    );
}

export function useQueryLimitContext() {
    const context = useContext(QueryLimitContext);
    if (context === undefined) {
        throw new Error('useQueryLimitContext must be used within a QueryLimitProvider');
    }
    return context;
}
