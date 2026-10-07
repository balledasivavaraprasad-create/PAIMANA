import React, { useState, useEffect, useRef, useMemo } from 'react';
import HeaderNav, { ActiveTab } from './components/HeaderNav';
import CeoPinManager, { ProjectPin } from './components/CeoPinManager';
import AddProjectModal from './components/AddProjectModal';
import ProjectIntelligence from './pages/ProjectIntelligence';
import Analytics from './pages/Analytics';
import Assistant from './pages/Assistant';
import Alerts from './pages/Alerts';
import MyProjects from './pages/MyProjects';
import DataModels from './pages/DataModels';
import UsersAudit from './pages/UsersAudit';
import ProjectInsightsModal from './components/ProjectInsightsModal';
import InvestigationModal from './components/InvestigationModal';
import SettingsModal, { SettingsTab } from './components/SettingsModal';
import MyProjectOverview from './components/MyProjectOverview';
import Login from './pages/Login';
import { EditorialLandingPage } from './landing/editorial/EditorialLandingPage';
import { InteractiveLivingBackground } from './components/InteractiveLivingBackground';
import { useTheme } from './hooks/useTheme';
import { getRiskCategory } from './lib/risk';
import { computeRealTimeShapFactors } from './lib/shap';
import { CurvedGrowthArrow, TrendBadge } from './components/CurvedTrendArrow';
import {
  fetchProjects, fetchMyProjects, fetchAlerts, fetchAnalyticsOverview, API_BASE,
  fetchCurrentUser, clearAuthToken, UserProfile, deleteProject
} from './lib/api';
import { DEMO_USER_10_PROJECTS, DEMO_ADMIN_28_PROJECTS } from './lib/seededProjects';

export type Page = ActiveTab | 'overview' | 'reports';

