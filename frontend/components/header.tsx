'use client';

import { useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { useAuth } from '@/app/authProvider';
import { useConversationContext } from '@/app/ConversationContext';
import { Button } from '@/components/ui/button';

import { Menu, X, PanelLeft } from 'lucide-react';

interface MobileNavigationProps {
  isOpen: boolean;
  onClose: () => void;
}

interface AuthContextType {
  isAuthenticated: boolean;
  logout: () => void;
}

export function MobileNavigation({
  isOpen,
  onClose,
}: MobileNavigationProps): JSX.Element | null {
  const { isAuthenticated, logout, isAdmin } = useAuth();

  const handleLogout = () => {
    logout();
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 mt-14">
      <div
        className="absolute inset-0 bg-background/80 backdrop-blur-10"
        onClick={onClose}
      />
      <div className="absolute inset-x-0 top-0 bg-background border-t px-4 shadow-lg">
        <div className="mt-4 space-y-4">
          <Button variant="outline" asChild className="w-full justify-start">
            <Link href="/features">Features</Link>
          </Button>
          {isAuthenticated && isAdmin && (
            <Button variant="outline" asChild className="w-full justify-start">
              <Link href="/admin">Admin</Link>
            </Button>
          )}
          {isAuthenticated ? (
            <Button
              variant="outline"
              onClick={handleLogout}
              className="w-full justify-start"
            >
              Logout
            </Button>
          ) : (
            <Button variant="ghost" asChild className="w-full justify-start">
              <Link href="/signin">Sign In</Link>
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}

export function Header() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const { isAuthenticated, logout, firstName, isAdmin } = useAuth();
  const { isSidebarOpen, setIsSidebarOpen } = useConversationContext();

  const toggleSidebar = () => {
    setIsSidebarOpen(!isSidebarOpen);
  };

  const handleLogout = () => {
    logout();
    setIsMenuOpen(false);
  };

  return (
    <>
      <header className="sticky top-0 z-50 w-full border-b bg-background backdrop-blur">
        <div className="px-4 flex h-14 items-center justify-between">
          <div className="flex items-center">
            <Button
              variant="ghost"
              size="icon"
              className="bg-muted"
              onClick={toggleSidebar}
            >
              <PanelLeft className="h-5 w-5" />
              <span className="sr-only">Toggle sidebar</span>
            </Button>
            {/* {isAuthenticated && (
            <Button
              variant="ghost"
              size="icon"
              className="bg-muted"
              onClick={toggleSidebar}
            >
              <PanelLeft className="h-5 w-5" />
              <span className="sr-only">Toggle sidebar</span>
            </Button>
          )} */}
            <Link href="/" className="flex items-center space-x-2">
              <Image
                src="/logo-black.png"
                alt="Nyayantar AI Logo"
                width={32}
                height={32}
                className="h-8 w-8"
                priority
              />
              <span className="text-xl font-bold">Nyayantar AI</span>
            </Link>
          </div>
          <nav className="hidden md:flex items-center space-x-4">
            <Button variant="link" asChild>
              <Link href="/features">Features</Link>
            </Button>
            {isAuthenticated && isAdmin && (
              <Button variant="link" asChild>
                <Link href="/admin">Admin</Link>
              </Button>
            )}
            {isAuthenticated ? (
              <Button variant="outline" onClick={handleLogout}>
                Logout
              </Button>
            ) : (
              <Button variant="outline" asChild>
                <Link href="/signin">Sign In</Link>
              </Button>
            )}
          </nav>
          <button
            className="inline-flex items-center justify-center rounded-md p-2 text-foreground hover:bg-accent hover:text-accent-foreground focus:outline-none focus:ring-2 focus:ring-inset focus:ring-primary md:hidden"
            onClick={() => setIsMenuOpen(!isMenuOpen)}
          >
            <span className="sr-only">Toggle menu</span>
            {isMenuOpen ? (
              <X className="h-6 w-6" aria-hidden="true" />
            ) : (
              <Menu className="h-6 w-6" aria-hidden="true" />
            )}
          </button>
        </div>
      </header>
      <MobileNavigation
        isOpen={isMenuOpen}
        onClose={() => setIsMenuOpen(false)}
      />
    </>
  );
}
