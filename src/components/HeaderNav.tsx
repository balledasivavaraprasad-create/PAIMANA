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
    <header className="fixed top-0 left-0 right-0 z-50 h-11 sm:h-12 px-3 sm:px-6 flex items-center justify-between pointer-events-none bg-[#0B0F17] border-b border-white/10 shadow-md gap-2 sm:gap-4 transition-colors duration-200">
      {/* Top Left Logo - Clean, economical PAIMANA branding */}
      <div 
        onClick={() => onTabChange('motion')}
        className="pointer-events-auto cursor-pointer select-none shrink-0 group flex items-center gap-2"
      >
        <div className="flex flex-col">
          <div className="text-xs sm:text-sm font-bold tracking-widest font-mono-code uppercase text-white leading-none">
            PAIMANA
          </div>
          <div className="text-[8px] tracking-wider font-mono-code uppercase text-slate-400 mt-0.5 hidden xs:block">
            PROJECT INTELLIGENCE
          </div>
        </div>
      </div>

      {/* Navigation Pills Bar - Organized, economical solid dark pill strip */}
      <div className="pointer-events-auto flex items-center gap-1 p-0.5 rounded-lg bg-[#141A26] border border-white/10 overflow-x-auto scrollbar-none flex-nowrap min-w-0 max-w-full">
        {navItems.map(item => {
          const active = currentTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onTabChange(item.id)}
              className={`shrink-0 flex items-center gap-1.5 px-2.5 sm:px-3 py-1 rounded-md text-[11px] sm:text-xs font-mono-code transition-colors duration-150 cursor-pointer whitespace-nowrap ${
                active
                  ? 'bg-white text-black font-bold shadow-sm'
                  : 'text-slate-300 hover:text-white hover:bg-white/10'
              }`}
            >
              {item.icon && <span className="text-[10px] sm:text-xs">{item.icon}</span>}
              <span>{item.label}</span>
              {item.badge !== undefined && item.badge > 0 && (
                <span className={`text-[8px] sm:text-[9px] px-1.5 py-0.2 rounded-full font-bold ${
                  active ? 'bg-black text-white' : 'bg-red-500/20 text-red-300 border border-red-500/30'
                }`}>
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Top Right Controls - Clean, economical Theme Switcher */}
      <div className="pointer-events-auto flex items-center gap-2 shrink-0">
        <button
          onClick={toggleTheme}
          aria-label="Toggle Theme"
          className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-[#141A26] hover:bg-[#1E2536] border border-white/10 text-[11px] sm:text-xs font-mono-code text-slate-200 hover:text-white transition-colors duration-150 cursor-pointer"
        >
          <span className="text-xs">{isDark ? '🌙' : '☀️'}</span>
          <span className="font-medium hidden md:inline">{isDark ? 'Dark' : 'Light'}</span>
        </button>
      </div>
    </header>
  );
}

export default HeaderNav;