export default function App() {
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  // Routing State: 'landing' | 'app' | 'login'
  const getInitialRoute = (): 'landing' | 'app' | 'login' => {
    const hash = window.location.hash;
    const pathname = window.location.pathname;
    if (hash.startsWith('#/app') || pathname.startsWith('/app')) {
      return 'app';
    }
    if (hash.startsWith('#/login') || hash.startsWith('#/auth') || pathname.startsWith('/login')) {
      return 'login';
    }
    return 'landing';
  };

  const [currentRoute, setCurrentRoute] = useState<'landing' | 'app' | 'login'>(getInitialRoute);
  const [authChecking, setAuthChecking] = useState<boolean>(true);
  const [currentUser, setCurrentUser] = useState<UserProfile | null>(null);

  const userRole = (currentUser?.role || '').toUpperCase();
  const isAdmin = userRole === 'ADMIN' || userRole === 'ANALYST' || currentUser?.username?.toLowerCase() === 'admin';
  const [currentTab, setCurrentTab] = useState<ActiveTab>('motion');

  const [ministryFilterOnly, setMinistryFilterOnly] = useState<boolean>(false);
  const [pins, setPins] = useState<ProjectPin[]>([]);
  const [selectedPin, setSelectedPin] = useState<ProjectPin | null>(null);
  const [insightsModalProjectId, setInsightsModalProjectId] = useState<string | null>(null);
  const [investigationModalProjectId, setInvestigationModalProjectId] = useState<string | null>(null);
  const [settingsModalOpen, setSettingsModalOpen] = useState<boolean>(false);
  const [settingsModalTab, setSettingsModalTab] = useState<SettingsTab>('profile');
  const [showCeoModal, setShowCeoModal] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);
  const [alertCount, setAlertCount] = useState<number>(31);

  // Overview Simulation State
  const [simMode, setSimMode] = useState<'live' | 'surge' | 'audit'>('live');
  const [isPulsingFeed, setIsPulsingFeed] = useState<boolean>(false);
  const [streamSpeed, setStreamSpeed] = useState<'14ms' | '5s' | '30s'>('14ms');
  const [telemetryPackets, setTelemetryPackets] = useState<number>(148418);

  const [portfolioStats, setPortfolioStats] = useState({
    avgDphis: 78.4,
    totalProjects: 428,
    criticalCount: 130
  });

  // Handle URL hash changes
  useEffect(() => {
    const handleHashOrPop = () => {
      const hash = window.location.hash;
      const pathname = window.location.pathname;
      if (hash.startsWith('#/app') || pathname.startsWith('/app')) {
        setCurrentRoute('app');
      } else if (hash.startsWith('#/login') || hash.startsWith('#/auth') || pathname.startsWith('/login')) {
        setCurrentRoute('login');
      } else {
        setCurrentRoute('landing');
      }
    };

    window.addEventListener('hashchange', handleHashOrPop);
    window.addEventListener('popstate', handleHashOrPop);
    return () => {
      window.removeEventListener('hashchange', handleHashOrPop);
      window.removeEventListener('popstate', handleHashOrPop);
    };
  }, []);

  // Telemetry stream incrementer
  useEffect(() => {
    const interval = setInterval(() => {
      setTelemetryPackets(prev => prev + 18);
    }, 1200);
    return () => clearInterval(interval);
  }, []);

  // 1. Initial Authentication Preflight & Live Data Sync
  useEffect(() => {
    fetchCurrentUser()
      .then(user => {
        if (user) {
          setCurrentUser(user);
        } else {
          clearAuthToken();
          setCurrentUser(null);
        }
      })
      .catch(() => {
        clearAuthToken();
        setCurrentUser(null);
      })
      .finally(() => {
        setAuthChecking(false);
      });

    fetchAlerts().then(items => {
      const pendingCount = items.filter(a => a.status === 'PENDING').length;
      setAlertCount(pendingCount > 0 ? pendingCount : 31);
    }).catch(console.warn);

    fetchAnalyticsOverview().then(ov => {
      if (ov) {
        setPortfolioStats({
          avgDphis: ov.average_dphis || 78.4,
          totalProjects: ov.total_projects || 428,
          criticalCount: ov.critical || 130
        });
      }
    }).catch(console.warn);
  }, []);

  // 2. Fetch Corridors for Logged-In User
  useEffect(() => {
    const isCurrentAdmin = currentUser && (
      (currentUser.role || '').toUpperCase() === 'ADMIN' ||
      (currentUser.role || '').toUpperCase() === 'ANALYST' ||
      currentUser.username.toLowerCase() === 'admin'
    );

    if (!currentUser) {
      const defaultPins: ProjectPin[] = DEMO_USER_10_PROJECTS.map(p => ({
        id: p.project_id,
        name: p.project_name,
        state: p.state,
        latPct: Math.round((((p.location?.latitude || 20) - 8) / (36 - 8)) * 100),
        lngPct: Math.round((((p.location?.longitude || 78) - 68) / (97 - 68)) * 100),
        dphis: Math.round(p.dphis || 50),
        risk: p.risk_level || 'moderate',
        cost: `₹${p.cost?.revised || 4000} Cr`,
        delay: `${Math.round((p.dphis || 50) > 70 ? 24 : 6)} mo`
      }));
      setPins(defaultPins);
      setSelectedPin(defaultPins[0] || null);
      return;
    }

    fetchMyProjects(currentUser.username).then(dbProjects => {
      let activeProjects = dbProjects;
      if (!activeProjects || activeProjects.length === 0) {
        activeProjects = isCurrentAdmin ? DEMO_ADMIN_28_PROJECTS : DEMO_USER_10_PROJECTS;
      } else if (isCurrentAdmin && activeProjects.length < 25) {
        const existingIds = new Set(activeProjects.map(p => p.project_id));
        const supplement = DEMO_ADMIN_28_PROJECTS.filter(p => !existingIds.has(p.project_id));
        activeProjects = [...activeProjects, ...supplement].slice(0, 28);
      } else if (!isCurrentAdmin && activeProjects.length !== 10) {
        activeProjects = activeProjects.length >= 10 ? activeProjects.slice(0, 10) : DEMO_USER_10_PROJECTS;
      }

      const mappedPins: ProjectPin[] = activeProjects.map(p => ({
        id: p.project_id,
        name: p.project_name,
        state: p.state,
        latPct: Math.round((((p.location?.latitude || 20) - 8) / (36 - 8)) * 100),
        lngPct: Math.round((((p.location?.longitude || 78) - 68) / (97 - 68)) * 100),
        dphis: Math.round(p.dphis || 50),
        risk: p.risk_level || 'moderate',
        cost: `₹${p.cost?.revised || 4000} Cr`,
        delay: `${Math.round((p.dphis || 50) > 70 ? 24 : 6)} mo`
      }));
      setPins(mappedPins);
      setSelectedPin(mappedPins[0] || null);
    }).catch(err => {
      console.warn('Failed to fetch user projects, using fallback', err);
      const fallbackList = isCurrentAdmin ? DEMO_ADMIN_28_PROJECTS : DEMO_USER_10_PROJECTS;
      const mappedPins: ProjectPin[] = fallbackList.map(p => ({
        id: p.project_id,
        name: p.project_name,
        state: p.state,
        latPct: Math.round((((p.location?.latitude || 20) - 8) / (36 - 8)) * 100),
        lngPct: Math.round((((p.location?.longitude || 78) - 68) / (97 - 68)) * 100),
        dphis: Math.round(p.dphis || 50),
        risk: p.risk_level || 'moderate',
        cost: `₹${p.cost?.revised || 4000} Cr`,
        delay: `${Math.round((p.dphis || 50) > 70 ? 24 : 6)} mo`
      }));
      setPins(mappedPins);
      setSelectedPin(mappedPins[0] || null);
    });
  }, [currentUser?.username, currentUser?.role]);

  const handleLoginSuccess = (authData: any) => {
    const profile: UserProfile = {
      username: authData.username,
      role: authData.role,
      email: authData.email || '',
      full_name: authData.full_name || authData.username,
      ministry: authData.ministry || 'Central Infrastructure',
      designation: authData.designation || (authData.role === 'ADMIN' ? 'MoSPI Lead Director' : 'Project Officer'),
      dphis_alert_threshold: authData.dphis_alert_threshold || 75.0,
      alert_email: authData.email || '',
      notify_via_email: true
    };
    setCurrentUser(profile);
    window.location.hash = '/app';
    setCurrentRoute('app');
    setCurrentTab('motion');
  };

  const handleSignOut = () => {
    clearAuthToken();
    setCurrentUser(null);
    window.location.hash = '';
    setCurrentRoute('landing');
  };

  const handleEnterPlatform = () => {
    if (currentUser) {
      window.location.hash = '/app';
      setCurrentRoute('app');
    } else {
      window.location.hash = '/login';
      setCurrentRoute('login');
    }
  };

  const handleNavigateToLanding = () => {
    window.location.hash = '';
    setCurrentRoute('landing');
  };

  const handleRemoveProject = async (projectId: string) => {
    if (!window.confirm(`Are you sure you want to remove project ${projectId} from monitoring?`)) {
      return;
    }
    const success = await deleteProject(projectId);
    if (success) {
      setPins(prev => prev.filter(p => p.id !== projectId));
      if (selectedPin?.id === projectId) {
        setSelectedPin(pins.find(p => p.id !== projectId) || null);
      }
    }
  };

  const handlePulseStream = () => {
    setIsPulsingFeed(true);
    setTelemetryPackets(prev => prev + 540);
    setTimeout(() => setIsPulsingFeed(false), 1400);
  };

  // 1. Splash preflight screen while verifying session
  if (authChecking) {
    return (
      <div className={`w-screen h-screen flex flex-col items-center justify-center transition-colors ${
        isDark ? 'bg-[#07090E] text-white' : 'bg-[#FAF7F2] text-black'
      }`}>
        <InteractiveLivingBackground isDark={isDark} />
        <div className="relative z-10 flex flex-col items-center gap-4">
          <div className={`w-14 h-14 rounded-2xl flex items-center justify-center font-mono font-bold text-2xl border ${
            isDark ? 'bg-black/80 text-white border-white/20 shadow-[0_0_24px_rgba(255,255,255,0.2)]' : 'bg-white/90 text-black border-black/10 shadow-lg'
          }`}>
            ▲
          </div>
          <div className="text-center">
            <div className={`text-xs font-mono font-bold tracking-widest uppercase ${isDark ? 'text-white' : 'text-slate-900'}`}>
              INFRABUILD AI COMMAND
            </div>
            <div className={`text-[11px] font-mono mt-1 ${isDark ? 'text-white/60' : 'text-slate-600'}`}>
              Synchronizing national infrastructure telemetry...
            </div>
          </div>
        </div>
      </div>
    );
  }

  // 2. PUBLIC EDITORIAL LANDING PAGE (Opening layer)
  if (currentRoute === 'landing') {
    return (
      <EditorialLandingPage onEnterApp={handleEnterPlatform} />
    );
  }

  // 3. LOGIN / AUTHENTICATION PORTAL
  if (currentRoute === 'login' || !currentUser) {
    return (
      <div className="relative min-h-screen">
        <InteractiveLivingBackground isDark={isDark} />
        <Login
          onLoginSuccess={handleLoginSuccess}
        />
        {/* Floating Return to Landing Page Pill */}
        <div style={{ position: 'fixed', bottom: '24px', right: '28px', zIndex: 9999 }}>
          <button
            onClick={handleNavigateToLanding}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '10px 20px',
              borderRadius: '9999px',
              backgroundColor: 'rgba(18, 19, 20, 0.94)',
              backdropFilter: 'blur(20px)',
              WebkitBackdropFilter: 'blur(20px)',
              color: '#FFFFFF',
              border: '1px solid rgba(255, 255, 255, 0.16)',
              fontSize: '12.5px',
              fontWeight: 700,
              boxShadow: '0 16px 40px -4px rgba(0, 0, 0, 0.45)',
              cursor: 'pointer',
            }}
          >
            <span>← Public Landing Film</span>
          </button>
        </div>
      </div>
    );
  }

  const isAnyModalOpen = Boolean(
    insightsModalProjectId ||
    investigationModalProjectId ||
    settingsModalOpen ||
    showAddModal ||
    showCeoModal
  );

  // 4. AUTHENTICATED COMMAND PLATFORM
  return (
    <div className={`relative w-screen h-screen overflow-hidden transition-colors duration-300 ${
      isDark ? 'bg-[#07090E] text-white' : 'bg-[#FAF7F2] text-[#121314]'
    }`}>
      {/* Living Atmospheric Aura Background (Replaces background videos) */}
      <InteractiveLivingBackground isDark={isDark} />

      {/* Floating Pill Top Header Navigation */}
      <HeaderNav
        currentTab={currentTab}
        onTabChange={setCurrentTab}
        alertCount={alertCount}
        user={currentUser}
        onSignOut={handleSignOut}
        onOpenSettings={(tab) => {
          setSettingsModalTab(tab || 'profile');
          setSettingsModalOpen(true);
        }}
        onOpenLanding={handleNavigateToLanding}
        isModalOpen={isAnyModalOpen}
      />

      {/* Floating Quick Return to Editorial Landing Pill (as shown in Screenshot 1) */}
      <div style={{
        position: 'fixed',
        bottom: '24px',
        right: '28px',
        zIndex: isAnyModalOpen ? 0 : 9999,
        opacity: isAnyModalOpen ? 0 : 1,
        pointerEvents: isAnyModalOpen ? 'none' : 'auto',
        transition: 'opacity 0.25s ease, transform 0.25s ease',
        transform: isAnyModalOpen ? 'translateY(12px)' : 'translateY(0)',
      }}>
        <button
          onClick={handleNavigateToLanding}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '10px 20px',
            borderRadius: '9999px',
            backgroundColor: 'rgba(18, 19, 20, 0.94)',
            backdropFilter: 'blur(20px)',
            WebkitBackdropFilter: 'blur(20px)',
            color: '#FFFFFF',
            border: '1px solid rgba(255, 255, 255, 0.16)',
            fontSize: '12.5px',
            fontWeight: 700,
            boxShadow: '0 16px 40px -4px rgba(0, 0, 0, 0.45), 0 2px 6px rgba(0, 0, 0, 0.2)',
            cursor: 'pointer',
            transition: 'all 0.25s cubic-bezier(0.16, 1, 0.3, 1)',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.transform = 'translateY(-2px)';
            e.currentTarget.style.backgroundColor = 'rgba(28, 29, 32, 0.98)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = 'translateY(0)';
            e.currentTarget.style.backgroundColor = 'rgba(18, 19, 20, 0.94)';
          }}
        >
          <span>← Public Landing Film</span>
        </button>
      </div>

      {/* VIEWPORT CONTENT CONTAINER */}
      {(currentTab === 'motion' || currentTab === 'overview') ? (
        !isAdmin ? (
          /* REGULAR USER: 4 COLUMNS SCOPE — MY PROJECT OVERVIEW */
          <div className="relative z-10 w-full h-full overflow-y-auto buttery-smooth-scroll pt-20 sm:pt-24 pb-24">
            <MyProjectOverview
              currentUser={currentUser}
              pins={pins}
              onViewProject={(projId) => {
                const found = pins.find(p => p.id === projId);
                if (found) setSelectedPin(found);
                setInsightsModalProjectId(projId);
              }}
              onNavigateToProjects={() => setCurrentTab('projects')}
              onNavigateToRiskIntelligence={(projId) => {
                const found = pins.find(p => p.id === projId);
                if (found) setSelectedPin(found);
                setCurrentTab('intelligence');
              }}
              onOpenAddProject={() => setShowAddModal(true)}
              onNavigateToInvestigation={(projId) => {
                const found = pins.find(p => p.id === projId);
                if (found) setSelectedPin(found);
                setInvestigationModalProjectId(projId);
              }}
              onRemoveProject={handleRemoveProject}
            />
          </div>
        ) : (
          /* ADMIN: 7 COLUMNS SCOPE — NATIONAL INFRASTRUCTURE OVERVIEW (Pixel-matched to Screenshot 1) */
          <div className="relative z-10 w-full h-full overflow-y-auto buttery-smooth-scroll pt-24 sm:pt-28 pb-28 px-4 sm:px-8 md:px-14 max-w-7xl mx-auto space-y-8 animate-fade-in">
            {/* 1. Telemetry Stream Sync Delay Banner (Screenshot 1 top banner) */}
            <div
              style={{
                borderRadius: '20px',
                padding: '18px 24px',
                backgroundColor: isDark ? 'rgba(18, 20, 24, 0.88)' : 'rgba(255, 255, 255, 0.92)',
                backdropFilter: 'blur(20px)',
                WebkitBackdropFilter: 'blur(20px)',
                border: isDark ? '1px solid rgba(255, 255, 255, 0.12)' : '1px solid #EFEFEA',
                boxShadow: isDark ? '0 12px 36px rgba(0,0,0,0.5)' : '0 10px 30px rgba(0,0,0,0.04)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                flexWrap: 'wrap',
                gap: '16px',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                <div
                  style={{
                    width: '10px',
                    height: '10px',
                    borderRadius: '50%',
                    backgroundColor: '#0284C7',
                    boxShadow: '0 0 10px #0284C7',
                  }}
                />
                <span
                  style={{
                    fontSize: '14px',
                    color: isDark ? '#E5E5E5' : '#4E5055',
                    lineHeight: 1.5,
                  }}
                >
                  Telemetry stream synchronized <strong style={{ color: isDark ? '#FFFFFF' : '#121314' }}>9 days ago</strong>. Automated predictive models operating with nominal peer covariance.
                </span>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span
                  style={{
                    fontSize: '11.5px',
                    fontWeight: 700,
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em',
                    padding: '6px 14px',
                    borderRadius: '9999px',
                    backgroundColor: isDark ? 'rgba(255, 255, 255, 0.08)' : '#F3F4F6',
                    color: isDark ? 'rgba(255, 255, 255, 0.7)' : '#6B7280',
                    border: isDark ? '1px solid rgba(255, 255, 255, 0.15)' : '1px solid #E5E7EB',
                  }}
                >
                  SYNC DELAYED
                </span>

                <button
                  type="button"
                  onClick={handlePulseStream}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    padding: '7px 16px',
                    borderRadius: '9999px',
                    backgroundColor: isDark ? '#FFFFFF' : '#121314',
                    color: isDark ? '#070A12' : '#FFFFFF',
                    border: 'none',
                    fontSize: '12.5px',
                    fontWeight: 700,
                    cursor: 'pointer',
                    boxShadow: '0 4px 14px rgba(0, 0, 0, 0.2)',
                    transition: 'all 0.2s ease',
                  }}
                >
                  <span>⚡</span>
                  <span>{isPulsingFeed ? 'Synchronizing...' : 'Sync Stream'}</span>
                </button>
              </div>
            </div>

            {/* 2. Hero Headline & Live Control Pills */}
            <div className="space-y-4">
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#0284C7' }} />
                <span
                  style={{
                    fontSize: '11.5px',
                    fontWeight: 800,
                    textTransform: 'uppercase',
                    letterSpacing: '0.1em',
                    color: isDark ? 'rgba(255, 255, 255, 0.65)' : '#64748B',
                  }}
                >
                  SOVEREIGN RISK INTELLIGENCE • NATIONAL OPERATIONS
                </span>
              </div>

              <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
                <div>
                  <h1
                    style={{
                      fontSize: 'clamp(2.2rem, 4.2vw, 3.4rem)',
                      fontWeight: 800,
                      letterSpacing: '-0.035em',
                      lineHeight: 1.05,
                      color: isDark ? '#FFFFFF' : '#121314',
                      margin: 0,
                    }}
                  >
                    National Infrastructure Overview
                  </h1>
                  <p
                    style={{
                      fontSize: '15px',
                      color: isDark ? 'rgba(255, 255, 255, 0.75)' : '#4E5055',
                      lineHeight: 1.6,
                      marginTop: '10px',
                      maxWidth: '720px',
                    }}
                  >
                    Continuous observational surveillance, verified contractor IPC ledgers, and peer covariance across 428 federal infrastructure assets.
                  </p>
                </div>

                {/* Filter and Pulse Actions */}
                <div className="flex items-center gap-3 flex-wrap">
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      backgroundColor: isDark ? 'rgba(22, 22, 24, 0.82)' : 'rgba(244, 242, 236, 0.78)',
                      padding: '4px',
                      borderRadius: '9999px',
                      border: isDark ? '1px solid rgba(255, 255, 255, 0.16)' : '1px solid #E5E3DC',
                    }}
                  >
                    {[
                      { id: 'live', label: '🟢 Live Telemetry' },
                      { id: 'surge', label: '⚡ Anomaly Surge' },
                      { id: 'audit', label: '🛡️ Audit Pipeline' },
                    ].map((m) => (
                      <button
                        key={m.id}
                        type="button"
                        onClick={() => setSimMode(m.id as any)}
                        style={{
                          padding: '7px 16px',
                          fontSize: '12px',
                          fontWeight: simMode === m.id ? 700 : 500,
                          borderRadius: '9999px',
                          border: 'none',
                          backgroundColor: simMode === m.id ? (isDark ? '#FFFFFF' : '#121314') : 'transparent',
                          color: simMode === m.id ? (isDark ? '#070A12' : '#FFFFFF') : (isDark ? 'rgba(255,255,255,0.7)' : '#4E5055'),
                          cursor: 'pointer',
                          transition: 'all 0.2s ease',
                        }}
                      >
                        {m.label}
                      </button>
                    ))}
                  </div>

                  <button
                    type="button"
                    onClick={handlePulseStream}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      padding: '11px 22px',
                      borderRadius: '9999px',
                      backgroundColor: '#121314',
                      color: '#FFFFFF',
                      border: 'none',
                      fontSize: '13px',
                      fontWeight: 700,
                      cursor: 'pointer',
                      boxShadow: '0 8px 24px rgba(0, 0, 0, 0.25)',
                      transition: 'all 0.2s ease',
                    }}
                  >
                    <span>⚡ Pulse Telemetry Feed</span>
                  </button>
                </div>
              </div>
            </div>

            {/* 3. National Surveillance Ribbon Meta Bar (Screenshot 1 middle pill row) */}
            <div
              style={{
                borderRadius: '24px',
                padding: '14px 24px',
                backgroundColor: isDark ? 'rgba(16, 18, 22, 0.85)' : 'rgba(255, 255, 255, 0.90)',
                backdropFilter: 'blur(16px)',
                WebkitBackdropFilter: 'blur(16px)',
                border: isDark ? '1px solid rgba(255, 255, 255, 0.12)' : '1px solid #EFEFEA',
                boxShadow: isDark ? '0 10px 30px rgba(0,0,0,0.4)' : '0 8px 24px rgba(0,0,0,0.03)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                flexWrap: 'wrap',
                gap: '12px',
              }}
            >
              <div className="flex items-center gap-3 flex-wrap text-xs">
                <span
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    padding: '5px 12px',
                    borderRadius: '9999px',
                    backgroundColor: isDark ? 'rgba(255, 255, 255, 0.08)' : '#F3F4F6',
                    fontWeight: 700,
                  }}
                >
                  <span style={{ color: '#10B981' }}>●</span>
                  <span>Monitoring active • 428 Federal Assets Under Surveillance</span>
                </span>

                <span
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    padding: '5px 12px',
                    borderRadius: '9999px',
                    backgroundColor: isDark ? 'rgba(255, 255, 255, 0.08)' : '#F3F4F6',
                    fontWeight: 600,
                  }}
                >
                  <span>🏛️</span>
                  <span>18 Federal Ministries Integrated</span>
                </span>

                <span
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    padding: '5px 12px',
                    borderRadius: '9999px',
                    backgroundColor: isDark ? 'rgba(255, 255, 255, 0.08)' : '#F3F4F6',
                    fontWeight: 700,
                    color: isDark ? '#FBBF24' : '#D97706',
                  }}
                >
                  <span>💰</span>
                  <span>₹1,990,633 Cr Capital Outlay</span>
                </span>
              </div>

              {/* Live Streaming Indicator */}
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  fontSize: '12px',
                  fontFamily: 'monospace',
                }}
              >
                <span style={{ color: '#10B981', fontWeight: 700 }}>● {telemetryPackets.toLocaleString()} pkts/s</span>
                <span style={{ opacity: 0.4 }}>|</span>
                <span style={{ color: isDark ? '#A3A3A3' : '#64748B' }}>STREAM:</span>
                <div style={{ display: 'flex', gap: '4px' }}>
                  {(['14ms', '5s', '30s'] as const).map((spd) => (
                    <button
                      key={spd}
                      type="button"
                      onClick={() => setStreamSpeed(spd)}
                      style={{
                        padding: '3px 8px',
                        borderRadius: '6px',
                        border: 'none',
                        fontSize: '11px',
                        fontWeight: streamSpeed === spd ? 800 : 500,
                        backgroundColor: streamSpeed === spd ? '#121314' : 'transparent',
                        color: streamSpeed === spd ? '#FFFFFF' : (isDark ? '#E5E5E5' : '#64748B'),
                        cursor: 'pointer',
                      }}
                    >
                      {spd === '14ms' ? `⚡ ${spd} Live` : spd === '5s' ? `${spd} Burst` : `${spd} Sync`}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* 4. Stat Metric Cards (Screenshot 1 bottom cards) */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
              {/* Card 1: Projects Monitored */}
              <div
                style={{
                  borderRadius: '24px',
                  padding: '24px 28px',
                  backgroundColor: isDark ? 'rgba(16, 18, 22, 0.88)' : '#FFFFFF',
                  backdropFilter: 'blur(20px)',
                  WebkitBackdropFilter: 'blur(20px)',
                  border: isDark ? '1px solid rgba(255, 255, 255, 0.12)' : '1px solid #EFEFEA',
                  boxShadow: isDark ? '0 16px 40px rgba(0,0,0,0.45)' : '0 12px 32px rgba(0,0,0,0.03)',
                }}
              >
                <div style={{ fontSize: '11.5px', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.08em', color: isDark ? 'rgba(255,255,255,0.6)' : '#64748B' }}>
                  PROJECTS MONITORED
                </div>
                <div style={{ fontSize: '42px', fontWeight: 900, letterSpacing: '-0.03em', lineHeight: 1.1, marginTop: '8px', color: isDark ? '#FFFFFF' : '#121314' }}>
                  428
                </div>
                <div style={{ fontSize: '12px', marginTop: '12px', color: isDark ? 'rgba(255,255,255,0.65)' : '#64748B', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span>⚡</span>
                  <span>Live continuous stream • 148,418 pkts</span>
                </div>
              </div>

              {/* Card 2: High & Critical Risk */}
              <div
                style={{
                  borderRadius: '24px',
                  padding: '24px 28px',
                  backgroundColor: isDark ? 'rgba(16, 18, 22, 0.88)' : '#FFFFFF',
                  backdropFilter: 'blur(20px)',
                  WebkitBackdropFilter: 'blur(20px)',
                  border: isDark ? '1px solid rgba(255, 255, 255, 0.12)' : '1px solid #EFEFEA',
                  boxShadow: isDark ? '0 16px 40px rgba(0,0,0,0.45)' : '0 12px 32px rgba(0,0,0,0.03)',
                  position: 'relative',
                }}
              >
                <div style={{ position: 'absolute', top: '24px', right: '24px', width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#EF4444', boxShadow: '0 0 8px #EF4444' }} />
                <div style={{ fontSize: '11.5px', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.08em', color: isDark ? 'rgba(255,255,255,0.6)' : '#64748B' }}>
                  HIGH & CRITICAL RISK
                </div>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginTop: '8px' }}>
                  <span style={{ fontSize: '42px', fontWeight: 900, letterSpacing: '-0.03em', lineHeight: 1.1, color: isDark ? '#FFFFFF' : '#121314' }}>
                    130
                  </span>
                  <span style={{ fontSize: '16px', fontWeight: 700, color: isDark ? 'rgba(255,255,255,0.6)' : '#64748B' }}>
                    Assets
                  </span>
                </div>
                <div style={{ fontSize: '12px', marginTop: '12px', color: '#EF4444', fontWeight: 600 }}>
                  Immediate inter-ministerial audit required
                </div>
              </div>

              {/* Card 3: Average DPHIS Risk */}
              <div
                style={{
                  borderRadius: '24px',
                  padding: '24px 28px',
                  backgroundColor: isDark ? 'rgba(16, 18, 22, 0.88)' : '#FFFFFF',
                  backdropFilter: 'blur(20px)',
                  WebkitBackdropFilter: 'blur(20px)',
                  border: isDark ? '1px solid rgba(255, 255, 255, 0.12)' : '1px solid #EFEFEA',
                  boxShadow: isDark ? '0 16px 40px rgba(0,0,0,0.45)' : '0 12px 32px rgba(0,0,0,0.03)',
                }}
              >
                <div style={{ fontSize: '11.5px', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.08em', color: isDark ? 'rgba(255,255,255,0.6)' : '#64748B' }}>
                  AVERAGE RISK SCORE (DPHIS)
                </div>
                <div style={{ fontSize: '42px', fontWeight: 900, letterSpacing: '-0.03em', lineHeight: 1.1, marginTop: '8px', color: isDark ? '#FFFFFF' : '#121314' }}>
                  {portfolioStats.avgDphis}
                </div>
                <div style={{ fontSize: '12px', marginTop: '12px', color: '#F59E0B', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <CurvedGrowthArrow className="w-3.5 h-3.5" />
                  <span>+4.1 pts higher risk than baseline</span>
                </div>
              </div>

              {/* Card 4: Capital at Drift Risk */}
              <div
                style={{
                  borderRadius: '24px',
                  padding: '24px 28px',
                  backgroundColor: isDark ? 'rgba(16, 18, 22, 0.88)' : '#FFFFFF',
                  backdropFilter: 'blur(20px)',
                  WebkitBackdropFilter: 'blur(20px)',
                  border: isDark ? '1px solid rgba(255, 255, 255, 0.12)' : '1px solid #EFEFEA',
                  boxShadow: isDark ? '0 16px 40px rgba(0,0,0,0.45)' : '0 12px 32px rgba(0,0,0,0.03)',
                }}
              >
                <div style={{ fontSize: '11.5px', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.08em', color: isDark ? 'rgba(255,255,255,0.6)' : '#64748B' }}>
                  EARLY DRIFT DETECTION
                </div>
                <div style={{ fontSize: '42px', fontWeight: 900, letterSpacing: '-0.03em', lineHeight: 1.1, marginTop: '8px', color: '#10B981' }}>
                  14.8%
                </div>
                <div style={{ fontSize: '12px', marginTop: '12px', color: isDark ? 'rgba(255,255,255,0.65)' : '#64748B' }}>
                  Detected before physical milestone breach
                </div>
              </div>
            </div>

            {/* 5. Quick Actions Row & Corridor Drill-Down */}
            <div
              style={{
                borderRadius: '24px',
                padding: '24px 28px',
                backgroundColor: isDark ? 'rgba(16, 18, 22, 0.88)' : '#FFFFFF',
                backdropFilter: 'blur(20px)',
                WebkitBackdropFilter: 'blur(20px)',
                border: isDark ? '1px solid rgba(255, 255, 255, 0.12)' : '1px solid #EFEFEA',
                boxShadow: isDark ? '0 16px 40px rgba(0,0,0,0.45)' : '0 12px 32px rgba(0,0,0,0.03)',
              }}
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-black/5 dark:border-white/10">
                <div>
                  <h3 style={{ fontSize: '18px', fontWeight: 800, color: isDark ? '#FFFFFF' : '#121314', margin: 0 }}>
                    Federal Infrastructure Corridors Under Active Surveillance
                  </h3>
                  <p style={{ fontSize: '13px', color: isDark ? 'rgba(255,255,255,0.6)' : '#64748B', marginTop: '4px', margin: 0 }}>
                    Select any project corridor below to inspect real-time SHAP feature importance drivers and agentic investigation traces.
                  </p>
                </div>

                <div className="flex items-center gap-3">
                  <button
                    type="button"
                    onClick={() => setCurrentTab('projects')}
                    style={{
                      padding: '8px 18px',
                      borderRadius: '12px',
                      backgroundColor: isDark ? '#FFFFFF' : '#121314',
                      color: isDark ? '#070A12' : '#FFFFFF',
                      fontSize: '12px',
                      fontWeight: 700,
                      border: 'none',
                      cursor: 'pointer',
                    }}
                  >
                    View All Corridors →
                  </button>
                  <button
                    type="button"
                    onClick={() => setCurrentTab('assistant')}
                    style={{
                      padding: '8px 18px',
                      borderRadius: '12px',
                      backgroundColor: isDark ? 'rgba(255,255,255,0.08)' : '#F3F4F6',
                      color: isDark ? '#FFFFFF' : '#121314',
                      fontSize: '12px',
                      fontWeight: 700,
                      border: isDark ? '1px solid rgba(255,255,255,0.15)' : '1px solid #E5E7EB',
                      cursor: 'pointer',
                    }}
                  >
                    💬 AI Assistant
                  </button>
                </div>
              </div>

              {/* Top Priority Corridors Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 pt-6">
                {pins.slice(0, 6).map((pin) => (
                  <div
                    key={pin.id}
                    onClick={() => {
                      setSelectedPin(pin);
                      setInsightsModalProjectId(pin.id);
                    }}
                    style={{
                      padding: '18px',
                      borderRadius: '16px',
                      backgroundColor: isDark ? 'rgba(255, 255, 255, 0.04)' : '#F8FAFC',
                      border: isDark ? '1px solid rgba(255, 255, 255, 0.08)' : '1px solid #E2E8F0',
                      cursor: 'pointer',
                      transition: 'all 0.2s ease',
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.backgroundColor = isDark ? 'rgba(255, 255, 255, 0.08)' : '#F1F5F9';
                      e.currentTarget.style.transform = 'translateY(-2px)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.backgroundColor = isDark ? 'rgba(255, 255, 255, 0.04)' : '#F8FAFC';
                      e.currentTarget.style.transform = 'translateY(0)';
                    }}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span style={{ fontSize: '11px', fontFamily: 'monospace', fontWeight: 700, color: '#0284C7' }}>
                        {pin.id}
                      </span>
                      <span
                        style={{
                          fontSize: '11px',
                          fontWeight: 800,
                          padding: '2px 8px',
                          borderRadius: '9999px',
                          backgroundColor: pin.dphis >= 65 ? 'rgba(239, 68, 68, 0.15)' : pin.dphis >= 45 ? 'rgba(245, 158, 11, 0.15)' : 'rgba(16, 185, 129, 0.15)',
                          color: pin.dphis >= 65 ? '#EF4444' : pin.dphis >= 45 ? '#F59E0B' : '#10B981',
                        }}
                      >
                        {pin.dphis} DPHIS
                      </span>
                    </div>

                    <div style={{ fontSize: '14px', fontWeight: 700, color: isDark ? '#FFFFFF' : '#121314', marginBottom: '8px' }}>
                      {pin.name}
                    </div>

                    <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
                      <span>{pin.state}</span>
                      <span style={{ fontWeight: 600 }}>{pin.cost}</span>
                      <span style={{ color: pin.delay.includes('24') ? '#EF4444' : '#F59E0B' }}>+{pin.delay}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )
      ) : currentTab === 'projects' ? (
        <div className="relative z-10 w-full h-full overflow-y-auto buttery-smooth-scroll pt-24 sm:pt-28 pb-24">
          <MyProjects
            currentUser={currentUser}
            pins={pins}
            onSelectProject={(projId) => {
              const found = pins.find(p => p.id === projId);
              if (found) setSelectedPin(found);
              setInsightsModalProjectId(projId);
            }}
            onViewProject={(projId) => {
              const found = pins.find(p => p.id === projId);
              if (found) setSelectedPin(found);
              setInsightsModalProjectId(projId);
            }}
            onNavigateToInsights={(projId) => {
              const found = pins.find(p => p.id === projId);
              if (found) setSelectedPin(found);
              setInsightsModalProjectId(projId);
            }}
            onNavigateToRiskIntelligence={(projId) => {
              const found = pins.find(p => p.id === projId);
              if (found) setSelectedPin(found);
              setInsightsModalProjectId(null);
              setCurrentTab('intelligence');
            }}
            onNavigateToInvestigation={(projId) => {
              const found = pins.find(p => p.id === projId);
              if (found) setSelectedPin(found);
              setInvestigationModalProjectId(projId);
            }}
            onOpenAddProject={() => setShowAddModal(true)}
            onRemoveProject={handleRemoveProject}
          />
        </div>
      ) : currentTab === 'intelligence' ? (
        <div className="relative z-10 w-full h-full overflow-y-auto buttery-smooth-scroll pt-24 sm:pt-28 pb-24">
          <ProjectIntelligence
            projectId={selectedPin?.id || pins[0]?.id}
            currentUser={currentUser}
            allProjects={pins}
            onNavigateToInvestigation={(projId) => {
              setInvestigationModalProjectId(projId);
            }}
            onSelectProject={(projId) => {
              const found = pins.find(p => p.id === projId);
              if (found) setSelectedPin(found);
            }}
            onOpenAddProject={() => setShowAddModal(true)}
            onNavigateBack={() => setCurrentTab('projects')}
          />
        </div>
      ) : currentTab === 'analytics' ? (
        <div className="relative z-10 w-full h-full overflow-y-auto buttery-smooth-scroll pt-24 sm:pt-28 pb-24">
          <Analytics
            allProjects={pins}
            currentUser={currentUser}
            onNavigateToProject={(projId) => {
              const found = pins.find(p => p.id === projId);
              if (found) setSelectedPin(found);
              setInsightsModalProjectId(projId);
            }}
            onNavigateToInvestigation={(projId) => {
              const found = pins.find(p => p.id === projId);
              if (found) setSelectedPin(found);
              setInvestigationModalProjectId(projId);
            }}
            onOpenAddProject={() => setShowAddModal(true)}
          />
        </div>
      ) : currentTab === 'alerts' ? (
        <div className="relative z-10 w-full h-full overflow-y-auto buttery-smooth-scroll pt-24 sm:pt-28 pb-24">
          <Alerts
            currentUser={currentUser}
            pinsCount={pins.length}
            onNavigateToInvestigation={(projId) => setInvestigationModalProjectId(projId)}
            onOpenInvestigation={(projId) => setInvestigationModalProjectId(projId)}
            onNavigateToProject={(projId) => {
              const found = pins.find(p => p.id === projId);
              if (found) setSelectedPin(found);
              setInsightsModalProjectId(projId);
            }}
            onOpenAddProject={() => setShowAddModal(true)}
          />
        </div>
      ) : currentTab === 'assistant' ? (
        <div className="relative z-10 w-full h-full overflow-y-auto buttery-smooth-scroll pt-24 sm:pt-28 pb-24">
          <Assistant
            selectedProjectId={selectedPin?.id}
            currentUser={currentUser}
            allProjects={pins}
            onNavigateToProject={(projId) => {
              const found = pins.find(p => p.id === projId);
              if (found) setSelectedPin(found);
              setInsightsModalProjectId(projId);
            }}
          />
        </div>
      ) : currentTab === 'data_models' ? (
        <div className="relative z-10 w-full h-full overflow-y-auto buttery-smooth-scroll pt-24 sm:pt-28 pb-24">
          <DataModels />
        </div>
      ) : currentTab === 'users_audit' ? (
        <div className="relative z-10 w-full h-full overflow-y-auto buttery-smooth-scroll pt-24 sm:pt-28 pb-24">
          <UsersAudit />
        </div>
      ) : null}

      {/* MODALS */}
      {insightsModalProjectId && (
        <ProjectInsightsModal
          projectId={insightsModalProjectId}
          isOpen={true}
          currentUser={currentUser}
          isAdmin={isAdmin}
          onClose={() => setInsightsModalProjectId(null)}
          onNavigateToInvestigation={(projId) => {
            setInsightsModalProjectId(null);
            setInvestigationModalProjectId(projId);
          }}
          onProjectUpdated={() => {
            if (currentUser) {
              fetchMyProjects(currentUser.username).then(dbProjects => {
                if (dbProjects && dbProjects.length > 0) {
                  const mapped = dbProjects.map(p => ({
                    id: p.project_id,
                    name: p.project_name,
                    state: p.state,
                    latPct: Math.round((((p.location?.latitude || 20) - 8) / (36 - 8)) * 100),
                    lngPct: Math.round((((p.location?.longitude || 78) - 68) / (97 - 68)) * 100),
                    dphis: Math.round(p.dphis || 50),
                    risk: p.risk_level || 'moderate',
                    cost: `₹${p.cost?.revised || 4000} Cr`,
                    delay: `${Math.round((p.dphis || 50) > 70 ? 24 : 6)} mo`
                  }));
                  setPins(mapped);
                }
              }).catch(console.warn);
            }
          }}
        />
      )}

      {investigationModalProjectId && (
        <InvestigationModal
          isOpen={true}
          projectId={investigationModalProjectId}
          onClose={() => setInvestigationModalProjectId(null)}
        />
      )}

      {settingsModalOpen && (
        <SettingsModal
          isOpen={settingsModalOpen}
          initialTab={settingsModalTab}
          onClose={() => setSettingsModalOpen(false)}
          currentUser={currentUser}
          onSignOut={handleSignOut}
        />
      )}

      {showAddModal && (
        <AddProjectModal
          isOpen={showAddModal}
          currentUser={currentUser}
          existingProjectsCount={pins.length}
          onClose={() => setShowAddModal(false)}
          onProjectAdded={(newProj) => {
            const costCr = newProj?.cost?.revised || 4000;
            const newPin: ProjectPin = {
              id: newProj.project_id,
              name: newProj.project_name,
              state: newProj.state || 'National Corridor',
              latPct: Math.round((((newProj.location?.latitude || 20) - 8) / (36 - 8)) * 100),
              lngPct: Math.round((((newProj.location?.longitude || 78) - 68) / (97 - 68)) * 100),
              dphis: Math.round(newProj.dphis || 50),
              risk: newProj.risk_level || 'moderate',
              cost: `₹${costCr} Cr`,
              delay: `${Math.round((newProj.dphis || 50) > 70 ? 24 : 6)} mo`
            };
            setPins(prev => [newPin, ...prev.filter(p => p.id !== newPin.id)]);
            setSelectedPin(newPin);
            setInsightsModalProjectId(newPin.id);
          }}
        />
      )}

      {showCeoModal && (
        <CeoPinManager
          isOpen={showCeoModal}
          onClose={() => setShowCeoModal(false)}
          pins={pins}
          selectedPin={selectedPin}
          onSelectPin={(pin) => {
            setSelectedPin(pin);
            setInsightsModalProjectId(pin.id);
          }}
          onAddPin={(newPin) => {
            setPins(prev => [newPin, ...prev]);
            setSelectedPin(newPin);
          }}
        />
      )}
    </div>
  );
}
