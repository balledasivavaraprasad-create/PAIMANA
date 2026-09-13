import React from 'react';
import Sidebar from './Sidebar';
import ThemeToggle from './ThemeToggle';
import type { Page } from '../App';

interface AppShellProps {
  currentPage: Page;
  onNavigate: (page: Page, projectId?: string) => void;
  children: React.ReactNode;
}

export function AppShell({ currentPage, onNavigate, children }: AppShellProps) {
  return (
    <div className="ambient-bg flex h-screen overflow-hidden text-[var(--text-primary)]">
      {/* Sidebar with floating glass container */}
      <div className="p-3 pr-0 h-full flex-shrink-0">
        <Sidebar currentPage={currentPage} onNavigate={onNavigate} />
      </div>

      {/* Main Content Viewport */}
      <div className="flex-1 flex flex-col min-w-0 h-full overflow-hidden">
        {/* Sticky Header Bar */}
        <header className="flex-shrink-0 h-14 px-6 flex items-center justify-between border-b border-[var(--border-hairline)] bg-[var(--glass-bg)] backdrop-blur-md z-20">
          <div className="flex items-center gap-3">
            <h1 className="text-sm font-semibold font-display tracking-tight text-[var(--text-primary)]">
              PAIMANA AI Infrastructure Intelligence
            </h1>
            <span className="text-[10px] uppercase font-mono-data tracking-wider px-2 py-0.5 rounded bg-[var(--accent-soft)] text-[var(--accent)] font-semibold border border-[var(--accent-soft)]">
              Central Sector Monitor
            </span>
          </div>

          <div className="flex items-center gap-4">
            <div className="hidden md:flex items-center gap-2 text-xs text-[var(--text-muted)]">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span>Live Engine Sync · FY26</span>
            </div>

            <ThemeToggle />
          </div>
        </header>

        {/* Dynamic Page Scroll Body */}
        <main className="flex-1 overflow-y-auto min-w-0 p-6">
          {children}
        </main>
      </div>
    </div>
  );
}

export default AppShell;
