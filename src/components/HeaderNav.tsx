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
    <header className="fixed top-0 left-0 right-0 z-50 px-3 sm:px-6 py-2.5 sm:py-3.5 flex items-center justify-between pointer-events-none backdrop-blur-2xl bg-gradient-to-b from-white/10 via-black/35 to-black/55 border-b border-white/20 shadow-[0_8px_32px_rgba(0,0,0,0.35)] gap-2 sm:gap-4 transition-colors duration-500 ease-out">
      {/* Top Left Logo - Glossy PAIMANA heading */}
      <div 
        onClick={() => onTabChange('motion')}
        className="pointer-events-auto cursor-pointer select-none shrink-0 group transition-transform duration-500 ease-out hover:scale-[1.02]"
      >
        <div className="text-base sm:text-lg font-bold tracking-widest font-mono-code uppercase text-white drop-shadow-[0_2px_8px_rgba(255,255,255,0.25)] leading-none">
          PAIMANA
        </div>
        <div className="text-[10px] tracking-widest font-mono-code uppercase text-white/60 drop-shadow-sm mt-0.5 hidden xs:block transition-colors duration-500 group-hover:text-white/80">
          PROJECT INTELLIGENCE
        </div>
      </div>

      {/* Navigation Pills Bar - Liquid Gloss Glass with Slower & Smoother Transitions */}
      <div className="pointer-events-auto flex items-center gap-1 sm:gap-1.5 p-1 sm:p-1.5 rounded-xl sm:rounded-2xl bg-gradient-to-b from-white/18 via-black/45 to-black/70 backdrop-blur-2xl border border-white/25 shadow-[0_12px_28px_rgba(0,0,0,0.40),inset_0_1px_1.5px_rgba(255,255,255,0.45)] overflow-x-auto scrollbar-none flex-nowrap min-w-0 max-w-full transition-all duration-500 ease-out">
        {navItems.map(item => {
          const active = currentTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onTabChange(item.id)}
              className={`shrink-0 flex items-center gap-1.5 px-3 sm:px-4 py-1 sm:py-1.5 rounded-lg sm:rounded-xl text-xs sm:text-sm font-mono-code transition-all duration-500 ease-out cursor-pointer whitespace-nowrap ${
                active
                  ? 'bg-gradient-to-b from-white via-slate-100 to-slate-200 text-black font-bold shadow-[0_4px_16px_rgba(255,255,255,0.40),inset_0_1px_1px_rgba(255,255,255,0.9)] border border-white/90 scale-[1.02]'
                  : 'text-white/80 hover:text-white hover:bg-white/12 hover:shadow-[inset_0_1px_1px_rgba(255,255,255,0.25)] border border-transparent hover:border-white/20'
              }`}
            >
              {item.icon && <span className="text-xs sm:text-sm transition-transform duration-500">{item.icon}</span>}
              <span>{item.label}</span>
              {item.badge !== undefined && item.badge > 0 && (
                <span className={`text-[10px] sm:text-xs px-1.5 py-0.2 rounded-full font-bold transition-all duration-500 ${active ? 'bg-black text-white shadow-inner' : 'bg-white/20 text-white border border-white/30'}`}>
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Top Right Controls - Glossy Theme Switcher with Smooth Slower Transition */}
      <div className="pointer-events-auto flex items-center gap-2 shrink-0">
        <button
          onClick={toggleTheme}
          aria-label="Toggle Theme"
          className="flex items-center gap-1.5 px-3 sm:px-4 py-1.5 rounded-xl bg-gradient-to-b from-white/15 via-black/45 to-black/70 border border-white/25 text-xs sm:text-sm font-mono-code text-white hover:bg-white/20 hover:border-white/40 shadow-[0_4px_16px_rgba(0,0,0,0.25),inset_0_1px_1px_rgba(255,255,255,0.35)] transition-all duration-500 ease-out cursor-pointer"
        >
          <span className="transition-transform duration-500 ease-out">{isDark ? '🌙' : '☀️'}</span>
          <span className="tracking-tight font-semibold hidden md:inline">{isDark ? 'Dark' : 'Light'}</span>
        </button>
      </div>
    </header>
  );
}

export default HeaderNav;
