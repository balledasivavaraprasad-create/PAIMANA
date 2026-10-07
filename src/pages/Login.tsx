import React, { useState, useEffect, useRef, useMemo } from 'react';
import { useTheme } from '../hooks/useTheme';
import { InteractiveLivingBackground } from '../components/InteractiveLivingBackground';
import {
  fetchMinistries, loginUser, registerUser, verifyOtp, resendOtp,
  fetchPublicRiskOverview, MinistryItem, AuthResponse, PublicRiskOverview
} from '../lib/api';

interface LoginProps {
  onLoginSuccess: (authData: AuthResponse) => void;
  onNavigateToLanding?: () => void;
}

export default function Login({ onLoginSuccess, onNavigateToLanding }: LoginProps) {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === 'dark';

  // Tab & Flow state
  const [activeTab, setActiveTab] = useState<'signin' | 'signup'>('signin');
  const [signupStep, setSignupStep] = useState<1 | 2 | 3>(1);

  // Form states - Sign In
  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [showLoginPassword, setShowLoginPassword] = useState(false);
  const [loginError, setLoginError] = useState('');
  const [loginLoading, setLoginLoading] = useState(false);

  // Form states - Sign Up
  const [fullName, setFullName] = useState('');
  const [signupEmail, setSignupEmail] = useState('');
  const [ministryId, setMinistryId] = useState<number | ''>('');
  const [designation, setDesignation] = useState('');
  const [signupPassword, setSignupPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showSignupPassword, setShowSignupPassword] = useState(false);
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

  // Dynamic Risk & Statistics Overview from Live Database
  const [publicOverview, setPublicOverview] = useState<PublicRiskOverview | null>(null);

  // Ministries list
  const [ministries, setMinistries] = useState<MinistryItem[]>([]);

  // Policy Modal
  const [showPolicyModal, setShowPolicyModal] = useState(false);
  const [policyTab, setPolicyTab] = useState<'terms' | 'privacy'>('terms');

  const otpInputsRef = useRef<(HTMLInputElement | null)[]>([]);

  // Real-time Password Strength Analysis
  const passwordCriteria = useMemo(() => {
    const hasMinLength = signupPassword.length >= 8;
    const hasUpper = /[A-Z]/.test(signupPassword);
    const hasLower = /[a-z]/.test(signupPassword);
    const hasDigit = /[0-9]/.test(signupPassword);
    const hasSpecial = /[^A-Za-z0-9]/.test(signupPassword);
    const score = [hasMinLength, (hasUpper && hasLower), hasDigit, hasSpecial].filter(Boolean).length;
    return {
      hasMinLength,
      hasUpper,
      hasLower,
      hasDigit,
      hasSpecial,
      score,
      isStrong: hasMinLength && hasUpper && hasLower && hasDigit && hasSpecial
    };
  }, [signupPassword]);

  // Fetch live sovereign metrics and ministries from database
  useEffect(() => {
    fetchMinistries().then(setMinistries).catch(console.warn);
    fetchPublicRiskOverview().then(setPublicOverview).catch(console.warn);
  }, []);

  // Resend OTP countdown
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

  const sanitizeErrorMessage = (err: any, fallback: string): string => {
    if (!err) return fallback;
    const raw = typeof err === 'string' ? err : (err.message || fallback);
    const lower = String(raw).toLowerCase();
    if (
      lower.includes('load failed') ||
      lower.includes('failed to fetch') ||
      lower.includes('networkerror') ||
      lower.includes('typeerror') ||
      lower.includes('network request failed') ||
      lower.includes('not found') ||
      lower.includes('404') ||
      lower.includes('cannot post') ||
      lower.includes('cannot get') ||
      lower.includes('econnrefused') ||
      lower.includes('cors')
    ) {
      return 'Connection to authentication service was interrupted. Please check credentials or retry.';
    }
    return raw;
  };

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
      setLoginError(sanitizeErrorMessage(err, 'Authentication failed. Please check credentials.'));
    } finally {
      setLoginLoading(false);
    }
  };

  // Fast 1-click Demo Fill
  const fillDemoCredentials = async (role: 'admin' | 'siva', autoSubmit = false) => {
    setLoginError('');
    let email = '';
    let password = '';
    if (role === 'admin') {
      email = 'admin';
      password = 'paimana2026';
    } else {
      email = 'balledasivavaraprasad@gmail.com';
      password = 'paimana2026';
    }
    setLoginEmail(email);
    setLoginPassword(password);

    if (autoSubmit) {
      setLoginLoading(true);
      try {
        const data = await loginUser({ email, password });
        onLoginSuccess(data);
      } catch (err: any) {
        setLoginError(sanitizeErrorMessage(err, 'Authentication failed. Please check credentials.'));
      } finally {
        setLoginLoading(false);
      }
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
    if (!passwordCriteria.isStrong) {
      setSignupError('Please provide a strong password meeting all institutional security requirements.');
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
      setSignupError(sanitizeErrorMessage(err, 'Registration failed.'));
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
      setOtpError(sanitizeErrorMessage(err, 'Invalid verification code.'));
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
      setOtpError(sanitizeErrorMessage(err, 'Failed to resend verification code.'));
    }
  };

  return (
    <div
      style={{
        position: 'relative',
        minHeight: '100vh',
        width: '100%',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '32px 16px',
        overflowX: 'hidden',
      }}
    >
      {/* Living Atmospheric Orange Aura Background */}
      <InteractiveLivingBackground isDark={isDark} />

      {/* Floating Top Bar (Matching Landing Page & Header Style) */}
      <nav
        className="login-floating-topbar"
        style={{
          position: 'fixed',
          top: '20px',
          left: '50%',
          transform: 'translateX(-50%)',
          width: 'max-content',
          maxWidth: 'calc(100vw - 32px)',
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          padding: '6px 14px',
          borderRadius: '9999px',
          backgroundColor: 'rgba(18, 19, 20, 0.94)',
          backdropFilter: 'blur(24px)',
          WebkitBackdropFilter: 'blur(24px)',
          border: '1px solid rgba(255, 255, 255, 0.16)',
          boxShadow: '0 20px 50px -10px rgba(0, 0, 0, 0.45)',
          zIndex: 100,
        }}
      >
        {/* Brand Mark */}
        <div
          onClick={() => {
            if (onNavigateToLanding) onNavigateToLanding();
            else window.location.hash = '';
          }}
          title="Return to Public Landing Page"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            cursor: 'pointer',
          }}
        >
          <div
            style={{
              width: '24px',
              height: '24px',
              borderRadius: '7px',
              backgroundColor: '#FFFFFF',
              color: '#121314',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '11px',
              fontWeight: 900,
            }}
          >
            ▲
          </div>
          <span style={{ fontSize: '14px', letterSpacing: '-0.02em' }}>
            <span style={{ fontWeight: 800, color: '#FFFFFF' }}>InfraBuild</span>{' '}
            <span style={{ fontSize: '12px', fontWeight: 700, color: '#38BDF8' }}>AI</span>
          </span>
        </div>

        <div style={{ width: '1px', height: '16px', backgroundColor: 'rgba(255, 255, 255, 0.15)' }} />

        {/* Return to Showcase Button */}
        <button
          type="button"
          className="public-showcase-btn"
          onClick={() => {
            if (onNavigateToLanding) onNavigateToLanding();
            else window.location.hash = '';
          }}
          style={{
            backgroundColor: 'transparent',
            border: 'none',
            color: '#FFFFFF',
            fontSize: '12px',
            fontWeight: 700,
            cursor: 'pointer',
            padding: '4px 10px',
            borderRadius: '9999px',
            transition: 'opacity 0.2s',
          }}
          onMouseEnter={(e) => (e.currentTarget.style.opacity = '1')}
          onMouseLeave={(e) => (e.currentTarget.style.opacity = '0.9')}
        >
          <span className="public-showcase-btn" style={{ color: '#FFFFFF', fontWeight: 700 }}>← Public Showcase</span>
        </button>

        <div style={{ width: '1px', height: '16px', backgroundColor: 'rgba(255, 255, 255, 0.15)' }} />

        {/* Theme Toggle */}
        <button
          type="button"
          onClick={toggleTheme}
          title={isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
          style={{
            width: '28px',
            height: '28px',
            borderRadius: '50%',
            backgroundColor: 'rgba(255, 255, 255, 0.08)',
            border: '1px solid rgba(255, 255, 255, 0.14)',
            color: '#FFFFFF',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
            fontSize: '12px',
          }}
        >
          {isDark ? '🌙' : '☀️'}
        </button>
      </nav>

      {/* Main Authentication Card */}
      <div
        style={{
          position: 'relative',
          zIndex: 10,
          width: '100%',
          maxWidth: '520px',
          marginTop: '70px',
          borderRadius: '28px',
          backgroundColor: isDark ? 'rgba(16, 18, 22, 0.90)' : 'rgba(255, 255, 255, 0.94)',
          backdropFilter: 'blur(28px)',
          WebkitBackdropFilter: 'blur(28px)',
          border: isDark ? '1px solid rgba(255, 255, 255, 0.14)' : '1px solid #E5E3DC',
          boxShadow: isDark ? '0 28px 70px rgba(0, 0, 0, 0.75)' : '0 20px 60px -10px rgba(0, 0, 0, 0.10)',
          padding: '36px 32px',
          transition: 'all 0.3s cubic-bezier(0.16, 1, 0.3, 1)',
        }}
      >
        {/* Header Emblem & Title */}
        <div style={{ textAlign: 'center', marginBottom: '28px' }}>
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '4px 12px',
              borderRadius: '9999px',
              backgroundColor: isDark ? 'rgba(99, 102, 241, 0.12)' : 'rgba(2, 132, 199, 0.08)',
              border: isDark ? '1px solid rgba(99, 102, 241, 0.3)' : '1px solid rgba(2, 132, 199, 0.2)',
              color: isDark ? '#A5B4FC' : '#0284C7',
              fontSize: '10.5px',
              fontWeight: 800,
              textTransform: 'uppercase',
              letterSpacing: '0.08em',
              marginBottom: '14px',
            }}
          >
            <span>●</span>
            <span>SOVEREIGN TELEMETRY GATEWAY</span>
          </div>

          <h2
            style={{
              fontSize: '26px',
              fontWeight: 800,
              letterSpacing: '-0.03em',
              color: isDark ? '#FFFFFF' : '#121314',
              margin: '0 0 8px 0',
            }}
          >
            Official Authentication Portal
          </h2>
          <p
            style={{
              fontSize: '13px',
              color: isDark ? 'rgba(255, 255, 255, 0.65)' : '#64748B',
              margin: 0,
              lineHeight: 1.5,
            }}
          >
            Ministry of Statistics & Programme Implementation (MoSPI) • Institutional Decision Support
          </p>
        </div>

        {/* Tab Switcher: Sign In vs Sign Up */}
        <div
          style={{
            display: 'flex',
            backgroundColor: isDark ? 'rgba(255, 255, 255, 0.06)' : '#F1F5F9',
            padding: '4px',
            borderRadius: '9999px',
            marginBottom: '24px',
            border: isDark ? '1px solid rgba(255, 255, 255, 0.1)' : '1px solid #E2E8F0',
          }}
        >
          <button
            type="button"
            onClick={() => {
              setActiveTab('signin');
              setLoginError('');
            }}
            style={{
              flex: 1,
              padding: '8px 16px',
              borderRadius: '9999px',
              border: 'none',
              backgroundColor: activeTab === 'signin' ? (isDark ? '#FFFFFF' : '#121314') : 'transparent',
              color: activeTab === 'signin' ? (isDark ? '#070A12' : '#FFFFFF') : (isDark ? 'rgba(255,255,255,0.7)' : '#64748B'),
              fontSize: '12.5px',
              fontWeight: activeTab === 'signin' ? 700 : 500,
              cursor: 'pointer',
              transition: 'all 0.2s ease',
              boxShadow: activeTab === 'signin' ? '0 2px 10px rgba(0,0,0,0.15)' : 'none',
            }}
          >
            Official Sign In
          </button>
          <button
            type="button"
            onClick={() => {
              setActiveTab('signup');
              setSignupError('');
            }}
            style={{
              flex: 1,
              padding: '8px 16px',
              borderRadius: '9999px',
              border: 'none',
              backgroundColor: activeTab === 'signup' ? (isDark ? '#FFFFFF' : '#121314') : 'transparent',
              color: activeTab === 'signup' ? (isDark ? '#070A12' : '#FFFFFF') : (isDark ? 'rgba(255,255,255,0.7)' : '#64748B'),
              fontSize: '12.5px',
              fontWeight: activeTab === 'signup' ? 700 : 500,
              cursor: 'pointer',
              transition: 'all 0.2s ease',
              boxShadow: activeTab === 'signup' ? '0 2px 10px rgba(0,0,0,0.15)' : 'none',
            }}
          >
            Register Personnel
          </button>
        </div>

        {/* TAB 1: SIGN IN */}
        {activeTab === 'signin' && (
          <div>
            {/* Quick 1-Click Demo Fill Buttons */}
            <div style={{ marginBottom: '20px' }}>
              <div
                style={{
                  fontSize: '10.5px',
                  fontWeight: 800,
                  textTransform: 'uppercase',
                  letterSpacing: '0.06em',
                  color: isDark ? 'rgba(255, 255, 255, 0.5)' : '#94A3B8',
                  marginBottom: '8px',
                }}
              >
                Fast 1-Click Demo Access:
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                <button
                  type="button"
                  onClick={() => fillDemoCredentials('admin', false)}
                  style={{
                    padding: '10px 14px',
                    borderRadius: '12px',
                    backgroundColor: isDark ? 'rgba(255, 255, 255, 0.06)' : '#F8FAFC',
                    border: isDark ? '1px solid rgba(255, 255, 255, 0.12)' : '1px solid #E2E8F0',
                    color: isDark ? '#FFFFFF' : '#1E293B',
                    fontSize: '12px',
                    fontWeight: 700,
                    cursor: 'pointer',
                    textAlign: 'left',
                    transition: 'all 0.2s ease',
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.borderColor = '#0284C7')}
                  onMouseLeave={(e) => (e.currentTarget.style.borderColor = isDark ? 'rgba(255, 255, 255, 0.12)' : '#E2E8F0')}
                >
                  <div style={{ color: '#0284C7', fontSize: '11px', fontWeight: 600 }}>MoSPI Director</div>
                  <div>Admin Account</div>
                </button>

                <button
                  type="button"
                  onClick={() => fillDemoCredentials('siva', false)}
                  style={{
                    padding: '10px 14px',
                    borderRadius: '12px',
                    backgroundColor: isDark ? 'rgba(255, 255, 255, 0.06)' : '#F8FAFC',
                    border: isDark ? '1px solid rgba(255, 255, 255, 0.12)' : '1px solid #E2E8F0',
                    color: isDark ? '#FFFFFF' : '#1E293B',
                    fontSize: '12px',
                    fontWeight: 700,
                    cursor: 'pointer',
                    textAlign: 'left',
                    transition: 'all 0.2s ease',
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.borderColor = '#10B981')}
                  onMouseLeave={(e) => (e.currentTarget.style.borderColor = isDark ? 'rgba(255, 255, 255, 0.12)' : '#E2E8F0')}
                >
                  <div style={{ color: '#10B981', fontSize: '11px', fontWeight: 600 }}>Project Officer</div>
                  <div>Ministry User</div>
                </button>
              </div>
            </div>

            {/* Error Message */}
            {loginError && (
              <div
                style={{
                  padding: '10px 14px',
                  borderRadius: '12px',
                  backgroundColor: 'rgba(239, 68, 68, 0.12)',
                  border: '1px solid rgba(239, 68, 68, 0.3)',
                  color: '#EF4444',
                  fontSize: '12px',
                  fontWeight: 600,
                  marginBottom: '16px',
                }}
              >
                ⚠️ {loginError}
              </div>
            )}

            {/* Login Form */}
            <form onSubmit={handleLoginSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div>
                <label
                  style={{
                    display: 'block',
                    fontSize: '11.5px',
                    fontWeight: 700,
                    color: isDark ? '#E5E5E5' : '#334155',
                    marginBottom: '6px',
                  }}
                >
                  Official Email or Username
                </label>
                <input
                  type="text"
                  value={loginEmail}
                  onChange={(e) => setLoginEmail(e.target.value)}
                  placeholder="e.g. admin or official.officer@nic.in"
                  required
                  style={{
                    width: '100%',
                    padding: '11px 14px',
                    borderRadius: '12px',
                    backgroundColor: isDark ? 'rgba(255, 255, 255, 0.05)' : '#FFFFFF',
                    border: isDark ? '1px solid rgba(255, 255, 255, 0.15)' : '1px solid #CBD5E1',
                    color: isDark ? '#FFFFFF' : '#121314',
                    fontSize: '13px',
                    outline: 'none',
                    transition: 'border-color 0.2s',
                    boxSizing: 'border-box',
                  }}
                  onFocus={(e) => (e.currentTarget.style.borderColor = '#0284C7')}
                  onBlur={(e) => (e.currentTarget.style.borderColor = isDark ? 'rgba(255, 255, 255, 0.15)' : '#CBD5E1')}
                />
              </div>

              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                  <label
                    style={{
                      fontSize: '11.5px',
                      fontWeight: 700,
                      color: isDark ? '#E5E5E5' : '#334155',
                    }}
                  >
                    Security Passkey / Password
                  </label>
                  <button
                    type="button"
                    onClick={() => setShowLoginPassword(!showLoginPassword)}
                    style={{
                      background: 'none',
                      border: 'none',
                      color: '#0284C7',
                      fontSize: '11px',
                      fontWeight: 600,
                      cursor: 'pointer',
                      padding: 0,
                    }}
                  >
                    {showLoginPassword ? 'Hide' : 'Show'}
                  </button>
                </div>
                <input
                  type={showLoginPassword ? 'text' : 'password'}
                  value={loginPassword}
                  onChange={(e) => setLoginPassword(e.target.value)}
                  placeholder="••••••••••••"
                  required
                  style={{
                    width: '100%',
                    padding: '11px 14px',
                    borderRadius: '12px',
                    backgroundColor: isDark ? 'rgba(255, 255, 255, 0.05)' : '#FFFFFF',
                    border: isDark ? '1px solid rgba(255, 255, 255, 0.15)' : '1px solid #CBD5E1',
                    color: isDark ? '#FFFFFF' : '#121314',
                    fontSize: '13px',
                    outline: 'none',
                    transition: 'border-color 0.2s',
                    boxSizing: 'border-box',
                  }}
                  onFocus={(e) => (e.currentTarget.style.borderColor = '#0284C7')}
                  onBlur={(e) => (e.currentTarget.style.borderColor = isDark ? 'rgba(255, 255, 255, 0.15)' : '#CBD5E1')}
                />
              </div>

              <button
                type="submit"
                disabled={loginLoading}
                style={{
                  marginTop: '8px',
                  padding: '13px 20px',
                  borderRadius: '14px',
                  backgroundColor: isDark ? '#FFFFFF' : '#121314',
                  color: isDark ? '#070A12' : '#FFFFFF',
                  border: 'none',
                  fontSize: '13.5px',
                  fontWeight: 800,
                  cursor: loginLoading ? 'wait' : 'pointer',
                  boxShadow: '0 8px 24px rgba(0, 0, 0, 0.2)',
                  transition: 'all 0.2s ease',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                }}
              >
                <span>{loginLoading ? 'Verifying Credentials...' : 'Sign In to Sovereign Gateway →'}</span>
              </button>
            </form>
          </div>
        )}

        {/* TAB 2: SIGN UP WIZARD */}
        {activeTab === 'signup' && (
          <div>
            {/* Step Wizard Indicator */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', marginBottom: '20px' }}>
              {[
                { s: 1, label: 'Details' },
                { s: 2, label: 'Verification' },
                { s: 3, label: 'Provisioned' },
              ].map((item) => (
                <div key={item.s} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <div
                    style={{
                      width: '22px',
                      height: '22px',
                      borderRadius: '50%',
                      backgroundColor: signupStep >= item.s ? '#0284C7' : (isDark ? 'rgba(255,255,255,0.1)' : '#E2E8F0'),
                      color: signupStep >= item.s ? '#FFFFFF' : (isDark ? 'rgba(255,255,255,0.5)' : '#94A3B8'),
                      fontSize: '11px',
                      fontWeight: 800,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    {signupStep > item.s ? '✓' : item.s}
                  </div>
                  <span style={{ fontSize: '11px', fontWeight: 600, color: signupStep === item.s ? (isDark ? '#FFFFFF' : '#121314') : '#94A3B8' }}>
                    {item.label}
                  </span>
                  {item.s < 3 && <span style={{ opacity: 0.3, margin: '0 4px' }}>–</span>}
                </div>
              ))}
            </div>

            {signupError && (
              <div
                style={{
                  padding: '10px 14px',
                  borderRadius: '12px',
                  backgroundColor: 'rgba(239, 68, 68, 0.12)',
                  border: '1px solid rgba(239, 68, 68, 0.3)',
                  color: '#EF4444',
                  fontSize: '12px',
                  fontWeight: 600,
                  marginBottom: '16px',
                }}
              >
                ⚠️ {signupError}
              </div>
            )}

            {/* STEP 1: Registration Form */}
            {signupStep === 1 && (
              <form onSubmit={handleSignupSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '11.5px', fontWeight: 700, color: isDark ? '#E5E5E5' : '#334155', marginBottom: '4px' }}>
                    Full Official Name
                  </label>
                  <input
                    type="text"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="e.g. Dr. Ramesh Kumar"
                    required
                    style={{
                      width: '100%',
                      padding: '10px 14px',
                      borderRadius: '12px',
                      backgroundColor: isDark ? 'rgba(255, 255, 255, 0.05)' : '#FFFFFF',
                      border: isDark ? '1px solid rgba(255, 255, 255, 0.15)' : '1px solid #CBD5E1',
                      color: isDark ? '#FFFFFF' : '#121314',
                      fontSize: '13px',
                      outline: 'none',
                      boxSizing: 'border-box',
                    }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '11.5px', fontWeight: 700, color: isDark ? '#E5E5E5' : '#334155', marginBottom: '4px' }}>
                    Official NIC / Ministry Email
                  </label>
                  <input
                    type="email"
                    value={signupEmail}
                    onChange={(e) => setSignupEmail(e.target.value)}
                    placeholder="officer@nic.in or your.email@domain.com"
                    required
                    style={{
                      width: '100%',
                      padding: '10px 14px',
                      borderRadius: '12px',
                      backgroundColor: isDark ? 'rgba(255, 255, 255, 0.05)' : '#FFFFFF',
                      border: isDark ? '1px solid rgba(255, 255, 255, 0.15)' : '1px solid #CBD5E1',
                      color: isDark ? '#FFFFFF' : '#121314',
                      fontSize: '13px',
                      outline: 'none',
                      boxSizing: 'border-box',
                    }}
                  />
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '11.5px', fontWeight: 700, color: isDark ? '#E5E5E5' : '#334155', marginBottom: '4px' }}>
                      Ministry / Department
                    </label>
                    <select
                      value={ministryId}
                      onChange={(e) => setMinistryId(e.target.value ? Number(e.target.value) : '')}
                      style={{
                        width: '100%',
                        padding: '10px 12px',
                        borderRadius: '12px',
                        backgroundColor: isDark ? 'rgba(255, 255, 255, 0.05)' : '#FFFFFF',
                        border: isDark ? '1px solid rgba(255, 255, 255, 0.15)' : '1px solid #CBD5E1',
                        color: isDark ? '#FFFFFF' : '#121314',
                        fontSize: '12px',
                        outline: 'none',
                        boxSizing: 'border-box',
                      }}
                    >
                      <option value="" style={{ color: '#000' }}>Select Ministry...</option>
                      {ministries.map((m) => (
                        <option key={m.id} value={m.id} style={{ color: '#000' }}>{m.name}</option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label style={{ display: 'block', fontSize: '11.5px', fontWeight: 700, color: isDark ? '#E5E5E5' : '#334155', marginBottom: '4px' }}>
                      Designation
                    </label>
                    <input
                      type="text"
                      value={designation}
                      onChange={(e) => setDesignation(e.target.value)}
                      placeholder="e.g. Project Director"
                      style={{
                        width: '100%',
                        padding: '10px 14px',
                        borderRadius: '12px',
                        backgroundColor: isDark ? 'rgba(255, 255, 255, 0.05)' : '#FFFFFF',
                        border: isDark ? '1px solid rgba(255, 255, 255, 0.15)' : '1px solid #CBD5E1',
                        color: isDark ? '#FFFFFF' : '#121314',
                        fontSize: '13px',
                        outline: 'none',
                        boxSizing: 'border-box',
                      }}
                    />
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '11.5px', fontWeight: 700, color: isDark ? '#E5E5E5' : '#334155', marginBottom: '4px' }}>
                      Password (Strong required)
                    </label>
                    <input
                      type={showSignupPassword ? 'text' : 'password'}
                      value={signupPassword}
                      onChange={(e) => setSignupPassword(e.target.value)}
                      placeholder="••••••••"
                      required
                      style={{
                        width: '100%',
                        padding: '10px 14px',
                        borderRadius: '12px',
                        backgroundColor: isDark ? 'rgba(255, 255, 255, 0.05)' : '#FFFFFF',
                        border: isDark 
                          ? (passwordCriteria.isStrong ? '1px solid #10B981' : '1px solid rgba(255, 255, 255, 0.15)') 
                          : (passwordCriteria.isStrong ? '1px solid #10B981' : '1px solid #CBD5E1'),
                        color: isDark ? '#FFFFFF' : '#121314',
                        fontSize: '13px',
                        outline: 'none',
                        boxSizing: 'border-box',
                      }}
                    />
                  </div>

                  <div>
                    <label style={{ display: 'block', fontSize: '11.5px', fontWeight: 700, color: isDark ? '#E5E5E5' : '#334155', marginBottom: '4px' }}>
                      Confirm Password
                    </label>
                    <input
                      type={showSignupPassword ? 'text' : 'password'}
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      placeholder="••••••••"
                      required
                      style={{
                        width: '100%',
                        padding: '10px 14px',
                        borderRadius: '12px',
                        backgroundColor: isDark ? 'rgba(255, 255, 255, 0.05)' : '#FFFFFF',
                        border: isDark ? '1px solid rgba(255, 255, 255, 0.15)' : '1px solid #CBD5E1',
                        color: isDark ? '#FFFFFF' : '#121314',
                        fontSize: '13px',
                        outline: 'none',
                        boxSizing: 'border-box',
                      }}
                    />
                  </div>
                </div>

                {/* Real-time Password Strength Indicator */}
                {signupPassword.length > 0 && (
                  <div style={{
                    padding: '10px 12px',
                    borderRadius: '12px',
                    backgroundColor: isDark ? 'rgba(255, 255, 255, 0.04)' : '#F8FAFC',
                    border: isDark ? '1px solid rgba(255, 255, 255, 0.08)' : '1px solid #E2E8F0',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '6px',
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '11px' }}>
                      <span style={{ fontWeight: 600, color: isDark ? '#94A3B8' : '#64748B' }}>Password Strength:</span>
                      <span style={{
                        fontWeight: 800,
                        color: passwordCriteria.score === 4 ? '#10B981' : passwordCriteria.score === 3 ? '#EAB308' : passwordCriteria.score === 2 ? '#F97316' : '#EF4444'
                      }}>
                        {passwordCriteria.score === 4 ? 'Strong (Approved ✓)' : passwordCriteria.score === 3 ? 'Good' : passwordCriteria.score === 2 ? 'Fair' : 'Weak'}
                      </span>
                    </div>

                    {/* Progress Track */}
                    <div style={{ height: '4px', width: '100%', backgroundColor: isDark ? 'rgba(255,255,255,0.1)' : '#E2E8F0', borderRadius: '9999px', overflow: 'hidden' }}>
                      <div style={{
                        height: '100%',
                        width: `${(passwordCriteria.score / 4) * 100}%`,
                        backgroundColor: passwordCriteria.score === 4 ? '#10B981' : passwordCriteria.score === 3 ? '#EAB308' : passwordCriteria.score === 2 ? '#F97316' : '#EF4444',
                        transition: 'all 0.3s ease',
                      }} />
                    </div>

                    {/* Requirements Checklist */}
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px', marginTop: '2px', fontSize: '10.5px' }}>
                      <div style={{ color: passwordCriteria.hasMinLength ? '#10B981' : isDark ? '#64748B' : '#94A3B8', display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <span>{passwordCriteria.hasMinLength ? '✓' : '•'}</span>
                        <span>8+ characters</span>
                      </div>
                      <div style={{ color: (passwordCriteria.hasUpper && passwordCriteria.hasLower) ? '#10B981' : isDark ? '#64748B' : '#94A3B8', display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <span>{(passwordCriteria.hasUpper && passwordCriteria.hasLower) ? '✓' : '•'}</span>
                        <span>Upper & lower case</span>
                      </div>
                      <div style={{ color: passwordCriteria.hasDigit ? '#10B981' : isDark ? '#64748B' : '#94A3B8', display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <span>{passwordCriteria.hasDigit ? '✓' : '•'}</span>
                        <span>At least one number</span>
                      </div>
                      <div style={{ color: passwordCriteria.hasSpecial ? '#10B981' : isDark ? '#64748B' : '#94A3B8', display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <span>{passwordCriteria.hasSpecial ? '✓' : '•'}</span>
                        <span>Special symbol (!@#$)</span>
                      </div>
                    </div>
                  </div>
                )}

                {/* Terms and AI Acknowledgment */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '4px' }}>
                  <label style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', fontSize: '11.5px', color: isDark ? '#CBD5E1' : '#475569', cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={termsAccepted}
                      onChange={(e) => setTermsAccepted(e.target.checked)}
                      style={{ marginTop: '2px' }}
                    />
                    <span>
                      I agree to the{' '}
                      <span
                        onClick={(e) => {
                          e.stopPropagation();
                          setPolicyTab('terms');
                          setShowPolicyModal(true);
                        }}
                        style={{ color: '#0284C7', textDecoration: 'underline' }}
                      >
                        Sovereign Infrastructure Data Terms
                      </span>
                    </span>
                  </label>

                  <label style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', fontSize: '11.5px', color: isDark ? '#CBD5E1' : '#475569', cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={aiAckAccepted}
                      onChange={(e) => setAiAckAccepted(e.target.checked)}
                      style={{ marginTop: '2px' }}
                    />
                    <span>
                      I acknowledge that AI/ML risk predictions operate under explicit human decision governance.
                    </span>
                  </label>
                </div>

                <button
                  type="submit"
                  disabled={signupLoading}
                  style={{
                    marginTop: '8px',
                    padding: '12px 20px',
                    borderRadius: '14px',
                    backgroundColor: isDark ? '#FFFFFF' : '#121314',
                    color: isDark ? '#070A12' : '#FFFFFF',
                    border: 'none',
                    fontSize: '13px',
                    fontWeight: 800,
                    cursor: signupLoading ? 'wait' : 'pointer',
                    transition: 'all 0.2s ease',
                  }}
                >
                  {signupLoading ? 'Generating Secure Registration...' : 'Proceed to Verification →'}
                </button>
              </form>
            )}

            {/* STEP 2: OTP VERIFICATION */}
            {signupStep === 2 && (
              <div style={{ textAlign: 'center', padding: '10px 0' }}>
                <p style={{ fontSize: '13px', color: isDark ? '#E5E5E5' : '#475569', marginBottom: '20px' }}>
                  A 6-digit verification passkey was dispatched to <strong style={{ color: isDark ? '#FFFFFF' : '#0F172A' }}>{signupEmail}</strong>.
                </p>

                {otpError && (
                  <div style={{ padding: '8px 12px', borderRadius: '10px', backgroundColor: 'rgba(239, 68, 68, 0.15)', color: '#EF4444', fontSize: '12px', marginBottom: '16px' }}>
                    {otpError}
                  </div>
                )}

                <div style={{ display: 'flex', justifyContent: 'center', gap: '8px', marginBottom: '24px' }}>
                  {otpDigits.map((digit, i) => (
                    <input
                      key={i}
                      ref={(el) => (otpInputsRef.current[i] = el)}
                      type="text"
                      maxLength={1}
                      value={digit}
                      onChange={(e) => handleOtpChange(i, e.target.value)}
                      onKeyDown={(e) => handleOtpKeyDown(i, e)}
                      style={{
                        width: '44px',
                        height: '52px',
                        textAlign: 'center',
                        fontSize: '22px',
                        fontWeight: 800,
                        borderRadius: '12px',
                        backgroundColor: isDark ? 'rgba(255, 255, 255, 0.08)' : '#F8FAFC',
                        border: isDark ? '1.5px solid rgba(255, 255, 255, 0.2)' : '1.5px solid #CBD5E1',
                        color: isDark ? '#FFFFFF' : '#121314',
                        outline: 'none',
                      }}
                    />
                  ))}
                </div>

                <button
                  type="button"
                  onClick={handleVerifyOtp}
                  disabled={otpLoading}
                  style={{
                    width: '100%',
                    padding: '12px',
                    borderRadius: '14px',
                    backgroundColor: isDark ? '#FFFFFF' : '#121314',
                    color: isDark ? '#070A12' : '#FFFFFF',
                    border: 'none',
                    fontSize: '13.5px',
                    fontWeight: 800,
                    cursor: otpLoading ? 'wait' : 'pointer',
                    marginBottom: '14px',
                  }}
                >
                  {otpLoading ? 'Validating Token...' : 'Verify & Authorize Account'}
                </button>

                <div style={{ fontSize: '12px', color: '#94A3B8' }}>
                  {canResend ? (
                    <button
                      type="button"
                      onClick={handleResendOtp}
                      style={{ background: 'none', border: 'none', color: '#0284C7', fontWeight: 700, cursor: 'pointer' }}
                    >
                      Resend Verification Code
                    </button>
                  ) : (
                    <span>Resend available in {resendTimer}s</span>
                  )}
                </div>
              </div>
            )}

            {/* STEP 3: PROVISIONED SUCCESS */}
            {signupStep === 3 && (
              <div style={{ textAlign: 'center', padding: '16px 0' }}>
                <div
                  style={{
                    width: '56px',
                    height: '56px',
                    borderRadius: '50%',
                    backgroundColor: 'rgba(16, 185, 129, 0.15)',
                    color: '#10B981',
                    fontSize: '28px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    margin: '0 auto 16px auto',
                  }}
                >
                  ✓
                </div>
                <h3 style={{ fontSize: '18px', fontWeight: 800, color: isDark ? '#FFFFFF' : '#121314', margin: '0 0 8px 0' }}>
                  Account Provisioned Successfully
                </h3>
                <p style={{ fontSize: '13px', color: isDark ? '#CBD5E1' : '#64748B', marginBottom: '24px' }}>
                  Your sovereign credentials have been verified and assigned to your ministry scope.
                </p>
                <button
                  type="button"
                  onClick={() => {
                    setActiveTab('signin');
                    setSignupStep(1);
                    setLoginEmail(signupEmail);
                  }}
                  style={{
                    width: '100%',
                    padding: '12px',
                    borderRadius: '14px',
                    backgroundColor: '#10B981',
                    color: '#FFFFFF',
                    border: 'none',
                    fontSize: '13.5px',
                    fontWeight: 800,
                    cursor: 'pointer',
                  }}
                >
                  Proceed to Official Sign In →
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* POLICY MODAL */}
      {showPolicyModal && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            zIndex: 1000,
            backgroundColor: 'rgba(0,0,0,0.7)',
            backdropFilter: 'blur(8px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '20px',
          }}
        >
          <div
            style={{
              width: '100%',
              maxWidth: '680px',
              borderRadius: '24px',
              backgroundColor: isDark ? '#0F172A' : '#FFFFFF',
              border: isDark ? '1px solid rgba(255,255,255,0.15)' : '1px solid #E2E8F0',
              padding: '28px',
              color: isDark ? '#FFFFFF' : '#1E293B',
              boxShadow: '0 25px 60px rgba(0,0,0,0.5)',
            }}
          >
            {/* Modal Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '20px' }}>⚖️</span>
                <h3 style={{ fontSize: '18px', fontWeight: 800, margin: 0 }}>
                  PAIMANA Governance & Compliance
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setShowPolicyModal(false)}
                style={{ background: 'none', border: 'none', fontSize: '18px', cursor: 'pointer', color: isDark ? '#FFF' : '#000' }}
              >
                ✕
              </button>
            </div>

            {/* Policy Tab Switcher */}
            <div style={{
              display: 'flex',
              gap: '4px',
              padding: '4px',
              borderRadius: '12px',
              backgroundColor: isDark ? 'rgba(255,255,255,0.06)' : '#F1F5F9',
              marginBottom: '16px',
            }}>
              <button
                type="button"
                onClick={() => setPolicyTab('terms')}
                style={{
                  flex: 1,
                  padding: '8px 14px',
                  borderRadius: '8px',
                  border: 'none',
                  backgroundColor: policyTab === 'terms' ? (isDark ? '#FFFFFF' : '#0F172A') : 'transparent',
                  color: policyTab === 'terms' ? (isDark ? '#0F172A' : '#FFFFFF') : (isDark ? '#94A3B8' : '#64748B'),
                  fontWeight: 700,
                  fontSize: '12px',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                }}
              >
                Terms of Use & Data Governance
              </button>
              <button
                type="button"
                onClick={() => setPolicyTab('privacy')}
                style={{
                  flex: 1,
                  padding: '8px 14px',
                  borderRadius: '8px',
                  border: 'none',
                  backgroundColor: policyTab === 'privacy' ? (isDark ? '#FFFFFF' : '#0F172A') : 'transparent',
                  color: policyTab === 'privacy' ? (isDark ? '#0F172A' : '#FFFFFF') : (isDark ? '#94A3B8' : '#64748B'),
                  fontWeight: 700,
                  fontSize: '12px',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                }}
              >
                Privacy & Cryptographic Security
              </button>
            </div>

            {/* Content Body */}
            <div style={{ fontSize: '13px', lineHeight: 1.65, maxHeight: '360px', overflowY: 'auto', paddingRight: '10px' }}>
              {policyTab === 'terms' ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <p style={{ margin: 0 }}>
                    <strong>1. National Infrastructure Telemetry Mandate:</strong> All project cost revisions, schedule slippages, and contractor IPC ledgers submitted to the PAIMANA platform are governed under the institutional monitoring oversight of the Ministry of Statistics and Programme Implementation (MoSPI) and PRAGATI coordination frameworks.
                  </p>
                  <p style={{ margin: 0 }}>
                    <strong>2. Role-Based Institutional Access:</strong> Analytical access is strictly restricted to authenticated ministry nodal officers, project directors, and accredited central planners. Account credentials cannot be delegated, shared, or automated through unauthorized third-party scripts.
                  </p>
                  <p style={{ margin: 0 }}>
                    <strong>3. AI/ML Decision-Support Nature:</strong> The Dynamic Project Health & Integrity Score (DPHIS), LightGBM predictive distributions, and SHAP explainability factors are advisory decision-support mechanisms. Automated risk triggers notify nodal officers but do not supersede official statutory administrative procedures.
                  </p>
                  <p style={{ margin: 0 }}>
                    <strong>4. Cryptographic Audit Trail:</strong> Every threshold calibration, asset parameter update, and alert resolution is immutably appended to the tamper-evident institutional audit ledger with officer attribution and UTC timestamps.
                  </p>
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <p style={{ margin: 0 }}>
                    <strong>1. Zero Commercialization & Data Sovereignty:</strong> PAIMANA maintains an absolute zero-commercialization guarantee. No government official contact data, project telemetry, or ministry communications are ever shared with commercial entities or third-party ad networks.
                  </p>
                  <p style={{ margin: 0 }}>
                    <strong>2. Ephemeral OTP & Credential Security:</strong> User registration and authentication verification codes (6-digit OTPs) are cryptographically hashed via SHA-256 and automatically expire after 5 minutes. Passwords must adhere to strict complexity requirements and are salted via bcrypt.
                  </p>
                  <p style={{ margin: 0 }}>
                    <strong>3. Encryption Standards:</strong> All data in transit is protected using TLS 1.3 encryption. At-rest database persistence in MongoDB Atlas utilizes AES-256 volume encryption with restricted IP whitelisting.
                  </p>
                  <p style={{ margin: 0 }}>
                    <strong>4. Session Management & Transparency:</strong> Authenticated sessions carry signed JWT bearer tokens. Officers may inspect active sessions and revoke authorized tokens on demand via Account Settings.
                  </p>
                </div>
              )}
            </div>

            <button
              type="button"
              onClick={() => setShowPolicyModal(false)}
              style={{
                marginTop: '20px',
                width: '100%',
                padding: '11px',
                borderRadius: '12px',
                backgroundColor: isDark ? '#FFFFFF' : '#121314',
                color: isDark ? '#070A12' : '#FFFFFF',
                border: 'none',
                fontWeight: 700,
                fontSize: '13px',
                cursor: 'pointer',
              }}
            >
              I Understand & Acknowledge
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
