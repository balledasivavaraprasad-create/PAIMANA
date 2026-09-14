import React, { useState, useEffect, useRef } from 'react';
import { useTheme } from '../hooks/useTheme';
import {
  fetchMinistries, loginUser, registerUser, verifyOtp, resendOtp,
  MinistryItem, AuthResponse
} from '../lib/api';

interface LoginProps {
  onLoginSuccess: (authData: AuthResponse) => void;
  onExploreGuest?: () => void;
}

const SLIDES = [
  {
    image: '/assets/bg-1-highway.png',
    label: 'Road Transport & Logistics · National Expressways (1080p HD)'
  },
  {
    image: '/assets/bg-2-bridge.png',
    label: 'Indian Railways · Chenab Megaproject USBRL (1080p HD)'
  },
  {
    image: '/assets/bg-3-metro.png',
    label: 'Urban Transit · High-Speed Viaduct Corridor (1080p HD)'
  }
];

export default function Login({ onLoginSuccess, onExploreGuest }: LoginProps) {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === 'dark';

  // Slideshow state
  const [currentSlide, setCurrentSlide] = useState(0);

  // Tab & Flow state
  const [activeTab, setActiveTab] = useState<'signin' | 'signup'>('signin');
  const [signupStep, setSignupStep] = useState<1 | 2 | 3>(1);

  // Form states - Sign In
  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [loginError, setLoginError] = useState('');
  const [loginLoading, setLoginLoading] = useState(false);

  // Form states - Sign Up
  const [fullName, setFullName] = useState('');
  const [signupEmail, setSignupEmail] = useState('');
  const [ministryId, setMinistryId] = useState<number | ''>('');
  const [designation, setDesignation] = useState('');
  const [signupPassword, setSignupPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [termsAccepted, setTermsAccepted] = useState(false);
  const [aiAckAccepted, setAiAckAccepted] = useState(false);
  const [signupError, setSignupError] = useState('');
  const [signupLoading, setSignupLoading] = useState(false);

  // OTP state
  const [otpDigits, setOtpDigits] = useState(['', '', '', '', '', '']);
  const [otpError, setOtpError] = useState('');
  const [otpLoading, setOtpLoading] = useState(false);
  const [resendTimer, setResendTimer] = useState(30);
  const [canResend, setCanResend] = useState(false);

  // Ministries list
  const [ministries, setMinistries] = useState<MinistryItem[]>([]);

  // Policy Modal
  const [showPolicyModal, setShowPolicyModal] = useState(false);
  const [policyTab, setPolicyTab] = useState<'terms' | 'privacy'>('terms');

  const otpInputsRef = useRef<(HTMLInputElement | null)[]>([]);

  // 1. Slideshow interval
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentSlide(prev => (prev + 1) % SLIDES.length);
    }, 6000);
    return () => clearInterval(timer);
  }, []);

  // 2. Fetch ministries
  useEffect(() => {
    fetchMinistries().then(setMinistries).catch(console.warn);
  }, []);

  // 3. Resend OTP countdown
  useEffect(() => {
    let interval: any = null;
    if (signupStep === 2 && resendTimer > 0) {
      interval = setInterval(() => {
        setResendTimer(prev => prev - 1);
      }, 1000);
    } else if (resendTimer === 0) {
      setCanResend(true);
    }
    return () => clearInterval(interval);
  }, [signupStep, resendTimer]);

  // Handle Login Submit
  const handleLoginSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoginError('');
    if (!loginEmail.trim() || !loginPassword) {
      setLoginError('Email/username and password are required.');
      return;
    }
    setLoginLoading(true);
    try {
      const data = await loginUser({ email: loginEmail.trim(), password: loginPassword });
      onLoginSuccess(data);
    } catch (err: any) {
      setLoginError(err.message || 'Authentication failed. Please check credentials.');
    } finally {
      setLoginLoading(false);
    }
  };

  // Fast 1-click Demo Fill
  const fillDemoCredentials = (role: 'admin' | 'analyst') => {
    if (role === 'admin') {
      setLoginEmail('admin');
      setLoginPassword('paimana2026');
    } else {
      setLoginEmail('analyst');
      setLoginPassword('paimana2026');
    }
  };

  // Handle Signup Submit
  const handleSignupSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSignupError('');

    if (!fullName.trim() || !signupEmail.trim() || !signupPassword || !confirmPassword) {
      setSignupError('All required fields must be completed.');
      return;
    }
    if (signupPassword.length < 8) {
      setSignupError('Password must be at least 8 characters.');
      return;
    }
    if (signupPassword !== confirmPassword) {
      setSignupError('Passwords do not match.');
      return;
    }
    if (!termsAccepted || !aiAckAccepted) {
      setSignupError('You must accept the Terms and AI/ML processing acknowledgement.');
      return;
    }

    setSignupLoading(true);
    try {
      await registerUser({
        fullName: fullName.trim(),
        email: signupEmail.trim(),
        ministryId: ministryId === '' ? undefined : Number(ministryId),
        designation: designation.trim() || 'Project Officer',
        password: signupPassword,
        termsAccepted,
        aiAckAccepted
      });
      setSignupStep(2);
      setResendTimer(30);
      setCanResend(false);
    } catch (err: any) {
      setSignupError(err.message || 'Registration failed.');
    } finally {
      setSignupLoading(false);
    }
  };

  // Handle OTP Inputs
  const handleOtpChange = (index: number, value: string) => {
    const clean = value.replace(/[^0-9]/g, '').slice(-1);
    const newDigits = [...otpDigits];
    newDigits[index] = clean;
    setOtpDigits(newDigits);

    if (clean && index < 5) {
      otpInputsRef.current[index + 1]?.focus();
    }
  };

  const handleOtpKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Backspace' && !otpDigits[index] && index > 0) {
      otpInputsRef.current[index - 1]?.focus();
    }
  };

  // Handle Verify OTP Submit
  const handleVerifyOtp = async () => {
    const fullCode = otpDigits.join('');
    if (fullCode.length !== 6) {
      setOtpError('Enter all 6 numeric digits.');
      return;
    }
    setOtpError('');
    setOtpLoading(true);
    try {
      await verifyOtp({ email: signupEmail.trim(), otp: fullCode });
      setSignupStep(3);
    } catch (err: any) {
      setOtpError(err.message || 'Invalid verification code.');
    } finally {
      setOtpLoading(false);
    }
  };

  // Handle Resend OTP
  const handleResendOtp = async () => {
    if (!canResend) return;
    setOtpError('');
    try {
      await resendOtp({ email: signupEmail.trim() });
      setResendTimer(30);
      setCanResend(false);
    } catch (err: any) {
      setOtpError(err.message || 'Could not resend code.');
    }
  };

  return (
    <div className={`relative min-h-screen flex flex-col justify-between p-4 sm:p-6 md:p-8 select-none transition-colors duration-200 overflow-x-hidden ${
      isDark ? 'text-slate-100' : 'text-slate-900'
    }`}>
      {/* ---------------- Fullscreen HD Background Slider (Crystal-Clear 1080p) ---------------- */}
      <div className={`fixed inset-0 z-0 overflow-hidden ${isDark ? 'bg-[#070C16]' : 'bg-[#0B1220]'}`}>
        {SLIDES.map((slide, idx) => (
          <div
            key={idx}
            style={{
              backgroundImage: `url('${slide.image}')`,
              imageRendering: '-webkit-optimize-contrast'
            }}
            className={`absolute inset-0 w-full h-full bg-cover bg-center bg-no-repeat transition-all duration-1000 transform ${
              currentSlide === idx ? 'opacity-100 scale-100' : 'opacity-0 scale-105 pointer-events-none'
            }`}
          />
        ))}
        {/* Subtle Vignette Scrim - Zero blur on background image to preserve 100% native 1080p sharpness */}
        <div className={`absolute inset-0 pointer-events-none transition-colors duration-300 ${
          isDark 
            ? 'bg-radial-gradient from-black/15 via-black/45 to-black/85' 
            : 'bg-radial-gradient from-transparent via-black/10 to-black/35'
        }`} />
      </div>

      {/* ---------------- Top Right: Theme Switcher & Guest Button ---------------- */}
      <div className="fixed top-4 right-4 sm:top-6 sm:right-8 z-50 flex items-center gap-2">
        {onExploreGuest && (
          <button
            onClick={onExploreGuest}
            className={`px-3 py-1.5 rounded-full text-xs font-mono font-medium border backdrop-blur-md shadow-md transition-all ${
              isDark 
                ? 'bg-white/10 hover:bg-white/20 border-white/20 text-white' 
                : 'bg-white/80 hover:bg-white border-black/15 text-slate-800'
            }`}
          >
            Explore as Guest →
          </button>
        )}
        <button
          onClick={toggleTheme}
          aria-label="Toggle Theme"
          className={`flex items-center gap-1.5 p-1.5 sm:px-3 sm:py-1.5 rounded-full border text-xs font-mono backdrop-blur-md shadow-md transition-colors ${
            isDark 
              ? 'bg-[#0E192E]/70 hover:bg-[#152542] border-white/20 text-white' 
              : 'bg-white/80 hover:bg-white border-black/15 text-slate-800'
          }`}
        >
          <span>{isDark ? '🌙' : '☀️'}</span>
          <span className="hidden sm:inline font-medium">{isDark ? 'Dark' : 'Light'}</span>
        </button>
      </div>

      {/* ---------------- Top: Full-Width Macro Telemetry Box ---------------- */}
      <header className={`relative z-10 w-full max-w-7xl mx-auto rounded-2xl border p-4 sm:p-6 mb-6 backdrop-blur-xl shadow-2xl transition-all ${
        isDark 
          ? 'bg-[#0A1222]/65 border-white/15' 
          : 'bg-white/75 border-white/80 shadow-slate-300/50'
      }`}>
        {/* Brand Row */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-white/10">
          <div>
            <div className="flex items-baseline gap-3 flex-wrap">
              <span className={`font-serif text-2xl sm:text-3xl font-bold tracking-wide ${isDark ? 'text-white' : 'text-slate-900'}`}>
                PAIMANA
              </span>
              <span className={`text-xs sm:text-sm font-medium ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
                National Infrastructure Predictive Monitoring &amp; Early-Warning Platform
              </span>
            </div>
            <div className="text-xs sm:text-sm font-serif font-semibold text-sky-400 mt-1">
              Ministry of Statistics &amp; Programme Implementation (MoSPI) · Institutional Decision Support
            </div>
          </div>

          <div className="flex items-center gap-2 self-start md:self-auto flex-wrap">
            <span className={`text-xs px-3 py-1 rounded-full border flex items-center gap-1.5 ${
              isDark ? 'bg-white/5 border-white/15 text-slate-300' : 'bg-slate-100 border-black/10 text-slate-700'
            }`}>
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              Surveillance: <strong className={isDark ? 'text-white' : 'text-black'}>1,842 Projects</strong>
            </span>
            <span className={`text-xs px-3 py-1 rounded-full border ${
              isDark ? 'bg-white/5 border-white/15 text-slate-300' : 'bg-slate-100 border-black/10 text-slate-700'
            }`}>
              Model Engine: <strong className={isDark ? 'text-white' : 'text-black'}>XGBoost + DPHIS v2</strong>
            </span>
          </div>
        </div>

        {/* 4-Metric Grid */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 my-4">
          <div className={`p-3.5 rounded-xl border flex flex-col justify-between ${
            isDark ? 'bg-[#0E192E]/70 border-white/10' : 'bg-white/80 border-slate-200'
          }`}>
            <span className="text-[10px] sm:text-xs font-mono font-semibold uppercase tracking-wider text-slate-400">
              Active Corridors
            </span>
            <div className={`text-xl sm:text-2xl font-bold font-mono my-1 ${isDark ? 'text-white' : 'text-slate-900'}`}>
              1,842
            </div>
            <span className="text-[10px] text-emerald-400 font-medium">1,262 Nominal Velocity</span>
          </div>

          <div className={`p-3.5 rounded-xl border flex flex-col justify-between ${
            isDark ? 'bg-[#0E192E]/70 border-white/10' : 'bg-white/80 border-slate-200'
          }`}>
            <span className="text-[10px] sm:text-xs font-mono font-semibold uppercase tracking-wider text-slate-400">
              Total Capex Monitored
            </span>
            <div className={`text-xl sm:text-2xl font-bold font-mono my-1 text-sky-400`}>
              ₹28.4L Cr
            </div>
            <span className="text-[10px] text-slate-400">Disbursed: ₹19.1L Cr</span>
          </div>

          <div className={`p-3.5 rounded-xl border flex flex-col justify-between ${
            isDark ? 'bg-[#0E192E]/70 border-white/10' : 'bg-white/80 border-slate-200'
          }`}>
            <span className="text-[10px] sm:text-xs font-mono font-semibold uppercase tracking-wider text-slate-400">
              Corridors At Risk
            </span>
            <div className={`text-xl sm:text-2xl font-bold font-mono my-1 text-amber-400`}>
              412
            </div>
            <span className="text-[10px] text-amber-400">Moderate / High Escalation</span>
          </div>

          <div className={`p-3.5 rounded-xl border flex flex-col justify-between ${
            isDark ? 'bg-[#0E192E]/70 border-white/10' : 'bg-white/80 border-slate-200'
          }`}>
            <span className="text-[10px] sm:text-xs font-mono font-semibold uppercase tracking-wider text-slate-400">
              Critical Slippage
            </span>
            <div className={`text-xl sm:text-2xl font-bold font-mono my-1 text-rose-500`}>
              168
            </div>
            <span className="text-[10px] text-rose-400 font-medium">Intervention Mandate Triggered</span>
          </div>
        </div>

        {/* Sector Chips Bar */}
        <div className="flex items-center gap-2 pt-3 border-t border-white/10 overflow-x-auto scrollbar-none text-xs">
          <span className="font-mono text-slate-400 uppercase text-[10px] tracking-wider whitespace-nowrap">
            Key Sectors:
          </span>
          {[
            'Road Transport & Logistics', 'Indian Railways (USBRL)', 'National Highways & Expressways',
            'Energy & Power', 'Water Resources & Sanitation', 'Coal & Steel Mining', 'Petroleum & Natural Gas'
          ].map((sec, i) => (
            <span
              key={i}
              className={`px-2.5 py-1 rounded-md border text-[11px] whitespace-nowrap ${
                isDark ? 'bg-white/5 border-white/10 text-slate-300' : 'bg-slate-100 border-slate-200 text-slate-700'
              }`}
            >
              {sec}
            </span>
          ))}
        </div>
      </header>

      {/* ---------------- Center: Authentication Card ---------------- */}
      <main className="relative z-10 flex justify-center items-center w-full max-w-md mx-auto my-auto py-4">
        <div className={`w-full rounded-2xl border p-6 sm:p-8 backdrop-blur-2xl shadow-2xl transition-all ${
          isDark 
            ? 'bg-[#0A1222]/75 border-white/20 shadow-black/60' 
            : 'bg-white/85 border-white/90 shadow-xl'
        }`}>
          {/* Tabs: Sign in vs Create account */}
          <div className={`flex rounded-lg p-1 mb-6 border ${
            isDark ? 'bg-black/30 border-white/10' : 'bg-slate-200/80 border-black/10'
          }`}>
            <button
              type="button"
              onClick={() => { setActiveTab('signin'); setLoginError(''); }}
              className={`flex-1 py-2 text-xs font-mono font-medium rounded-md transition-all ${
                activeTab === 'signin'
                  ? (isDark ? 'bg-white/15 text-white font-bold shadow' : 'bg-white text-black font-bold shadow')
                  : (isDark ? 'text-slate-400 hover:text-white' : 'text-slate-600 hover:text-black')
              }`}
            >
              Sign in
            </button>
            <button
              type="button"
              onClick={() => { setActiveTab('signup'); setSignupError(''); setSignupStep(1); }}
              className={`flex-1 py-2 text-xs font-mono font-medium rounded-md transition-all ${
                activeTab === 'signup'
                  ? (isDark ? 'bg-white/15 text-white font-bold shadow' : 'bg-white text-black font-bold shadow')
                  : (isDark ? 'text-slate-400 hover:text-white' : 'text-slate-600 hover:text-black')
              }`}
            >
              Create account
            </button>
          </div>

          {/* ================= SIGN IN TAB ================= */}
          {activeTab === 'signin' && (
            <div>
              <div className="mb-5">
                <h1 className="text-xl sm:text-2xl font-serif font-bold tracking-tight mb-1">
                  Sign in
                </h1>
                <p className="text-xs text-slate-400">
                  Enter your official credentials to access the PAIMANA predictive intelligence console.
                </p>
              </div>

              {loginError && (
                <div className="mb-4 p-3 rounded-lg bg-rose-500/15 border border-rose-500/30 text-rose-400 text-xs font-medium">
                  {loginError}
                </div>
              )}

              <form onSubmit={handleLoginSubmit} className="space-y-4">
                <div>
                  <label className="block text-xs font-mono text-slate-300 mb-1.5">
                    Official Email or Username
                  </label>
                  <input
                    type="text"
                    value={loginEmail}
                    onChange={e => setLoginEmail(e.target.value)}
                    placeholder="name@ministry.gov.in or admin"
                    autoComplete="username"
                    className={`w-full px-3.5 py-2.5 rounded-lg border text-sm font-mono outline-none transition-all ${
                      isDark 
                        ? 'bg-black/40 border-white/15 text-white focus:border-sky-400 focus:ring-2 focus:ring-sky-400/20' 
                        : 'bg-white/90 border-slate-300 text-black focus:border-sky-600 focus:ring-2 focus:ring-sky-600/20'
                    }`}
                  />
                </div>

                <div>
                  <div className="flex justify-between items-center mb-1.5">
                    <label className="text-xs font-mono text-slate-300">
                      Password
                    </label>
                    <a href="#forgot" onClick={(e) => { e.preventDefault(); alert('Please contact your ministry system administrator for credential reset.'); }} className="text-[11px] text-sky-400 hover:underline">
                      Forgot password?
                    </a>
                  </div>
                  <input
                    type="password"
                    value={loginPassword}
                    onChange={e => setLoginPassword(e.target.value)}
                    placeholder="••••••••"
                    autoComplete="current-password"
                    className={`w-full px-3.5 py-2.5 rounded-lg border text-sm font-mono outline-none transition-all ${
                      isDark 
                        ? 'bg-black/40 border-white/15 text-white focus:border-sky-400 focus:ring-2 focus:ring-sky-400/20' 
                        : 'bg-white/90 border-slate-300 text-black focus:border-sky-600 focus:ring-2 focus:ring-sky-600/20'
                    }`}
                  />
                </div>

                <div className="flex items-center justify-between text-xs text-slate-400">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input type="checkbox" defaultChecked className="rounded border-slate-600 text-sky-500 focus:ring-0" />
                    <span>Keep me signed in</span>
                  </label>
                </div>

                <button
                  type="submit"
                  disabled={loginLoading}
                  className="w-full py-2.5 px-4 rounded-lg bg-sky-500 hover:bg-sky-400 text-slate-950 font-mono font-bold text-sm shadow-lg shadow-sky-500/20 transition-all cursor-pointer disabled:opacity-50"
                >
                  {loginLoading ? 'Authenticating...' : 'Sign in to Console →'}
                </button>
              </form>

              {/* Quick Demo Credentials */}
              <div className="mt-6 pt-4 border-t border-white/10 text-center">
                <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider block mb-2">
                  Demo Evaluation Credentials
                </span>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => fillDemoCredentials('admin')}
                    className={`flex-1 py-1.5 px-2 rounded-md border text-[11px] font-mono transition-colors ${
                      isDark ? 'bg-white/5 hover:bg-white/15 border-white/10 text-slate-300' : 'bg-slate-100 hover:bg-slate-200 border-slate-300 text-slate-700'
                    }`}
                  >
                    👑 Admin (MoSPI Lead)
                  </button>
                  <button
                    type="button"
                    onClick={() => fillDemoCredentials('analyst')}
                    className={`flex-1 py-1.5 px-2 rounded-md border text-[11px] font-mono transition-colors ${
                      isDark ? 'bg-white/5 hover:bg-white/15 border-white/10 text-slate-300' : 'bg-slate-100 hover:bg-slate-200 border-slate-300 text-slate-700'
                    }`}
                  >
                    📊 Risk Analyst
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* ================= SIGN UP TAB ================= */}
          {activeTab === 'signup' && (
            <div>
              {/* Step 1: Details */}
              {signupStep === 1 && (
                <div>
                  <div className="mb-4">
                    <h1 className="text-xl sm:text-2xl font-serif font-bold tracking-tight mb-1">
                      Request access
                    </h1>
                    <p className="text-xs text-slate-400">
                      Register with your official ministry credentials. Access is role-governed.
                    </p>
                  </div>

                  {signupError && (
                    <div className="mb-4 p-3 rounded-lg bg-rose-500/15 border border-rose-500/30 text-rose-400 text-xs font-medium">
                      {signupError}
                    </div>
                  )}

                  <form onSubmit={handleSignupSubmit} className="space-y-3">
                    <div>
                      <label className="block text-xs font-mono text-slate-300 mb-1">
                        Full Name
                      </label>
                      <input
                        type="text"
                        value={fullName}
                        onChange={e => setFullName(e.target.value)}
                        placeholder="As per official records"
                        className={`w-full px-3 py-2 rounded-lg border text-sm font-mono outline-none ${
                          isDark ? 'bg-black/40 border-white/15 text-white' : 'bg-white border-slate-300 text-black'
                        }`}
                      />
                    </div>

                    <div>
                      <label className="block text-xs font-mono text-slate-300 mb-1">
                        Official Email
                      </label>
                      <input
                        type="email"
                        value={signupEmail}
                        onChange={e => setSignupEmail(e.target.value)}
                        placeholder="name@ministry.gov.in"
                        className={`w-full px-3 py-2 rounded-lg border text-sm font-mono outline-none ${
                          isDark ? 'bg-black/40 border-white/15 text-white' : 'bg-white border-slate-300 text-black'
                        }`}
                      />
                    </div>

                    <div className="grid grid-cols-2 gap-2">
                      <div>
                        <label className="block text-xs font-mono text-slate-300 mb-1">
                          Ministry / Dept
                        </label>
                        <select
                          value={ministryId}
                          onChange={e => setMinistryId(e.target.value ? Number(e.target.value) : '')}
                          className={`w-full px-2.5 py-2 rounded-lg border text-xs font-mono outline-none ${
                            isDark ? 'bg-[#0E192E] border-white/15 text-white' : 'bg-white border-slate-300 text-black'
                          }`}
                        >
                          <option value="">Select Ministry</option>
                          {ministries.map(m => (
                            <option key={m.id} value={m.id}>{m.name}</option>
                          ))}
                        </select>
                      </div>

                      <div>
                        <label className="block text-xs font-mono text-slate-300 mb-1">
                          Designation
                        </label>
                        <input
                          type="text"
                          value={designation}
                          onChange={e => setDesignation(e.target.value)}
                          placeholder="e.g. Chief Engineer"
                          className={`w-full px-3 py-2 rounded-lg border text-sm font-mono outline-none ${
                            isDark ? 'bg-black/40 border-white/15 text-white' : 'bg-white border-slate-300 text-black'
                          }`}
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-2">
                      <div>
                        <label className="block text-xs font-mono text-slate-300 mb-1">
                          Password
                        </label>
                        <input
                          type="password"
                          value={signupPassword}
                          onChange={e => setSignupPassword(e.target.value)}
                          placeholder="Min. 8 chars"
                          className={`w-full px-3 py-2 rounded-lg border text-sm font-mono outline-none ${
                            isDark ? 'bg-black/40 border-white/15 text-white' : 'bg-white border-slate-300 text-black'
                          }`}
                        />
                      </div>

                      <div>
                        <label className="block text-xs font-mono text-slate-300 mb-1">
                          Confirm
                        </label>
                        <input
                          type="password"
                          value={confirmPassword}
                          onChange={e => setConfirmPassword(e.target.value)}
                          placeholder="Re-enter"
                          className={`w-full px-3 py-2 rounded-lg border text-sm font-mono outline-none ${
                            isDark ? 'bg-black/40 border-white/15 text-white' : 'bg-white border-slate-300 text-black'
                          }`}
                        />
                      </div>
                    </div>

                    <div className="space-y-2 pt-1 text-[11px] text-slate-400">
                      <label className="flex items-start gap-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={termsAccepted}
                          onChange={e => setTermsAccepted(e.target.checked)}
                          className="mt-0.5 rounded border-slate-600 text-sky-500"
                        />
                        <span>
                          I agree to the{' '}
                          <button
                            type="button"
                            onClick={() => { setShowPolicyModal(true); setPolicyTab('terms'); }}
                            className="text-sky-400 hover:underline"
                          >
                            Terms &amp; Conditions and Privacy Policy
                          </button>.
                        </span>
                      </label>

                      <label className="flex items-start gap-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={aiAckAccepted}
                          onChange={e => setAiAckAccepted(e.target.checked)}
                          className="mt-0.5 rounded border-slate-600 text-sky-500"
                        />
                        <span>
                          I acknowledge project parameters will be evaluated by{' '}
                          <button
                            type="button"
                            onClick={() => { setShowPolicyModal(true); setPolicyTab('privacy'); }}
                            className="text-sky-400 hover:underline"
                          >
                            AI/ML predictive systems
                          </button>{' '}
                          for risk scoring.
                        </span>
                      </label>
                    </div>

                    <button
                      type="submit"
                      disabled={signupLoading}
                      className="w-full py-2.5 px-4 mt-2 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-mono font-bold text-sm shadow-lg shadow-emerald-500/20 transition-all cursor-pointer disabled:opacity-50"
                    >
                      {signupLoading ? 'Registering...' : 'Request Access & Verify OTP →'}
                    </button>
                  </form>
                </div>
              )}

              {/* Step 2: 6-Digit OTP */}
              {signupStep === 2 && (
                <div>
                  <button
                    onClick={() => setSignupStep(1)}
                    className="text-xs text-slate-400 hover:text-white mb-3 flex items-center gap-1 cursor-pointer font-mono"
                  >
                    ← Back to form
                  </button>

                  <div className="mb-4">
                    <h2 className="text-xl font-serif font-bold tracking-tight mb-1">
                      Verify it's you
                    </h2>
                    <p className="text-xs text-slate-400">
                      We've dispatched a 6-digit code to <strong className="text-white">{signupEmail}</strong>. Enter it below to complete registration.
                    </p>
                  </div>

                  {otpError && (
                    <div className="mb-4 p-3 rounded-lg bg-rose-500/15 border border-rose-500/30 text-rose-400 text-xs font-medium">
                      {otpError}
                    </div>
                  )}

                  {/* 6-box input */}
                  <div className="flex justify-between gap-2 my-5">
                    {otpDigits.map((digit, idx) => (
                      <input
                        key={idx}
                        ref={el => (otpInputsRef.current[idx] = el)}
                        type="text"
                        inputMode="numeric"
                        maxLength={1}
                        value={digit}
                        onChange={e => handleOtpChange(idx, e.target.value)}
                        onKeyDown={e => handleOtpKeyDown(idx, e)}
                        className={`w-11 h-12 text-center text-xl font-mono font-bold rounded-lg border outline-none transition-all ${
                          isDark 
                            ? 'bg-black/50 border-white/20 text-white focus:border-sky-400 focus:ring-2 focus:ring-sky-400/20' 
                            : 'bg-white border-slate-300 text-black focus:border-sky-600 focus:ring-2 focus:ring-sky-600/20'
                        }`}
                      />
                    ))}
                  </div>

                  <div className="flex items-center justify-between text-xs text-slate-400 mb-5">
                    {canResend ? (
                      <button
                        type="button"
                        onClick={handleResendOtp}
                        className="text-sky-400 hover:underline font-mono font-medium cursor-pointer"
                      >
                        Resend verification code
                      </button>
                    ) : (
                      <span className="font-mono">
                        Resend code in <strong className="text-white">{resendTimer}s</strong>
                      </span>
                    )}
                  </div>

                  <button
                    type="button"
                    onClick={handleVerifyOtp}
                    disabled={otpLoading || otpDigits.join('').length !== 6}
                    className="w-full py-2.5 px-4 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-mono font-bold text-sm shadow-lg shadow-emerald-500/20 transition-all cursor-pointer disabled:opacity-50"
                  >
                    {otpLoading ? 'Verifying...' : 'Verify & Activate Account →'}
                  </button>
                </div>
              )}

              {/* Step 3: Success Confirmation */}
              {signupStep === 3 && (
                <div className="text-center py-6">
                  <div className="w-14 h-14 mx-auto mb-3 rounded-full bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400 text-2xl">
                    ✓
                  </div>
                  <h2 className="text-xl font-serif font-bold tracking-tight mb-2">
                    Account Verified
                  </h2>
                  <p className="text-xs text-slate-400 mb-6 leading-relaxed">
                    Your official identity has been authenticated and provisioned. You may now sign in using your credentials.
                  </p>
                  <button
                    type="button"
                    onClick={() => { setActiveTab('signin'); setLoginEmail(signupEmail); }}
                    className="w-full py-2.5 px-4 rounded-lg bg-sky-500 hover:bg-sky-400 text-slate-950 font-mono font-bold text-sm shadow-lg shadow-sky-500/20 transition-all cursor-pointer"
                  >
                    Proceed to Sign in →
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </main>

      {/* ---------------- Bottom: Active Corridor Badge & Slide Indicators ---------------- */}
      <footer className="relative z-10 flex flex-col sm:flex-row items-center justify-between gap-4 mt-6">
        {/* Left: Active Corridor Badge */}
        <div className={`flex items-center gap-2.5 px-3.5 py-1.5 rounded-full border backdrop-blur-md shadow-lg ${
          isDark ? 'bg-[#0E192E]/70 border-white/15 text-slate-200' : 'bg-white/80 border-slate-300 text-slate-800'
        }`}>
          <span className="w-2 h-2 rounded-full bg-sky-400 animate-pulse shadow-[0_0_8px_#38bdf8]" />
          <span className="text-[11px] font-mono">
            {SLIDES[currentSlide]?.label}
          </span>
        </div>

        {/* Right: Dot Navigation */}
        <div className="flex items-center gap-2">
          {SLIDES.map((_, idx) => (
            <button
              key={idx}
              onClick={() => setCurrentSlide(idx)}
              aria-label={`Slide ${idx + 1}`}
              className={`h-1.5 rounded-full transition-all duration-300 cursor-pointer ${
                currentSlide === idx 
                  ? (isDark ? 'w-8 bg-sky-400' : 'w-8 bg-sky-600') 
                  : (isDark ? 'w-4 bg-white/30 hover:bg-white/50' : 'w-4 bg-black/20 hover:bg-black/40')
              }`}
            />
          ))}
        </div>
      </footer>

      {/* ---------------- Terms & Privacy Policy Modal ---------------- */}
      {showPolicyModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <div className={`w-full max-w-lg rounded-2xl border p-6 backdrop-blur-xl shadow-2xl ${
            isDark ? 'bg-[#0A1222] border-white/20 text-slate-200' : 'bg-white border-slate-300 text-slate-800'
          }`}>
            <div className="flex justify-between items-center pb-3 border-b border-white/10 mb-4">
              <h3 className="font-serif text-lg font-bold">
                Governance &amp; Privacy Policy
              </h3>
              <button
                onClick={() => setShowPolicyModal(false)}
                className="text-slate-400 hover:text-white text-xl cursor-pointer"
              >
                ×
              </button>
            </div>

            <div className="flex gap-2 mb-4 border-b border-white/10 pb-2 text-xs font-mono">
              <button
                onClick={() => setPolicyTab('terms')}
                className={`pb-1 border-b-2 transition-colors ${
                  policyTab === 'terms' ? 'border-sky-400 text-sky-400 font-bold' : 'border-transparent text-slate-400'
                }`}
              >
                Terms &amp; Conditions
              </button>
              <button
                onClick={() => setPolicyTab('privacy')}
                className={`pb-1 border-b-2 transition-colors ${
                  policyTab === 'privacy' ? 'border-sky-400 text-sky-400 font-bold' : 'border-transparent text-slate-400'
                }`}
              >
                AI/ML Privacy Policy
              </button>
            </div>

            <div className="max-h-64 overflow-y-auto text-xs space-y-3 text-slate-400 pr-2">
              {policyTab === 'terms' ? (
                <>
                  <p><strong>1. Acceptance of Terms:</strong> By logging into the PAIMANA platform, you affirm authorization as an accredited officer or analyst of the Government of India or affiliated implementing authority.</p>
                  <p><strong>2. Authorized Usage:</strong> Analytical models, forecasts, and early-warning alerts are designed for decision-support and proactive risk mitigation across major infrastructure portfolios.</p>
                  <p><strong>3. Confidentiality:</strong> All contractor milestone evaluations and financial disbursement data remain protected under official data governance protocols.</p>
                </>
              ) : (
                <>
                  <p><strong>1. Predictive Modeling Notice:</strong> Project telemetry, milestone completion rates, and physical-to-financial disparity metrics are analyzed using XGBoost machine learning regressors and SHAP explainability engines.</p>
                  <p><strong>2. Diagnostic Assurance:</strong> AI-generated statutory directives represent empirical recommendations based on past milestone hysteresis curves to support human executive decision-making.</p>
                </>
              )}
            </div>

            <div className="mt-5 pt-3 border-t border-white/10 flex justify-end">
              <button
                onClick={() => setShowPolicyModal(false)}
                className="px-4 py-1.5 rounded-lg bg-white/10 hover:bg-white/20 text-xs font-mono font-medium cursor-pointer"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
