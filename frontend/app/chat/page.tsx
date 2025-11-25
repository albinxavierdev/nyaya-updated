'use client';

import { useCallback, useEffect, useState } from 'react';
import { useChat } from 'ai/react';
import { ChatInput, ChatMessages } from '@/components/ui/chat';
import { useClientConfig } from '@/components/ui/chat/hooks/use-config';
import { useRouter, useSearchParams } from 'next/navigation';
import { Suspense } from 'react';
import { useConversationContext } from '@/app/ConversationContext';
import { useAuth } from '@/app/authProvider';
import { useQueryLimitContext } from '@/app/QueryLimitContext';
import Loading from '@/components/loading';
import { toast } from 'sonner';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { FileText, Download, CheckCircle, Clock, AlertCircle } from 'lucide-react';
import { SignupPromptDialog } from '@/components/ui/SignupPromptDialog';
import { QueryCounter } from '@/components/ui/QueryCounter';

function ChatContent() {
  const { accessToken, axiosInstance, isAuthenticated } = useAuth();
  const queryLimitContext = useQueryLimitContext();
  const { backend, starterQuestions } = useClientConfig();
  const router = useRouter();
  const searchParams = useSearchParams();
  const [conversationId, setConversationId] = useState<string | null>(null);
  const { conversationList, setConversationList } = useConversationContext();
  const [isClient, setIsClient] = useState(false);
  const [showSignupDialog, setShowSignupDialog] = useState(false);


  useEffect(() => {
    setIsClient(true);
  }, []);


  const fetchMessages = useCallback(async () => {
    if (!conversationId) return;
    try {
      const response = await axiosInstance.get(
        `/api/conversation/${conversationId}`
      );
      setMessages(response.data.messages || []);
    } catch (error: any) {
      if (error.response && error.response.status === 401) {
        return;
      }
      toast(`Failed to fetch conversation: ${error.message}`);
    }
  }, [conversationId]);

  const fetchConversations = useCallback(async () => {
    // Skip fetching conversations for guest users
    if (!isAuthenticated) {
      return;
    }

    try {
      const response = await axiosInstance.get('/api/conversation/list');
      setConversationList(response.data.conversations);
    } catch (error: any) {
      console.error('Error fetching conversations:', error.message);
    }
  }, [isAuthenticated, axiosInstance]);

  const handleNewChat = useCallback(async () => {
    // Skip conversation creation for guest users
    if (!isAuthenticated) {
      setConversationId('guest');
      return;
    }

    try {
      const response = await axiosInstance.get('/api/conversation');
      const newConversationId = response.data.conversation_id;
      router.push(`/chat?conversation_id=${newConversationId}`);
    } catch (error: any) {
      console.error('Error creating new conversation:', error.message);
    }
  }, [router, isAuthenticated, axiosInstance]);

  const {
    messages,
    input,
    isLoading,
    handleSubmit,
    handleInputChange,
    reload,
    stop,
    append,
    setInput,
    setMessages,
  } = useChat({
    api: isAuthenticated
      ? conversationId
        ? `${backend}/api/chat?conversation_id=${conversationId}`
        : ''
      : `${backend}/api/chat/guest`,  // Always use guest endpoint for unauthenticated users
    headers: {
      'Content-Type': 'application/json',
      ...(isAuthenticated && { Authorization: `Bearer ${accessToken}` }),
    },
    body: isAuthenticated ? { conversation_id: conversationId } : {},
    streamProtocol: 'text',  // Enable Vercel AI SDK text streaming protocol
    onFinish: (message) => {
      // Increment query count for guest users after successful message
      if (!isAuthenticated) {
        queryLimitContext.incrementCount();
      }
    },
    onError: (error: unknown) => {
      if (!(error instanceof Error)) throw error;
      let errorMessage = 'An unexpected error occurred.';

      try {
        const errorResponse = JSON.parse(error.message);

        if (errorResponse.detail === 'Not authenticated') {
          alert('Session has expired. Please login again.');
          router.push('/signin');
          return;
        }

        if (errorResponse.detail) {
          errorMessage = `Error: ${errorResponse.detail}`;
        } else if (errorResponse.errors) {
          errorMessage = `Validation Errors: ${errorResponse.errors.join(
            ', '
          )}`;
        } else if (errorResponse.message) {
          errorMessage = `Message: ${errorResponse.message}`;
        } else if (errorResponse.error) {
          errorMessage = `Error: ${errorResponse.error}`;
        } else {
          errorMessage = `Unknown error format: ${error.message}`;
        }
      } catch (parseError) {
        errorMessage = `Error parsing response: ${error.message}`;
      }

      toast(errorMessage);
    },
  });

  // Custom submit handler to check query limits for guest users
  const handleChatSubmit = useCallback((e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    // Check query limit for guest users
    if (!isAuthenticated && !queryLimitContext.canMakeQuery) {
      setShowSignupDialog(true);
      return;
    }

    // Proceed with normal submission
    handleSubmit(e);
  }, [isAuthenticated, queryLimitContext.canMakeQuery, handleSubmit]);

  const updateMessageContent = useCallback((
    id: string,
    oldContent: string,
    newContent: string
  ) => {
    const messageIndex = messages.findIndex(
      (m) => m.role === 'user' && m.content === oldContent
    );
    if (messageIndex !== -1) {
      const updatedMessages = [...messages.slice(0, messageIndex)];
      setMessages(updatedMessages);

      append!({
        role: 'user',
        content: newContent,
      });
    }
  }, [messages, append, setMessages]);


  useEffect(() => {
    if (isClient) {
      fetchConversations();
    }
  }, [isClient, isLoading, fetchConversations]);

  useEffect(() => {
    if (isClient && conversationId) {
      fetchMessages();
    }
  }, [isClient, conversationId, fetchMessages]);

  useEffect(() => {
    if (isClient) {
      const urlConversationId = searchParams.get('conversation_id');
      const query = searchParams.get('query');

      setConversationId(urlConversationId);
      if (query) {
        setInput(query);
      }

      if (!urlConversationId) {
        const timer = setTimeout(() => {
          handleNewChat();
        }, 1000);

        return () => clearTimeout(timer);
      }
    }
  }, [isClient, searchParams, setInput, handleNewChat]);

  if (!isClient) {
    return <Loading />;
  }

  return (
    <div className="w-full h-full flex justify-center items-center bg-primary-foreground">
      <div className="space-y-2 w-full  md:w-[90%] lg:w-[70%] h-full flex flex-col p-4">
        {/* Query Counter for Guest Users */}
        {!isAuthenticated && (
          <QueryCounter
            remainingQueries={queryLimitContext.remainingQueries}
          />
        )}

        <Suspense fallback={<Loading />}>
          <ChatMessages
            messages={messages}
            isLoading={isLoading}
            reload={reload}
            stop={stop}
            append={append}
            updateMessageContent={updateMessageContent}
            starterQuestions={starterQuestions}
          />
        </Suspense>
        <Suspense fallback={<Loading />}>
          <ChatInput
            input={input}
            handleSubmit={handleChatSubmit}
            handleInputChange={handleInputChange}
            isLoading={isLoading}
            messages={messages}
            append={append}
            setInput={setInput}
          />
        </Suspense>

        {/* Signup Prompt Dialog */}
        <SignupPromptDialog
          open={showSignupDialog}
          onOpenChange={setShowSignupDialog}
          queryCount={queryLimitContext.queryCount}
        />
      </div>
    </div>
  );
}

export default function Chat() {
  return (
    <Suspense fallback={<Loading />}>
      <ChatContent />
    </Suspense>
  );
}
