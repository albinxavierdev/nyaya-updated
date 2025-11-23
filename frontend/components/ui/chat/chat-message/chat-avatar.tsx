import { User2, Bot } from 'lucide-react';

export default function ChatAvatar({ role }: { role: string }) {
  if (role === 'user') {
    return (
      <div className="flex h-8 w-8 shrink-0 select-none items-center justify-center rounded-md border bg-background shadow">
        <User2 className="h-4 w-4" />
      </div>
    );
  }

  return (
    <div className="hidden md:flex h-8 w-8 shrink-0 select-none items-center justify-center rounded-md border bg-primary text-primary-foreground shadow">
      <Bot className="h-4 w-4" />
    </div>
  );
}
