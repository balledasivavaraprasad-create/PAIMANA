import React from 'react';
import { useTheme } from '../hooks/useTheme';

export type ActiveTab = 'motion' | 'intelligence' | 'investigation' | 'analytics' | 'assistant' | 'alerts' | 'login';

interface HeaderNavProps {
  currentTab: ActiveTab;
  onTabChange: (tab: ActiveTab) => void;
  alertCount?: number;
  user?: { full_name?: string; ministry?: string; username?: string } | null;
  onSignOut?: () => void;
  onSignInClick?: () => void;
}

export function HeaderNav({
  currentTab,
  onTabChange,
  alertCount = 0,
  user = null,
  onSignOut,
  onSignInClick
}: HeaderNavProps) {
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
    <header className={`fixed top-0 left-0 right-0 z-50 h-11 sm:h-12 px-3 sm:px-6 flex items-center justify-between pointer-events-none shadow-md gap-2 sm:gap-4 transition-colors duration-200 ${
      isDark ? 'bg-[#0B0F17] border-b border-white/10' : 'bg-white/90 backdrop-blur-md border-b border-black/10'
    }`}>
      {/* Top Left Logo - Clean, economical PAIMANA branding */}
      <div 
        onClick={() => onTabChange('motion')}
        className="pointer-events-auto cursor-pointer select-none shrink-0 group flex items-center gap-2"
      >
        <div className="flex flex-col">
          <div className={`text-xs sm:text-sm font-bold tracking-widest font-mono-code uppercase leading-none ${isDark ? 'text-white' : 'text-black'}`}>
            PAIMANA
          </div>
          <div className={`text-[8px] tracking-wider font-mono-code uppercase mt-0.5 hidden xs:block ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
            PROJECT INTELLIGENCE
          </div>
        </div>
      </div>

      {/* Navigation Pills Bar - Organized, economical pill strip */}
      <div 
        style={!isDark ? { color: '#000000' } : undefined}
        className={`pointer-events-auto flex items-center gap-1 p-0.5 rounded-lg border overflow-x-auto scrollbar-none flex-nowrap min-w-0 max-w-full ${
          isDark ? 'bg-[#141A26] border-white/10' : 'bg-slate-200/90 border-black/15 shadow-inner'
        }`}
      >
        {navItems.map(item => {
          const active = currentTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onTabChange(item.id)}
              style={!isDark ? { color: '#000000' } : undefined}
              className={`shrink-0 flex items-center gap-1.5 px-2.5 sm:px-3 py-1 rounded-md text-[11px] sm:text-xs font-mono-code transition-colors duration-150 cursor-pointer whitespace-nowrap ${
                active
                  ? (isDark ? 'bg-white text-black font-bold shadow-sm' : 'bg-white text-black font-bold shadow-sm border border-black/20')
                  : (isDark ? 'text-slate-300 hover:text-white hover:bg-white/10' : 'text-black hover:bg-black/10 font-semibold')
              }`}
            >
              {item.icon && <span style={!isDark ? { color: '#000000' } : undefined} className={`text-[10px] sm:text-xs ${isDark ? '' : 'text-black'}`}>{item.icon}</span>}
              <span style={!isDark ? { color: '#000000' } : undefined} className={isDark ? '' : 'text-black'}>{item.label}</span>
              {item.badge !== undefined && item.badge > 0 && (
                <span 
                  style={!isDark ? { color: '#000000' } : undefined}
                  className={`text-[8px] sm:text-[9px] px-1.5 py-0.2 rounded-full font-bold ${
                    active 
                      ? (isDark ? 'bg-black text-white' : 'bg-red-500/25 text-black border border-red-600/40')
                      : (isDark ? 'bg-red-500/20 text-red-300 border border-red-500/30' : 'bg-red-500/20 text-black border border-red-500/40')
                  }`}
                >
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Top Right Controls - User Status & Theme Switcher */}
      <div className="pointer-events-auto flex items-center gap-2 shrink-0">
        {user ? (
          <div className="flex items-center gap-1.5">
            <div className={`hidden sm:flex flex-col text-right leading-none ${isDark ? 'text-slate-300' : 'text-slate-800'}`}>
              <span className="text-[10px] font-bold font-mono-code truncate max-w-[140px]">
                {user.full_name || user.username}
              </span>
              <span className="text-[8px] font-mono-code opacity-70 truncate max-w-[140px]">
                {user.ministry || 'MoSPI Official'}
              </span>
            </div>
            {onSignOut && (
              <button
                onClick={onSignOut}
                title="Sign Out"
                className={`px-2 py-1 rounded-md border text-[10px] font-mono-code transition-colors cursor-pointer ${
                  isDark
                    ? 'bg-rose-500/15 hover:bg-rose-500/25 border-rose-500/30 text-rose-300'
                    : 'bg-rose-50 hover:bg-rose-100 border-rose-300 text-rose-700'
                }`}
              >
                Sign Out
              </button>
            )}
          </div>
        ) : (
          <button
            onClick={() => onSignInClick ? onSignInClick() : onTabChange('login')}
            className={`px-2.5 py-1 rounded-md border text-[11px] sm:text-xs font-mono-code font-bold transition-all cursor-pointer flex items-center gap-1 shadow-sm ${
              isDark
                ? 'bg-sky-500/20 hover:bg-sky-500/30 border-sky-400/40 text-sky-300'
                : 'bg-sky-50 hover:bg-sky-100 border-sky-300 text-sky-800'
            }`}
          >
            <span>✦</span>
            <span>Sign In</span>
          </button>
        )}

        <button
          onClick={toggleTheme}
          aria-label="Toggle Theme"
          className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md border text-[11px] sm:text-xs font-mono-code transition-colors duration-150 cursor-pointer ${
            isDark
              ? 'bg-[#141A26] hover:bg-[#1E2536] border-white/10 text-slate-200 hover:text-white'
              : 'bg-slate-200/90 hover:bg-slate-300 border-black/10 text-slate-900 font-semibold'
          }`}
        >
          <span className="text-xs">{isDark ? '🌙' : '☀️'}</span>
          <span className="font-medium hidden md:inline">{isDark ? 'Dark' : 'Light'}</span>
        </button>
      </div>
    </header>
  );
}

export default HeaderNav;
