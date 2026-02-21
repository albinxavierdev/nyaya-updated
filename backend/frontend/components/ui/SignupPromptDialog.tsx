'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Sparkles, CheckCircle2 } from 'lucide-react';

interface SignupPromptDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    queryCount: number;
}

export function SignupPromptDialog({ open, onOpenChange, queryCount }: SignupPromptDialogProps) {
    const router = useRouter();

    const handleSignup = () => {
        router.push('/signup');
    };

    const handleSignin = () => {
        router.push('/signin');
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[500px]">
                <DialogHeader>
                    <div className="flex items-center justify-center mb-4">
                        <div className="rounded-full bg-primary/10 p-3">
                            <Sparkles className="h-8 w-8 text-primary" />
                        </div>
                    </div>
                    <DialogTitle className="text-center text-2xl">
                        You've Used All Your Free Queries!
                    </DialogTitle>
                    <DialogDescription className="text-center text-base pt-2">
                        You've made <Badge variant="secondary" className="mx-1">{queryCount} queries</Badge>
                        and explored Nyayantar AI. Create a free account to continue getting legal guidance powered by AI.
                    </DialogDescription>
                </DialogHeader>

                <div className="py-4 space-y-3">
                    <div className="flex items-start gap-3">
                        <CheckCircle2 className="h-5 w-5 text-primary mt-0.5 flex-shrink-0" />
                        <div>
                            <p className="font-medium">Unlimited Queries</p>
                            <p className="text-sm text-muted-foreground">Ask as many legal questions as you need</p>
                        </div>
                    </div>
                    <div className="flex items-start gap-3">
                        <CheckCircle2 className="h-5 w-5 text-primary mt-0.5 flex-shrink-0" />
                        <div>
                            <p className="font-medium">Conversation History</p>
                            <p className="text-sm text-muted-foreground">Access your past conversations anytime</p>
                        </div>
                    </div>
                    <div className="flex items-start gap-3">
                        <CheckCircle2 className="h-5 w-5 text-primary mt-0.5 flex-shrink-0" />
                        <div>
                            <p className="font-medium">Advanced Features</p>
                            <p className="text-sm text-muted-foreground">Document analysis and personalized insights</p>
                        </div>
                    </div>
                </div>

                <DialogFooter className="flex-col sm:flex-col gap-2">
                    <Button onClick={handleSignup} className="w-full" size="lg">
                        Create Free Account
                    </Button>
                    <Button onClick={handleSignin} variant="outline" className="w-full" size="lg">
                        Sign In to Existing Account
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
