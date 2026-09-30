import React, { useState, useEffect } from 'react';
import { useTheme } from '../hooks/useTheme';
import { UserProfile } from '../lib/api';

export type SettingsTab = 'profile' | 'security' | '2fa' | 'sessions' | 'account';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentUser?: UserProfile | null;
  initialTab?: SettingsTab;
  onSignOut?: () => void;
}

export default function SettingsModal({
  isOpen,
  onClose,
  currentUser,
  initialTab = 'profile',
  onSignOut
}: SettingsModalProps) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  const [activeTab, setActiveTab] = useState<SettingsTab>(initialTab);
  const [fullName, setFullName] = useState(currentUser?.full_name || 'Balleda Siva Vara Prasad');
  const [displayName, setDisplayName] = useState(currentUser?.username || 'siva');
  const [email, setEmail] = useState(currentUser?.email || 'balledasivavaraprasad@gmail.com');
  const [bio, setBio] = useState('Senior Infrastructure Risk Specialist · National Project Monitoring Division');
  const [phone, setPhone] = useState('+91 98765 43210');
  const [timezone, setTimezone] = useState('Asia/Kolkata (IST +05:30)');
  const [twoFactorEnabled, setTwoFactorEnabled] = useState(false);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);

  useEffect(() => {
    if (initialTab) setActiveTab(initialTab);
  }, [initialTab, isOpen]);

  // Close on Escape key press
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    if (isOpen) {
      window.addEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'hidden';
    }
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = '';
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const handleSave = () => {
    setSaveMessage('Settings saved successfully!');
    setTimeout(() => setSaveMessage(null), 2500);
  };

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-black/80 backdrop-blur-md animate-fade-in"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div 
        className={`relative w-full max-w-3xl max-h-[90vh] flex flex-col rounded-2xl border shadow-2xl overflow-hidden transition-colors ${
          isDark 
            ? 'bg-[#0B0F17] border-white/20 text-white shadow-[0_25px_80px_rgba(0,0,0,0.95)]' 
            : 'bg-white border-slate-300 text-slate-900 shadow-2xl'
        }`}
      >
        {/* Header */}
        <div className={`px-5 py-4 border-b flex items-center justify-between gap-3 shrink-0 ${
          isDark ? 'border-white/10 bg-[#0F1522]' : 'border-slate-200 bg-slate-50'
        }`}>
          <div className="flex items-center gap-2">
            <span className="text-base">⚙️</span>
            <h2 className="text-base sm:text-lg font-bold font-display">
              Account & Profile Settings
            </h2>
          </div>
          <button
            onClick={onClose}
            className={`w-8 h-8 rounded-lg flex items-center justify-center font-mono font-bold text-sm transition-all cursor-pointer ${
              isDark ? 'bg-white/10 hover:bg-white/20 text-white' : 'bg-slate-200 hover:bg-slate-300 text-slate-800'
            }`}
          >
            ✕
          </button>
        </div>

        {/* Tab Navigation */}
        <div className={`flex items-center gap-1 px-5 pt-3 border-b overflow-x-auto scrollbar-none shrink-0 ${
          isDark ? 'border-white/10 bg-[#0B0F17]' : 'border-slate-200 bg-slate-100'
        }`}>
          {[
            { id: 'profile', label: 'Profile Details' },
            { id: 'security', label: 'Login & Security' },
            { id: '2fa', label: 'Two-Factor Auth' },
            { id: 'sessions', label: 'Active Sessions' },
            { id: 'account', label: 'Account Settings' },
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as SettingsTab)}
              className={`px-3 py-2 text-xs font-mono font-bold border-b-2 transition-all cursor-pointer whitespace-nowrap ${
                activeTab === tab.id
                  ? (isDark ? 'border-white text-white' : 'border-slate-900 text-slate-900')
                  : (isDark ? 'border-transparent text-white/50 hover:text-white/80' : 'border-transparent text-slate-500 hover:text-slate-900')
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <div className="overflow-y-auto p-5 sm:p-7 space-y-5 flex-1">
          {saveMessage && (
            <div className={`p-3 rounded-lg border text-xs font-mono ${
              isDark ? 'bg-emerald-500/15 border-emerald-500/30 text-emerald-400' : 'bg-emerald-50 border-emerald-300 text-emerald-800'
            }`}>
              ✓ {saveMessage}
            </div>
          )}

          {/* TAB 1: PROFILE DETAILS */}
          {activeTab === 'profile' && (
            <div className="space-y-4 animate-fade-in">
              <div className={`flex items-center gap-4 pb-4 border-b ${isDark ? 'border-white/10' : 'border-slate-200'}`}>
                <div className="w-16 h-16 rounded-full bg-gradient-to-br from-indigo-500 to-sky-600 flex items-center justify-center text-2xl font-bold text-white shadow-lg border-2 border-white/20">
                  {fullName.charAt(0).toUpperCase()}
                </div>
                <div className="space-y-1">
                  <div className={`font-bold text-sm ${isDark ? 'text-white' : 'text-slate-900'}`}>{fullName}</div>
                  <div className={`text-xs font-mono ${isDark ? 'text-white/60' : 'text-slate-600'}`}>{currentUser?.ministry || 'Infrastructure Administration'}</div>
                  <button className={`text-xs font-mono ${isDark ? 'text-sky-400 hover:underline' : 'text-sky-600 hover:underline'}`}>
                    Change profile photo
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
                <div>
                  <label className={`block text-xs font-mono font-semibold mb-1 ${isDark ? 'text-white/70' : 'text-slate-700'}`}>
                    Full Name
                  </label>
                  <input
                    type="text"
                    value={fullName}
                    onChange={e => setFullName(e.target.value)}
                    className={`w-full px-3 py-2 rounded-lg text-xs outline-none transition-colors ${
                      isDark ? 'bg-white/5 border border-white/20 text-white focus:border-white' : 'bg-white border border-slate-300 text-slate-900 focus:border-slate-900'
                    }`}
                  />
                </div>
                <div>
                  <label className={`block text-xs font-mono font-semibold mb-1 ${isDark ? 'text-white/70' : 'text-slate-700'}`}>
                    Display Name
                  </label>
                  <input
                    type="text"
                    value={displayName}
                    onChange={e => setDisplayName(e.target.value)}
                    className={`w-full px-3 py-2 rounded-lg text-xs outline-none transition-colors ${
                      isDark ? 'bg-white/5 border border-white/20 text-white focus:border-white' : 'bg-white border border-slate-300 text-slate-900 focus:border-slate-900'
                    }`}
                  />
                </div>
              </div>

              <div>
                <label className={`block text-xs font-mono font-semibold mb-1 ${isDark ? 'text-white/70' : 'text-slate-700'}`}>
                  Headline / Bio Description
                </label>
                <textarea
                  rows={2}
                  value={bio}
                  onChange={e => setBio(e.target.value)}
                  className={`w-full px-3 py-2 rounded-lg text-xs outline-none transition-colors ${
                    isDark ? 'bg-white/5 border border-white/20 text-white focus:border-white' : 'bg-white border border-slate-300 text-slate-900 focus:border-slate-900'
                  }`}
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5">
                <div>
                  <label className={`block text-xs font-mono font-semibold mb-1 ${isDark ? 'text-white/70' : 'text-slate-700'}`}>
                    Contact Email
                  </label>
                  <input
                    type="email"
                    value={email}
                    onChange={e => setEmail(e.target.value)}
                    className={`w-full px-3 py-2 rounded-lg text-xs outline-none transition-colors ${
                      isDark ? 'bg-white/5 border border-white/20 text-white focus:border-white' : 'bg-white border border-slate-300 text-slate-900 focus:border-slate-900'
                    }`}
                  />
                </div>
                <div>
                  <label className={`block text-xs font-mono font-semibold mb-1 ${isDark ? 'text-white/70' : 'text-slate-700'}`}>
                    Phone Number
                  </label>
                  <input
                    type="text"
                    value={phone}
                    onChange={e => setPhone(e.target.value)}
                    className={`w-full px-3 py-2 rounded-lg text-xs outline-none transition-colors ${
                      isDark ? 'bg-white/5 border border-white/20 text-white focus:border-white' : 'bg-white border border-slate-300 text-slate-900 focus:border-slate-900'
                    }`}
                  />
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: LOGIN & SECURITY */}
          {activeTab === 'security' && (
            <div className="space-y-4 animate-fade-in">
              <div className={`p-4 rounded-xl border space-y-3 ${isDark ? 'bg-white/5 border-white/10' : 'bg-slate-50 border-slate-200'}`}>
                <h4 className={`text-xs font-mono font-bold uppercase ${isDark ? 'text-white/80' : 'text-slate-900'}`}>Change Password</h4>
                <div className="space-y-2.5 max-w-md">
                  <input
                    type="password"
                    placeholder="Current Password"
                    className={`w-full px-3 py-2 rounded-lg text-xs outline-none ${
                      isDark ? 'bg-black/40 border border-white/15 text-white focus:border-white' : 'bg-white border border-slate-300 text-slate-900 focus:border-slate-900'
                    }`}
                  />
                  <input
                    type="password"
                    placeholder="New Password (min 8 characters)"
                    className={`w-full px-3 py-2 rounded-lg text-xs outline-none ${
                      isDark ? 'bg-black/40 border border-white/15 text-white focus:border-white' : 'bg-white border border-slate-300 text-slate-900 focus:border-slate-900'
                    }`}
                  />
                  <input
                    type="password"
                    placeholder="Confirm New Password"
                    className={`w-full px-3 py-2 rounded-lg text-xs outline-none ${
                      isDark ? 'bg-black/40 border border-white/15 text-white focus:border-white' : 'bg-white border border-slate-300 text-slate-900 focus:border-slate-900'
                    }`}
                  />
                  <button
                    onClick={handleSave}
                    className={`px-4 py-2 rounded-lg text-xs font-mono font-bold transition-all cursor-pointer ${
                      isDark ? 'bg-white text-black hover:bg-slate-200' : 'bg-slate-900 text-white hover:bg-black shadow-sm'
                    }`}
                  >
                    Update Password
                  </button>
                </div>
              </div>

              <div className={`p-4 rounded-xl border space-y-2 ${isDark ? 'bg-white/5 border-white/10' : 'bg-slate-50 border-slate-200'}`}>
                <h4 className={`text-xs font-mono font-bold uppercase ${isDark ? 'text-white/80' : 'text-slate-900'}`}>Registered Email Address</h4>
                <p className={`text-xs ${isDark ? 'text-white/70' : 'text-slate-600'}`}>
                  Primary notification channel: <strong className={isDark ? 'text-white' : 'text-slate-900'}>{email}</strong>
                </p>
              </div>
            </div>
          )}

          {/* TAB 3: TWO-FACTOR AUTHENTICATION */}
          {activeTab === '2fa' && (
            <div className="space-y-4 animate-fade-in">
              <div className={`p-5 rounded-xl border space-y-3 ${isDark ? 'bg-white/5 border-white/10' : 'bg-slate-50 border-slate-200'}`}>
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className={`text-xs font-mono font-bold uppercase ${isDark ? 'text-white' : 'text-slate-900'}`}>Two-Factor Authentication (2FA)</h4>
                    <p className={`text-xs mt-0.5 ${isDark ? 'text-white/70' : 'text-slate-600'}`}>
                      Require a 6-digit verification code sent via SMS or Authenticator App on sign in.
                    </p>
                  </div>
                  <button
                    onClick={() => setTwoFactorEnabled(!twoFactorEnabled)}
                    className={`px-4 py-2 rounded-xl text-xs font-mono font-bold transition-all cursor-pointer ${
                      twoFactorEnabled
                        ? (isDark ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40' : 'bg-emerald-100 text-emerald-800 border border-emerald-300')
                        : (isDark ? 'bg-white/10 hover:bg-white/20 text-white border border-white/20' : 'bg-white hover:bg-slate-200 text-slate-800 border border-slate-300 shadow-sm')
                    }`}
                  >
                    {twoFactorEnabled ? '✓ Enabled' : 'Enable 2FA'}
                  </button>
                </div>
              </div>

              <div className={`p-4 rounded-xl border text-xs space-y-1 font-mono ${
                isDark ? 'bg-white/5 border-white/10 text-white/70' : 'bg-slate-50 border-slate-200 text-slate-700'
              }`}>
                <p>Status: {twoFactorEnabled ? 'Enforced on next login' : 'Optional (Recommended for Admin & Officials)'}</p>
                <p>Standard: TOTP RFC 6238 / Government Sovereign Auth</p>
              </div>
            </div>
          )}

          {/* TAB 4: ACTIVE SESSIONS */}
          {activeTab === 'sessions' && (
            <div className="space-y-3 animate-fade-in">
              <h4 className={`text-xs font-mono font-bold uppercase ${isDark ? 'text-white/80' : 'text-slate-900'}`}>Active Login Sessions</h4>
              <div className="space-y-2">
                <div className={`p-3.5 rounded-xl border flex items-center justify-between text-xs ${
                  isDark ? 'bg-white/5 border-white/10' : 'bg-slate-50 border-slate-200'
                }`}>
                  <div className="space-y-0.5">
                    <div className={`font-bold flex items-center gap-2 ${isDark ? 'text-white' : 'text-slate-900'}`}>
                      <span>💻 Current Device (macOS · Chrome)</span>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-mono ${
                        isDark ? 'bg-emerald-500/20 text-emerald-400' : 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                      }`}>Active Now</span>
                    </div>
                    <div className={`text-[11px] font-mono ${isDark ? 'text-white/60' : 'text-slate-500'}`}>IP: 103.21.244.12 · New Delhi, India</div>
                  </div>
                  <span className={`text-[11px] font-mono ${isDark ? 'text-white/50' : 'text-slate-500'}`}>This session</span>
                </div>

                <div className={`p-3.5 rounded-xl border flex items-center justify-between text-xs ${
                  isDark ? 'bg-white/5 border-white/10' : 'bg-slate-50 border-slate-200'
                }`}>
                  <div className="space-y-0.5">
                    <div className={`font-bold ${isDark ? 'text-white' : 'text-slate-900'}`}>📱 Mobile Browser (iOS Safari)</div>
                    <div className={`text-[11px] font-mono ${isDark ? 'text-white/60' : 'text-slate-500'}`}>Last active: Yesterday at 18:24 · Mumbai, India</div>
                  </div>
                  <button className="text-xs text-rose-500 hover:underline font-mono cursor-pointer">
                    Revoke
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* TAB 5: ACCOUNT SETTINGS */}
          {activeTab === 'account' && (
            <div className="space-y-4 animate-fade-in">
              <div className={`p-4 rounded-xl border space-y-2 ${isDark ? 'bg-white/5 border-white/10' : 'bg-slate-50 border-slate-200'}`}>
                <h4 className={`text-xs font-mono font-bold uppercase ${isDark ? 'text-white' : 'text-slate-900'}`}>Account Deactivation</h4>
                <p className={`text-xs ${isDark ? 'text-white/70' : 'text-slate-600'}`}>
                  Temporarily disable your monitoring account and pause automated risk threshold SMS and email dispatches.
                </p>
                <button
                  onClick={() => alert('Account deactivation requested. Your department administrator will review.')}
                  className={`px-3.5 py-1.5 rounded-lg border text-xs font-mono cursor-pointer mt-1 ${
                    isDark ? 'border-amber-500/40 text-amber-300 hover:bg-amber-500/10' : 'border-amber-500 text-amber-900 bg-white hover:bg-amber-50'
                  }`}
                >
                  Deactivate Account
                </button>
              </div>

              <div className={`p-4 rounded-xl border space-y-2 ${isDark ? 'bg-rose-500/10 border-rose-500/30' : 'bg-rose-50 border-rose-200'}`}>
                <h4 className={`text-xs font-mono font-bold uppercase ${isDark ? 'text-rose-300' : 'text-rose-900'}`}>Danger Zone · Account Deletion</h4>
                <p className={`text-xs ${isDark ? 'text-rose-200/80' : 'text-rose-700'}`}>
                  Permanently remove this login profile and disassociate all personal alert configurations.
                </p>
                <button
                  onClick={() => {
                    if (confirm('Are you sure you want to request account deletion?')) {
                      alert('Deletion request sent to system administrator.');
                    }
                  }}
                  className="px-3.5 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-700 text-white text-xs font-mono font-bold cursor-pointer mt-1"
                >
                  Delete Account
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className={`px-5 py-3 border-t flex items-center justify-between shrink-0 ${
          isDark ? 'border-white/10 bg-[#0F1522]' : 'border-slate-200 bg-slate-50'
        }`}>
          <div className="flex items-center gap-2">
            {onSignOut && (
              <button
                onClick={onSignOut}
                className={`px-3 py-1.5 rounded-lg border text-xs font-mono cursor-pointer transition-colors ${
                  isDark
                    ? 'border-rose-500/30 bg-rose-500/15 hover:bg-rose-500/25 text-rose-300'
                    : 'border-rose-300 bg-rose-100 hover:bg-rose-200 text-rose-800 font-bold'
                }`}
              >
                Sign Out
              </button>
            )}
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className={`px-4 py-1.5 rounded-lg border text-xs font-mono cursor-pointer transition-colors ${
                isDark ? 'border-white/20 text-white/80 hover:bg-white/10' : 'border-slate-300 text-slate-700 hover:bg-slate-200'
              }`}
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              className={`px-4 py-1.5 rounded-lg text-xs font-mono font-bold cursor-pointer transition-all ${
                isDark ? 'bg-white text-black hover:bg-slate-200' : 'bg-slate-900 text-white hover:bg-black shadow-sm'
              }`}
            >
              Save Changes
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
