import React from 'react';
import { useTheme } from '../hooks/useTheme';

export type ActiveTab = 'motion' | 'intelligence' | 'investigation' | 'analytics' | 'assistant' | 'alerts';

interface HeaderNavProps {
  currentTab: ActiveTab;
  onTabChange: (tab: ActiveTab) => void;
  alertCount?: number;
}

export function HeaderNav({ currentTab, onTabChange, alertCount = 0 }: HeaderNavProps) {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === 'dark';

  const navItems: Array<{ id: ActiveTab; label: string; icon?: string; badge?: number }> = [
    { id: 'motion', label: 'Motion', icon: '✦' },
    { id: 'intelligence', label: 'Intelligence', icon: '⌖' },
    { id: 'investigation', label: 'Investigation', icon: '🔍' },
    { id: 'analytics', label: 'Analytics', icon: '📈' },
    { id: 'assistant', label: 'Assistant', icon: '💬' },
    { id: 'alerts', label: 'Alerts', badge: alertCount },
  ];

  return (
    <header className="fixed top-0 left-0 right-0 z-50 px-3 sm:px-6 py-2.5 sm:py-3.5 flex items-center justify-between pointer-events-none backdrop-blur-md bg-black/40 border-b border-white/10 gap-2 sm:gap-4">
      {/* Top Left Logo - Clean PAIMANA heading without extra icon beside it */}
      <div 
        onClick={() => onTabChange('motion')}
        className="pointer-events-auto cursor-pointer select-none shrink-0"
      >
        <div className="text-base sm:text-lg font-bold tracking-widest font-mono-code uppercase text-white drop-shadow-md leading-none">
          PAIMANA
        </div>
        <div className="text-[10px] tracking-widest font-mono-code uppercase text-white/60 drop-shadow-sm mt-0.5 hidden xs:block">
          PROJECT INTELLIGENCE
        </div>
      </div>

      {/* Navigation Pills Bar - Fully Responsive with horizontal scroll on mobile/half screen */}
      <div className="pointer-events-auto flex items-center gap-1 sm:gap-2 p-1 sm:p-1.5 rounded-xl sm:rounded-2xl bg-black/60 backdrop-blur-xl border border-white/20 shadow-xl overflow-x-auto scrollbar-none flex-nowrap min-w-0 max-w-full">
        {navItems.map(item => {
          const active = currentTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onTabChange(item.id)}
              className={`shrink-0 flex items-center gap-1.5 px-2.5 sm:px-3.5 py-1 sm:py-1.5 rounded-lg sm:rounded-xl text-xs sm:text-sm font-mono-code transition-all duration-200 cursor-pointer whitespace-nowrap ${
                active
                  ? 'bg-white text-black font-bold shadow-md'
                  : 'text-white/80 hover:text-white hover:bg-white/10'
              }`}
            >
              {item.icon && <span className="text-xs sm:text-sm">{item.icon}</span>}
              <span>{item.label}</span>
              {item.badge !== undefined && item.badge > 0 && (
                <span className={`text-[10px] sm:text-xs px-1.5 py-0.2 rounded-full font-bold ${active ? 'bg-black text-white' : 'bg-white/20 text-white border border-white/30'}`}>
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Top Right Controls - Live engine removed as requested */}
      <div className="pointer-events-auto flex items-center gap-2 shrink-0">
        <button
          onClick={toggleTheme}
          aria-label="Toggle Theme"
          className="flex items-center gap-1.5 px-2.5 sm:px-3.5 py-1.5 rounded-xl bg-black/60 border border-white/25 text-xs sm:text-sm font-mono-code text-white hover:bg-white/20 transition-all cursor-pointer shadow-md"
        >
          <span>{isDark ? '🌙' : '☀️'}</span>
          <span className="tracking-tight font-semibold hidden md:inline">{isDark ? 'Dark' : 'Light'}</span>
        </button>
      </div>
    </header>
  );
}

export default HeaderNav;
