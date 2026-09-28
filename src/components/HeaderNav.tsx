import React, { useRef, useState, useEffect } from 'react';
import { useTheme } from '../hooks/useTheme';
import { SettingsTab } from './SettingsModal';

export type ActiveTab = 
  | 'motion' 
  | 'projects' 
  | 'intelligence' 
  | 'investigation' 
  | 'analytics' 
  | 'assistant' 
  | 'alerts' 
  | 'data_models' 
  | 'users_audit' 
  | 'login'
  | 'overview'
  | 'reports';

interface HeaderNavProps {
  currentTab: ActiveTab;
  onTabChange: (tab: ActiveTab) => void;
  alertCount?: number;
  user?: { full_name?: string; ministry?: string; username?: string; role?: string; designation?: string; email?: string } | null;
  onSignOut?: () => void;
  onSignInClick?: () => void;
  onOpenSettings?: (tab?: SettingsTab) => void;
}

export function HeaderNav({
  currentTab,
  onTabChange,
  alertCount = 0,
  user = null,
  onSignOut,
  onSignInClick,
  onOpenSettings
}: HeaderNavProps) {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === 'dark';

  const scrollRef = useRef<HTMLDivElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const [canScrollLeft, setCanScrollLeft] = useState(false);
  const [canScrollRight, setCanScrollRight] = useState(false);
  const [profileDropdownOpen, setProfileDropdownOpen] = useState(false);

  const isAdmin = user?.role === 'ADMIN' || user?.role === 'ANALYST';

  // Navigation Items (Investigation removed from standalone navbar tabs — now accessible via dedicated pop-up modal)
  const navItems: Array<{ id: ActiveTab; label: string; badge?: number; icon?: string }> = isAdmin
    ? [
        { id: 'motion', label: 'Overview' },
        { id: 'projects', label: 'Portfolio' },
        { id: 'analytics', label: 'Analytics' },
        { id: 'alerts', label: 'Alerts & Automation', badge: alertCount },
        { id: 'assistant', label: 'Assistant' },
        { id: 'data_models', label: 'Data & Models' },
        { id: 'users_audit', label: 'Users & Audit' },
      ]
    : [
        { id: 'motion', label: 'Dashboard' },
        { id: 'projects', label: 'My Projects' },
        { id: 'alerts', label: 'Alerts', badge: alertCount },
        { id: 'assistant', label: 'Assistant' },
      ];

  const checkScroll = () => {
    const el = scrollRef.current;
    if (!el) return;
    setCanScrollLeft(el.scrollLeft > 6);
    setCanScrollRight(el.scrollLeft + el.clientWidth < el.scrollWidth - 6);
  };

  useEffect(() => {
    checkScroll();
    const el = scrollRef.current;
    if (el) {
      el.addEventListener('scroll', checkScroll, { passive: true });
      window.addEventListener('resize', checkScroll);
    }
    return () => {
      el?.removeEventListener('scroll', checkScroll);
      window.removeEventListener('resize', checkScroll);
    };
  }, [navItems, currentTab]);

  // Click outside to close profile dropdown
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setProfileDropdownOpen(false);
      }
    };
    if (profileDropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [profileDropdownOpen]);

  const scrollStride = (direction: 'left' | 'right') => {
    const el = scrollRef.current;
    if (!el) return;
    const stride = Math.max(130, el.clientWidth * 0.6);
    el.scrollBy({
      left: direction === 'right' ? stride : -stride,
      behavior: 'smooth'
    });
  };

  return (
    <header className={`fixed top-0 left-0 right-0 z-50 h-11 sm:h-12 px-3 sm:px-6 flex items-center justify-between pointer-events-none shadow-md gap-2 sm:gap-4 transition-colors duration-200 ${
      isDark ? 'bg-[#0B0F17] border-b border-white/10' : 'bg-white/90 backdrop-blur-md border-b border-black/10'
    }`}>
      {/* Top Left Logo - Clean, economical InfraBuild AI branding */}
      <div 
        onClick={() => onTabChange('motion')}
        className="pointer-events-auto cursor-pointer select-none shrink-0 group flex items-center gap-2"
      >
        <div className="flex flex-col">
          <div className={`text-xs sm:text-sm font-bold tracking-wider font-mono-code uppercase leading-none ${isDark ? 'text-white' : 'text-black'}`}>
            InfraBuild AI
          </div>
          <div className={`text-[8px] tracking-wider font-mono-code uppercase mt-0.5 hidden xs:block ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
            {isAdmin ? 'ADMIN COMMAND CENTER' : 'PROJECT MONITOR'}
          </div>
        </div>
      </div>

      {/* Navigation Pills Bar with Stride Navigation Arrows */}
      <div className="relative flex items-center min-w-0 max-w-full overflow-hidden">
        {/* Left Stride Arrow */}
        {canScrollLeft && (
          <button
            onClick={() => scrollStride('left')}
            title="Previous pages"
            aria-label="Scroll navigation left"
            className={`pointer-events-auto shrink-0 z-20 w-5 sm:w-6 h-7 rounded-l-md flex items-center justify-center text-xs font-bold transition-all shadow-sm cursor-pointer ${
              isDark
                ? 'bg-[#141A26] hover:bg-[#1E2638] text-white border-y border-l border-white/20'
                : 'bg-white hover:bg-slate-100 text-black border-y border-l border-black/20'
            }`}
          >
            ‹
          </button>
        )}

        <div 
          ref={scrollRef}
          style={!isDark ? { color: '#000000' } : undefined}
          className={`pointer-events-auto flex items-center gap-1 p-0.5 rounded-lg border overflow-x-auto scrollbar-none flex-nowrap min-w-0 max-w-full scroll-smooth ${
            isDark ? 'bg-[#141A26] border-white/10' : 'bg-slate-200/90 border-black/15 shadow-inner'
          } ${canScrollLeft ? 'rounded-l-none' : ''} ${canScrollRight ? 'rounded-r-none' : ''}`}
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

        {/* Right Stride Arrow */}
        {canScrollRight && (
          <button
            onClick={() => scrollStride('right')}
            title="Next pages"
            aria-label="Scroll navigation right"
            className={`pointer-events-auto shrink-0 z-20 w-5 sm:w-6 h-7 rounded-r-md flex items-center justify-center text-xs font-bold transition-all shadow-sm cursor-pointer ${
              isDark
                ? 'bg-[#141A26] hover:bg-[#1E2638] text-white border-y border-r border-white/20'
                : 'bg-white hover:bg-slate-100 text-black border-y border-r border-black/20'
            }`}
          >
            ›
          </button>
        )}
      </div>

      {/* Top Right Controls - Profile Icon Dropdown & Theme Toggle */}
      <div className="pointer-events-auto flex items-center gap-2 shrink-0">
        {user ? (
          <div ref={dropdownRef} className="relative">
            {/* Profile Avatar Button */}
            <button
              onClick={() => setProfileDropdownOpen(!profileDropdownOpen)}
              title="Profile & Settings"
              style={{ color: '#ffffff' }}
              className={`w-7 sm:w-8 h-7 sm:h-8 rounded-full flex items-center justify-center font-mono font-bold text-xs sm:text-sm transition-all cursor-pointer shadow-md select-none header-avatar-light ${
                isDark
                  ? 'bg-gradient-to-tr from-sky-600 to-indigo-600 text-white border border-white/25 hover:border-white/50'
                  : 'bg-gradient-to-tr from-blue-600 via-indigo-600 to-sky-500 text-white border-2 border-white ring-2 ring-indigo-500/35 shadow-[0_2px_10px_rgba(79,70,229,0.35)] hover:scale-105'
              }`}
            >
              <span style={{ color: '#ffffff' }} className="header-avatar-light">
                {user.full_name ? user.full_name.charAt(0).toUpperCase() : user.username ? user.username.charAt(0).toUpperCase() : '👤'}
              </span>
            </button>

            {/* Dropdown Menu */}
            {profileDropdownOpen && (
              <div 
                className={`absolute right-0 top-10 sm:top-11 w-64 rounded-xl border shadow-2xl p-1.5 z-50 animate-fade-in ${
                  isDark
                    ? 'bg-[#0E1422] border-white/20 text-white shadow-black/90'
                    : 'bg-white border-slate-300 text-slate-900 shadow-xl'
                }`}
              >
                {/* User Header */}
                <div className={`px-3 py-2 border-b mb-1 ${isDark ? 'border-white/10' : 'border-slate-200'}`}>
                  <div className="font-bold text-xs truncate">
                    {user.full_name || user.username}
                  </div>
                  <div className={`text-[10px] font-mono truncate ${isDark ? 'text-white/60' : 'text-slate-500'}`}>
                    {user.ministry || 'Infrastructure Administration'}
                  </div>
                  <span className={`inline-block text-[8px] px-1.5 py-0.2 rounded font-mono font-bold uppercase mt-1 ${
                    isAdmin 
                      ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30' 
                      : (isDark ? 'bg-white/10 text-white/80' : 'bg-slate-200 text-slate-800')
                  }`}>
                    {isAdmin ? 'ADMIN' : 'PROJECT OFFICER'}
                  </span>
                </div>

                {/* Condensed Settings Items */}
                <div className="space-y-0.5 text-xs font-mono">
                  <button
                    onClick={() => {
                      setProfileDropdownOpen(false);
                      onOpenSettings && onOpenSettings('profile');
                    }}
                    className={`w-full text-left px-2.5 py-1.5 rounded-lg flex items-center gap-2 cursor-pointer transition-colors ${
                      isDark ? 'hover:bg-white/10 text-white/90' : 'hover:bg-slate-100 text-slate-800'
                    }`}
                  >
                    <span>👤</span>
                    <span>Profile Details</span>
                  </button>

                  <button
                    onClick={() => {
                      setProfileDropdownOpen(false);
                      onOpenSettings && onOpenSettings('security');
                    }}
                    className={`w-full text-left px-2.5 py-1.5 rounded-lg flex items-center gap-2 cursor-pointer transition-colors ${
                      isDark ? 'hover:bg-white/10 text-white/90' : 'hover:bg-slate-100 text-slate-800'
                    }`}
                  >
                    <span>🔒</span>
                    <span>Login & Security</span>
                  </button>

                  <button
                    onClick={() => {
                      setProfileDropdownOpen(false);
                      onOpenSettings && onOpenSettings('2fa');
                    }}
                    className={`w-full text-left px-2.5 py-1.5 rounded-lg flex items-center gap-2 cursor-pointer transition-colors ${
                      isDark ? 'hover:bg-white/10 text-white/90' : 'hover:bg-slate-100 text-slate-800'
                    }`}
                  >
                    <span>🛡️</span>
                    <span>Two-Factor Auth</span>
                  </button>

                  <button
                    onClick={() => {
                      setProfileDropdownOpen(false);
                      onOpenSettings && onOpenSettings('sessions');
                    }}
                    className={`w-full text-left px-2.5 py-1.5 rounded-lg flex items-center gap-2 cursor-pointer transition-colors ${
                      isDark ? 'hover:bg-white/10 text-white/90' : 'hover:bg-slate-100 text-slate-800'
                    }`}
                  >
                    <span>💻</span>
                    <span>Active Sessions</span>
                  </button>

                  <button
                    onClick={() => {
                      setProfileDropdownOpen(false);
                      onOpenSettings && onOpenSettings('account');
                    }}
                    className={`w-full text-left px-2.5 py-1.5 rounded-lg flex items-center gap-2 cursor-pointer transition-colors ${
                      isDark ? 'hover:bg-white/10 text-white/90' : 'hover:bg-slate-100 text-slate-800'
                    }`}
                  >
                    <span>⚙️</span>
                    <span>Account Settings</span>
                  </button>
                </div>

                {/* Sign Out Action */}
                {onSignOut && (
                  <div className={`pt-1 mt-1 border-t ${isDark ? 'border-white/10' : 'border-slate-200'}`}>
                    <button
                      onClick={() => {
                        setProfileDropdownOpen(false);
                        onSignOut();
                      }}
                      className="w-full text-left px-2.5 py-1.5 rounded-lg flex items-center gap-2 text-xs font-mono text-rose-400 hover:bg-rose-500/15 cursor-pointer transition-colors"
                    >
                      <span>🚪</span>
                      <span>Sign Out</span>
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        ) : (
          <button
            onClick={() => onSignInClick ? onSignInClick() : onTabChange('login')}
            className={`px-2.5 py-1 rounded-md border text-[11px] sm:text-xs font-mono-code font-bold transition-all cursor-pointer flex items-center gap-1 shadow-sm ${
              isDark
                ? 'bg-white/10 hover:bg-white/20 border-white/20 text-white'
                : 'bg-black/10 hover:bg-black/20 border-black/20 text-black'
            }`}
          >
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
