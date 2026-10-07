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
  onOpenLanding?: () => void;
  isModalOpen?: boolean;
}

export function HeaderNav({
  currentTab,
  onTabChange,
  alertCount = 31,
  user = null,
  onSignOut,
  onSignInClick,
  onOpenSettings,
  onOpenLanding,
  isModalOpen = false,
}: HeaderNavProps) {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === 'dark';

  const [profileDropdownOpen, setProfileDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const isAdmin = user?.role === 'ADMIN' || user?.role === 'ANALYST' || user?.username?.toLowerCase() === 'admin';

  // 4 tabs for standard user, 7 tabs for admin
  const navItems: Array<{ id: ActiveTab; label: string; badge?: number }> = isAdmin
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
        { id: 'motion', label: 'Overview' },
        { id: 'projects', label: 'My Projects' },
        { id: 'alerts', label: 'Alerts', badge: alertCount },
        { id: 'assistant', label: 'Assistant' },
      ];

  // Close profile dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent | TouchEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setProfileDropdownOpen(false);
      }
    };
    if (profileDropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      document.addEventListener('touchstart', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('touchstart', handleClickOutside);
    };
  }, [profileDropdownOpen]);

  return (
    <div
      style={{
        position: 'fixed',
        top: '16px',
        left: '50%',
        transform: isModalOpen ? 'translate(-50%, -24px)' : 'translateX(-50%)',
        opacity: isModalOpen ? 0 : 1,
        visibility: isModalOpen ? 'hidden' : 'visible',
        width: 'max-content',
        maxWidth: 'calc(100vw - 24px)',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        zIndex: isModalOpen ? 0 : 9990,
        pointerEvents: 'none',
        transition: 'opacity 0.25s cubic-bezier(0.16, 1, 0.3, 1), transform 0.25s cubic-bezier(0.16, 1, 0.3, 1), visibility 0.25s ease',
      }}
    >
      <nav
        style={{
          margin: '0 auto',
          pointerEvents: 'auto',
          backgroundColor: 'rgba(18, 19, 20, 0.94)',
          backdropFilter: 'blur(24px)',
          WebkitBackdropFilter: 'blur(24px)',
          border: '1px solid rgba(255, 255, 255, 0.16)',
          borderRadius: '9999px',
          boxShadow: '0 20px 50px -10px rgba(0, 0, 0, 0.45), 0 2px 6px rgba(0, 0, 0, 0.2)',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          padding: '6px 10px 6px 14px',
          maxWidth: 'calc(100vw - 24px)',
          overflow: 'visible',
        }}
      >
        {/* Brand Mark: InfraBuild AI */}
        <div
          onClick={() => {
            if (onOpenLanding) {
              onOpenLanding();
            } else {
              window.location.hash = '';
            }
          }}
          title="Return to Public Landing Page"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            cursor: 'pointer',
            textDecoration: 'none',
            flexShrink: 0,
            paddingRight: '4px',
          }}
        >
          <div
            style={{
              width: '24px',
              height: '24px',
              borderRadius: '7px',
              background: '#FFFFFF',
              color: '#121314',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '11px',
              fontWeight: 900,
              boxShadow: '0 2px 8px rgba(255, 255, 255, 0.2)',
            }}
          >
            ▲
          </div>
          <span
            style={{
              fontSize: '14px',
              letterSpacing: '-0.02em',
              whiteSpace: 'nowrap',
            }}
          >
            <span style={{ fontWeight: 800, color: '#FFFFFF' }}>InfraBuild</span>{' '}
            <span style={{ fontSize: '12px', fontWeight: 700, color: '#38BDF8' }}>AI</span>
          </span>
        </div>

        {/* Separator */}
        <div
          style={{
            width: '1px',
            height: '18px',
            backgroundColor: 'rgba(255, 255, 255, 0.15)',
            flexShrink: 0,
            margin: '0 2px',
          }}
        />

        {/* Navigation Tabs (4 for user, 7 for admin) */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            flexShrink: 0,
            maxWidth: 'calc(100vw - 360px)',
            overflowX: 'auto',
            scrollbarWidth: 'none',
          }}
        >
          {navItems.map((item) => {
            const isActive =
              currentTab === item.id ||
              (item.id === 'motion' && currentTab === 'overview') ||
              (item.id === 'projects' && (currentTab === 'intelligence' || currentTab === 'investigation'));

            return (
              <button
                key={item.id}
                type="button"
                onClick={() => onTabChange(item.id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: isActive ? '6px 16px' : '6px 13px',
                  borderRadius: '9999px',
                  border: 'none',
                  backgroundColor: isActive ? '#FFFFFF' : 'transparent',
                  color: isActive ? '#121314' : 'rgba(255, 255, 255, 0.72)',
                  fontSize: '13px',
                  fontWeight: isActive ? 700 : 500,
                  cursor: 'pointer',
                  transition: 'all 0.22s cubic-bezier(0.16, 1, 0.3, 1)',
                  whiteSpace: 'nowrap',
                  boxShadow: isActive ? '0 2px 10px rgba(255, 255, 255, 0.25)' : 'none',
                }}
                onMouseEnter={(e) => {
                  if (!isActive) {
                    e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.10)';
                    e.currentTarget.style.color = '#FFFFFF';
                  }
                }}
                onMouseLeave={(e) => {
                  if (!isActive) {
                    e.currentTarget.style.backgroundColor = 'transparent';
                    e.currentTarget.style.color = 'rgba(255, 255, 255, 0.72)';
                  }
                }}
              >
                <span>{item.label}</span>
                {item.badge !== undefined && item.badge > 0 && (
                  <span
                    style={{
                      fontSize: '10px',
                      fontWeight: 800,
                      padding: '1px 6px',
                      borderRadius: '9999px',
                      backgroundColor: isActive ? '#EF4444' : 'rgba(239, 68, 68, 0.85)',
                      color: '#FFFFFF',
                      lineHeight: 1.2,
                    }}
                  >
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </div>

        {/* Separator */}
        <div
          style={{
            width: '1px',
            height: '18px',
            backgroundColor: 'rgba(255, 255, 255, 0.15)',
            flexShrink: 0,
            margin: '0 2px',
          }}
        />

        {/* Right Section: Notifications Bell, Theme Toggle, Profile/SignOut */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            flexShrink: 0,
          }}
        >
          {/* Notification Bell with Badge */}
          <button
            type="button"
            onClick={() => onTabChange('alerts')}
            title="Surveillance Alerts"
            style={{
              position: 'relative',
              width: '32px',
              height: '32px',
              borderRadius: '50%',
              backgroundColor: 'rgba(255, 255, 255, 0.08)',
              border: '1px solid rgba(255, 255, 255, 0.14)',
              color: '#FFFFFF',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              fontSize: '13px',
              transition: 'all 0.2s ease',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.16)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.08)';
            }}
          >
            🔔
            {alertCount > 0 && (
              <span
                style={{
                  position: 'absolute',
                  top: '-3px',
                  right: '-3px',
                  backgroundColor: '#EF4444',
                  color: '#FFFFFF',
                  fontSize: '9px',
                  fontWeight: 800,
                  borderRadius: '9999px',
                  padding: '1px 4px',
                  minWidth: '15px',
                  textAlign: 'center',
                  boxShadow: '0 0 6px rgba(239, 68, 68, 0.8)',
                }}
              >
                {alertCount}
              </span>
            )}
          </button>

          {/* Theme Toggle (Moon / Sun) */}
          <button
            type="button"
            onClick={toggleTheme}
            title={isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
            style={{
              width: '32px',
              height: '32px',
              borderRadius: '50%',
              backgroundColor: 'rgba(255, 255, 255, 0.08)',
              border: '1px solid rgba(255, 255, 255, 0.14)',
              color: '#FFFFFF',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              fontSize: '13px',
              transition: 'all 0.2s ease',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.16)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.08)';
            }}
          >
            {isDark ? '🌙' : '☀️'}
          </button>

          {/* Sign Out & Profile */}
          {user ? (
            <div ref={dropdownRef} style={{ display: 'flex', alignItems: 'center', gap: '6px', position: 'relative' }}>
              {/* Direct Sign Out Button */}
              <button
                type="button"
                onClick={() => {
                  setProfileDropdownOpen(false);
                  if (onSignOut) onSignOut();
                }}
                title="Sign Out of Session"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '5px 12px',
                  borderRadius: '9999px',
                  backgroundColor: 'rgba(255, 255, 255, 0.12)',
                  border: '1px solid rgba(255, 255, 255, 0.18)',
                  color: '#FFFFFF',
                  cursor: 'pointer',
                  fontSize: '12px',
                  fontWeight: 600,
                  transition: 'all 0.2s ease',
                  whiteSpace: 'nowrap',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = 'rgba(239, 68, 68, 0.28)';
                  e.currentTarget.style.borderColor = 'rgba(239, 68, 68, 0.55)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.12)';
                  e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.18)';
                }}
              >
                <span>← Sign Out</span>
              </button>

              {/* Profile Avatar Settings Trigger */}
              <button
                type="button"
                onClick={() => setProfileDropdownOpen(!profileDropdownOpen)}
                title="Profile & Settings"
                style={{
                  width: '28px',
                  height: '28px',
                  borderRadius: '50%',
                  background: 'linear-gradient(135deg, #0284C7 0%, #6366F1 100%)',
                  color: '#FFFFFF',
                  border: '1.5px solid rgba(255, 255, 255, 0.35)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '11px',
                  fontWeight: 800,
                  cursor: 'pointer',
                }}
              >
                {user.full_name ? user.full_name.charAt(0).toUpperCase() : user.username ? user.username.charAt(0).toUpperCase() : '👤'}
              </button>

              {/* Profile Dropdown */}
              {profileDropdownOpen && (
                <div
                  style={{
                    position: 'absolute',
                    top: 'calc(100% + 8px)',
                    right: 0,
                    width: '230px',
                    backgroundColor: 'rgba(18, 19, 20, 0.98)',
                    backdropFilter: 'blur(20px)',
                    border: '1px solid rgba(255, 255, 255, 0.16)',
                    borderRadius: '16px',
                    padding: '12px',
                    boxShadow: '0 20px 40px rgba(0, 0, 0, 0.6)',
                    zIndex: 9999,
                    color: '#FFFFFF',
                  }}
                >
                  <div style={{ marginBottom: '10px', paddingBottom: '8px', borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
                    <div style={{ fontSize: '13px', fontWeight: 700 }}>{user.full_name || user.username}</div>
                    <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.6)', marginTop: '2px' }}>{user.ministry || 'National Infrastructure'}</div>
                    <div style={{ fontSize: '10px', color: '#38BDF8', fontWeight: 700, marginTop: '2px', textTransform: 'uppercase' }}>
                      {isAdmin ? 'ADMINISTRATOR' : 'PROJECT OFFICER'}
                    </div>
                  </div>

                  {onOpenSettings && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                      <button
                        type="button"
                        onClick={() => {
                          setProfileDropdownOpen(false);
                          onOpenSettings('profile');
                        }}
                        style={{
                          width: '100%',
                          textAlign: 'left',
                          padding: '7px 10px',
                          borderRadius: '8px',
                          backgroundColor: 'transparent',
                          border: 'none',
                          color: 'rgba(255, 255, 255, 0.9)',
                          fontSize: '12px',
                          fontWeight: 500,
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '8px',
                          transition: 'background-color 0.15s ease',
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.1)';
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.backgroundColor = 'transparent';
                        }}
                      >
                        <span>👤</span>
                        <span>Profile Details</span>
                      </button>

                      <button
                        type="button"
                        onClick={() => {
                          setProfileDropdownOpen(false);
                          onOpenSettings('security');
                        }}
                        style={{
                          width: '100%',
                          textAlign: 'left',
                          padding: '7px 10px',
                          borderRadius: '8px',
                          backgroundColor: 'transparent',
                          border: 'none',
                          color: 'rgba(255, 255, 255, 0.9)',
                          fontSize: '12px',
                          fontWeight: 500,
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '8px',
                          transition: 'background-color 0.15s ease',
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.1)';
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.backgroundColor = 'transparent';
                        }}
                      >
                        <span>🔒</span>
                        <span>Login & Security</span>
                      </button>

                      <button
                        type="button"
                        onClick={() => {
                          setProfileDropdownOpen(false);
                          onOpenSettings('2fa');
                        }}
                        style={{
                          width: '100%',
                          textAlign: 'left',
                          padding: '7px 10px',
                          borderRadius: '8px',
                          backgroundColor: 'transparent',
                          border: 'none',
                          color: 'rgba(255, 255, 255, 0.9)',
                          fontSize: '12px',
                          fontWeight: 500,
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '8px',
                          transition: 'background-color 0.15s ease',
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.1)';
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.backgroundColor = 'transparent';
                        }}
                      >
                        <span>🛡️</span>
                        <span>Two-Factor Auth</span>
                      </button>

                      <button
                        type="button"
                        onClick={() => {
                          setProfileDropdownOpen(false);
                          onOpenSettings('sessions');
                        }}
                        style={{
                          width: '100%',
                          textAlign: 'left',
                          padding: '7px 10px',
                          borderRadius: '8px',
                          backgroundColor: 'transparent',
                          border: 'none',
                          color: 'rgba(255, 255, 255, 0.9)',
                          fontSize: '12px',
                          fontWeight: 500,
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '8px',
                          transition: 'background-color 0.15s ease',
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.1)';
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.backgroundColor = 'transparent';
                        }}
                      >
                        <span>💻</span>
                        <span>Active Sessions</span>
                      </button>

                      <button
                        type="button"
                        onClick={() => {
                          setProfileDropdownOpen(false);
                          onOpenSettings('account');
                        }}
                        style={{
                          width: '100%',
                          textAlign: 'left',
                          padding: '7px 10px',
                          borderRadius: '8px',
                          backgroundColor: 'transparent',
                          border: 'none',
                          color: 'rgba(255, 255, 255, 0.9)',
                          fontSize: '12px',
                          fontWeight: 500,
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '8px',
                          transition: 'background-color 0.15s ease',
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.1)';
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.backgroundColor = 'transparent';
                        }}
                      >
                        <span>⚙️</span>
                        <span>Account Settings</span>
                      </button>
                    </div>
                  )}

                  {onOpenLanding && (
                    <button
                      type="button"
                      onClick={() => {
                        setProfileDropdownOpen(false);
                        onOpenLanding();
                      }}
                      style={{
                        width: '100%',
                        textAlign: 'left',
                        padding: '7px 10px',
                        borderRadius: '8px',
                        backgroundColor: 'transparent',
                        border: 'none',
                        color: 'rgba(255, 255, 255, 0.85)',
                        fontSize: '12px',
                        fontWeight: 500,
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.1)';
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.backgroundColor = 'transparent';
                      }}
                    >
                      🏛️ Public Showcase
                    </button>
                  )}

                  <button
                    type="button"
                    onClick={() => {
                      setProfileDropdownOpen(false);
                      if (onSignOut) onSignOut();
                    }}
                    style={{
                      width: '100%',
                      textAlign: 'left',
                      padding: '7px 10px',
                      marginTop: '4px',
                      borderRadius: '8px',
                      backgroundColor: 'rgba(239, 68, 68, 0.15)',
                      border: '1px solid rgba(239, 68, 68, 0.3)',
                      color: '#F87171',
                      fontSize: '12px',
                      fontWeight: 600,
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.backgroundColor = 'rgba(239, 68, 68, 0.25)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.backgroundColor = 'rgba(239, 68, 68, 0.15)';
                    }}
                  >
                    🚪 Sign Out
                  </button>
                </div>
              )}
            </div>
          ) : (
            <button
              type="button"
              onClick={onSignInClick}
              style={{
                padding: '6px 14px',
                borderRadius: '9999px',
                backgroundColor: '#FFFFFF',
                color: '#121314',
                border: 'none',
                fontSize: '12px',
                fontWeight: 700,
                cursor: 'pointer',
              }}
            >
              Sign In →
            </button>
          )}
        </div>
      </nav>
    </div>
  );
}

export default HeaderNav;
