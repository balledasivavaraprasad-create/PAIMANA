import React, { useEffect, useState } from 'react';
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
  const [apiOnline, setApiOnline] = useState<boolean | null>(null);

  useEffect(() => {
    fetch('http://localhost:8000/health')
      .then(res => res.ok ? setApiOnline(true) : setApiOnline(false))
      .catch(() => setApiOnline(false));
  }, []);

  const navItems: Array<{ id: ActiveTab; label: string; icon: string; badge?: number }> = [
    { id: 'motion', label: 'Executive Motion', icon: '✦' },
    { id: 'intelligence', label: 'Project Intelligence', icon: '📊' },
    { id: 'investigation', label: 'AI Investigation', icon: '🔍' },
    { id: 'analytics', label: 'Analytics', icon: '📈' },
    { id: 'assistant', label: 'AI Assistant', icon: '💬' },
    { id: 'alerts', label: 'Alerts', icon: '🚨', badge: alertCount },
  ];

  return (
    <header className="fixed top-0 left-0 right-0 z-50 px-6 py-4 flex items-center justify-between pointer-events-none backdrop-blur-md bg-black/25 border-b border-white/10">
      {/* Top Left Logo */}
      <div 
        onClick={() => onTabChange('motion')}
        className="flex items-center gap-2 pointer-events-auto cursor-pointer select-none"
      >
        <div className="w-4 h-4 flex items-center justify-center text-xs text-white">
          ✦
        </div>
        <div>
          <div className="text-sm font-bold tracking-widest font-mono-code uppercase text-white drop-shadow-md leading-none">
            PAIMANA
          </div>
          <div className="text-[9px] tracking-widest font-mono-code uppercase text-slate-300 drop-shadow-sm mt-0.5">
            PROJECT INTELLIGENCE
          </div>
        </div>
      </div>

      {/* Navigation Pills Bar */}
      <div className="pointer-events-auto flex items-center gap-1.5 p-1 rounded-2xl bg-black/50 backdrop-blur-xl border border-white/20 shadow-xl overflow-x-auto max-w-[65vw]">
        {navItems.map(item => {
          const active = currentTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onTabChange(item.id)}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-xl text-xs font-mono-code transition-all duration-200 cursor-pointer whitespace-nowrap ${
                active
                  ? 'bg-white text-black font-bold shadow-md'
                  : 'text-white/80 hover:text-white hover:bg-white/10'
              }`}
            >
              <span className="text-xs">{item.icon}</span>
              <span>{item.label}</span>
              {item.badge !== undefined && item.badge > 0 && (
                <span className={`text-[10px] px-1.5 py-0.2 rounded-full font-bold ${active ? 'bg-black text-white' : 'bg-red-500 text-white'}`}>
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Top Right Controls & Backend Status */}
      <div className="pointer-events-auto flex items-center gap-3">
        <div className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-black/40 border border-white/15 text-[10px] font-mono-code text-white/90">
          <span className={`w-2 h-2 rounded-full ${apiOnline ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'}`} />
          <span>{apiOnline ? 'Live Engine' : 'FastAPI Connecting'}</span>
        </div>

        <button
          onClick={toggleTheme}
          className="flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-black/60 border border-white/25 text-xs font-mono-code text-white hover:bg-white/20 transition-all cursor-pointer shadow-md"
        >
          <span>{isDark ? '🌙' : '☀️'}</span>
          <span className="tracking-tight font-semibold hidden md:inline">{isDark ? 'Dark' : 'Light'}</span>
        </button>
      </div>
    </header>
  );
}

export default HeaderNav;
