import React from 'react';
import type { Page } from '../App';
import ThemeToggle from './ThemeToggle';

const icons = {
  overview: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>
    </svg>
  ),
  projects: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
    </svg>
  ),
  intelligence: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 2a10 10 0 1 0 10 10"/><path d="M12 6v6l4 2"/><circle cx="18" cy="6" r="3"/>
    </svg>
  ),
  analytics: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>
    </svg>
  ),
  investigation: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/><line x1="11" y1="8" x2="11" y2="14"/><line x1="8" y1="11" x2="14" y2="11"/>
    </svg>
  ),
  assistant: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
    </svg>
  ),
  alerts: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/>
    </svg>
  ),
  reports: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/>
    </svg>
  ),
};

const navItems: Array<{ id: Page; label: string; badge?: number }> = [
  { id: 'overview', label: 'Overview' },
  { id: 'projects', label: 'Projects' },
  { id: 'intelligence', label: 'Risk Intelligence' },
  { id: 'analytics', label: 'Portfolio Analytics' },
  { id: 'investigation', label: 'AI Investigations' },
  { id: 'assistant', label: 'Intelligence Assistant' },
  { id: 'alerts', label: 'Alerts', badge: 14 },
  { id: 'reports', label: 'Reports' },
];

interface SidebarProps {
  currentPage: Page;
  onNavigate: (page: Page) => void;
}

export default function Sidebar({ currentPage, onNavigate }: SidebarProps) {
  return (
    <div
      className="glass-floating rounded-2xl flex flex-col h-full w-[240px] overflow-hidden"
    >
      {/* Brand Header */}
      <div className="p-4 border-b border-[var(--border-hairline)]">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-xl bg-[var(--accent)] text-white flex items-center justify-center font-bold text-xs font-display shadow-md">
            PAI
          </div>
          <div>
            <div className="font-semibold text-sm font-display tracking-tight text-[var(--text-primary)]">
              PAIMANA AI
            </div>
            <div className="text-[10px] text-[var(--text-muted)] tracking-wider">
              Project Intelligence System
            </div>
          </div>
        </div>

        <div className="mt-3 p-2 rounded-lg bg-[var(--surface-sunken)] border border-[var(--border-hairline)] flex items-center gap-2">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 flex-shrink-0" />
          <span className="text-[10px] text-[var(--text-secondary)] font-medium truncate">
            Govt. of India · FY 2025–26
          </span>
        </div>
      </div>

      {/* Navigation List */}
      <nav className="flex-1 p-2 space-y-1 overflow-y-auto">
        <div className="px-3 py-1 text-[9px] font-semibold uppercase tracking-widest text-[var(--text-muted)]">
          Navigation
        </div>
        {navItems.map(item => {
          const isActive = currentPage === item.id;
          const icon = icons[item.id];
          return (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              className={`w-full flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-medium transition-all cursor-pointer ${
                isActive
                  ? 'bg-[var(--accent)] text-white font-semibold shadow-md'
                  : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-sunken)]'
              }`}
            >
              <span className={isActive ? 'opacity-100' : 'opacity-70'}>{icon}</span>
              <span className="flex-1 text-left tracking-tight">{item.label}</span>
              {item.badge && (
                <span
                  className={`text-[10px] font-bold px-1.5 py-0.5 rounded-full ${
                    isActive ? 'bg-white/20 text-white' : 'bg-red-500/15 text-red-500'
                  }`}
                >
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Footer Profile & Theme Switcher */}
      <div className="p-3 border-t border-[var(--border-hairline)] bg-[var(--surface-sunken)] space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-[10px] font-semibold uppercase tracking-wider text-[var(--text-muted)]">
            Appearance
          </span>
          <ThemeToggle />
        </div>

        <div className="pt-2 border-t border-[var(--border-hairline)] flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-full bg-[var(--accent-soft)] border border-[var(--accent)] text-[var(--accent)] font-semibold text-xs flex items-center justify-center flex-shrink-0">
            AS
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-xs font-medium text-[var(--text-primary)] truncate">Arjun Sharma</div>
            <div className="text-[10px] text-[var(--text-muted)] truncate">Senior Analyst</div>
          </div>
        </div>
      </div>
    </div>
  );
}
