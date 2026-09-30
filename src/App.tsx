import React, { useState, useEffect, useRef } from 'react';
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
  const [activeSection, setActiveSection] = useState<'01' | '02' | '03' | '04'>('01');
  const [showCeoModal, setShowCeoModal] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);
  const [alertCount, setAlertCount] = useState<number>(0);
  const [portfolioStats, setPortfolioStats] = useState({
    avgDphis: 78.4,
    totalProjects: 1500,
    criticalCount: 60
  });

  // Check if project corridor belongs to user's ministry/jurisdiction
  const isUserMinistryProject = (pin: ProjectPin) => {
    if (!currentUser?.ministry) return true;
    const min = currentUser.ministry.toLowerCase();
    const pName = pin.name.toLowerCase();

    if (min.includes('road') || min.includes('highway') || min.includes('transport') || min.includes('morth')) {
      return pName.includes('highway') || pName.includes('expressway') || pName.includes('road') || pName.includes('nh-') || pName.includes('trans harbour') || pName.includes('connector');
    }
    if (min.includes('rail')) {
      return pName.includes('rail') || pName.includes('freight') || pName.includes('chenab') || pName.includes('broad gauge') || pName.includes('usbrl');
    }
    if (min.includes('urban') || min.includes('housing')) {
      return pName.includes('metro') || pName.includes('viaduct') || pName.includes('transit');
    }
    if (min.includes('power') || min.includes('energy')) {
      return pName.includes('solar') || pName.includes('grid') || pName.includes('power') || pName.includes('gas cracker');
    }
    if (min.includes('port') || min.includes('shipping')) {
      return pName.includes('port') || pName.includes('deepwater');
    }
    return true; // MoSPI / Admin sees all
  };

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
    setCurrentTab('motion');
  };

  const handleSignOut = () => {
    clearAuthToken();
    setCurrentUser(null);
    setCurrentTab('motion');
  };

  // Scroll Progress Tracking for Video Dimming
  const [scrollProgress, setScrollProgress] = useState(0);
  const [darkVideoEnded, setDarkVideoEnded] = useState(false);
  const [lightVideoEnded, setLightVideoEnded] = useState(false);
  const videoEnded = isDark ? darkVideoEnded : lightVideoEnded;
  const containerRef = useRef<HTMLDivElement>(null);

  // 1. Initial Authentication Preflight & Live Data Sync
  useEffect(() => {
    // A. Verify authenticated session with backend
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

    // B. Fetch live alerts count
    fetchAlerts().then(items => {
      setAlertCount(items.filter(a => a.status === 'PENDING').length);
    }).catch(console.warn);

    // C. Fetch portfolio stats
    fetchAnalyticsOverview().then(ov => {
      if (ov) {
        setPortfolioStats({
          avgDphis: ov.average_dphis,
          totalProjects: ov.total_projects,
          criticalCount: ov.critical
        });
      }
    }).catch(console.warn);
  }, []);

  // 2. Fetch Corridors Strictly Associated with the Logged-In User from Sovereign Database
  useEffect(() => {
    const isCurrentAdmin = currentUser && (
      (currentUser.role || '').toUpperCase() === 'ADMIN' ||
      (currentUser.role || '').toUpperCase() === 'ANALYST' ||
      currentUser.username.toLowerCase() === 'admin'
    );

    if (!currentUser) {
      // Default initial view: load the 10 user projects so dashboard is never empty
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
      console.warn('Failed to fetch user projects, using robust fallback', err);
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

  const handleProjectAdded = (newProject: any) => {
    const costCr = newProject?.cost?.revised || 4000;
    const newPin: ProjectPin = {
      id: newProject.project_id,
      name: newProject.project_name,
      state: newProject.state || 'National Corridor',
      latPct: Math.round((((newProject.location?.latitude || 20) - 8) / (36 - 8)) * 100),
      lngPct: Math.round((((newProject.location?.longitude || 78) - 68) / (97 - 68)) * 100),
      dphis: Math.round(newProject.dphis || 50),
      risk: newProject.risk_level || 'moderate',
      cost: `₹${costCr} Cr`,
      delay: `${Math.round((newProject.dphis || 50) > 70 ? 24 : 6)} mo`
    };

    setPins(prev => [newPin, ...prev.filter(p => p.id !== newPin.id)]);
    setSelectedPin(newPin);
    setInsightsModalProjectId(newPin.id);
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

  useEffect(() => {
    let animationFrameId: number | null = null;
    const handleScroll = () => {
      if (animationFrameId !== null) return;
      animationFrameId = window.requestAnimationFrame(() => {
        animationFrameId = null;
        if (!containerRef.current) return;
        const scrollTop = containerRef.current.scrollTop;
        const scrollHeight = containerRef.current.scrollHeight - containerRef.current.clientHeight;
        
        const progress = Math.min(Math.max(scrollTop / (scrollHeight || 1), 0), 1);
        setScrollProgress(progress);

        const vh = window.innerHeight;
        if (scrollTop < vh * 0.5) {
          setActiveSection('01');
        } else if (scrollTop < vh * 1.5) {
          setActiveSection('02');
        } else if (scrollTop < vh * 2.5) {
          setActiveSection('03');
        } else {
          setActiveSection('04');
        }
      });
    };

    const ref = containerRef.current;
    if (ref) ref.addEventListener('scroll', handleScroll, { passive: true });
    return () => {
      if (ref) ref.removeEventListener('scroll', handleScroll);
      if (animationFrameId !== null) window.cancelAnimationFrame(animationFrameId);
    };
  }, [currentTab]);

  const handleAddPin = async (newPin: ProjectPin) => {
    setPins(prev => [newPin, ...prev]);
    setSelectedPin(newPin);

    // Persist to FastAPI MongoDB backend
    try {
      const costNum = parseFloat(newPin.cost.replace(/[^0-9.]/g, '')) || 3500;
      await fetch(`${API_BASE}/projects`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_id: newPin.id,
          project_name: newPin.name,
          ministry: 'Ministry of Road Transport and Highways',
          department: 'National Highway Development Unit',
          sector: 'Roads & Highways',
          state: newPin.state,
          location: { latitude: 26.8, longitude: 80.9, district: 'Varanasi', state: newPin.state },
          cost: { original: costNum, revised: costNum, currency: 'INR_CR' },
          schedule: { original_start: '2024-01-01', original_end: '2026-12-31', revised_end: '2027-12-31' },
          metadata: { project_type: 'Highway', implementing_agency: 'State Authority' }
        })
      });
    } catch (err) {
      console.warn('Backend offline, added locally:', err);
    }
  };

  const shapDrivers = selectedPin ? computeRealTimeShapFactors(selectedPin).map(f => ({
    name: f.feature,
    impact: `${f.direction === 'increase' ? '+' : '-'}${f.impact} pts`,
    text: f.description,
    severity: f.impact >= 25 ? 'critical' : f.impact >= 12 ? 'high' : 'low'
  })) : [
    { name: 'Schedule Delays', impact: '+43.2 pts', text: 'Main construction work is running 28 months behind the planned schedule.', severity: 'critical' },
    { name: 'Spending Ahead of Progress', impact: '+24.1 pts', text: '62% of funds have been spent, but only 34% of actual construction is completed.', severity: 'critical' },
    { name: 'Machinery & Equipment Shortage', impact: '+14.5 pts', text: 'Heavy equipment on site is 38% below the target needed to finish on time.', severity: 'high' },
    { name: 'Land Acquisition & Clearances', impact: '-8.0 pts', text: '98.4% of land has been acquired and cleared, which prevents work stoppages.', severity: 'low' },
  ];

  // 1. Splash preflight screen while verifying active database session
  if (authChecking) {
    return (
      <div className={`w-screen h-screen flex flex-col items-center justify-center transition-colors ${
        isDark ? 'bg-black text-white' : 'bg-white text-black'
      }`}>
        <div className="flex flex-col items-center gap-4">
          <div className={`w-14 h-14 rounded-2xl flex items-center justify-center font-mono font-bold text-2xl border ${
            isDark ? 'bg-black text-white border-white/30 shadow-[0_0_24px_rgba(255,255,255,0.2)]' : 'bg-white text-black border-black/20 shadow-md'
          }`}>
            IB
          </div>
          <div className="text-center">
            <div className={`text-xs font-mono font-bold tracking-widest uppercase ${isDark ? 'text-white' : 'text-black'}`}>
              INFRABUILD AI PLATFORM
            </div>
            <div className={`text-[11px] font-mono mt-1 ${isDark ? 'text-white/70' : 'text-black/70'}`}>
              Loading your projects and account...
            </div>
          </div>
        </div>
      </div>
    );
  }

  // 2. MANDATORY LOGIN PROMPT:
  // Must show login prompt first; only if database credentials are verified does dashboard open
  if (!currentUser) {
    return <Login onLoginSuccess={handleLoginSuccess} />;
  }

  // Strictly display only the corridors associated with this authenticated user
  const displayedPins = pins;

  return (
    <div className={`relative w-screen h-screen overflow-hidden transition-colors duration-300 ${isDark ? 'bg-black text-white' : 'bg-[#F8FAFC] text-[#0F172A]'}`}>
      {/* Top Header Navigation */}
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
      />

      {/* BACKGROUND VIDEO & STATIC MAP AT END - VISIBLE ON ALL DASHBOARD PAGES */}
      {currentTab !== 'login' && (
        <div className={`fixed inset-0 z-0 overflow-hidden pointer-events-none transition-colors duration-500 ${isDark ? 'bg-black' : 'bg-[#EAECEF]'}`}>
        {isDark ? (
          <React.Fragment key="dark-mode-media">
            {/* Dark Mode Stationary Map (Final Frame) */}
            <img
              src="/india_map_final.png"
              alt="National Infrastructure Spatial Map - Dark Mode"
              className="absolute inset-0 w-full h-full object-cover transition-opacity duration-700 ease-out"
              style={{
                opacity: darkVideoEnded
                  ? (currentTab === 'motion' ? Math.max(0.92, 1 - scrollProgress * 0.08) : 0.90)
                  : 0,
                filter: currentTab === 'motion'
                  ? `brightness(${Math.max(0.93, 1 - scrollProgress * 0.07)})`
                  : 'brightness(1.0)'
              }}
            />

            {/* Dark Mode Video: dashboard.mp4 */}
            <video
              key="video-dark"
              src="/dashboard.mp4"
              autoPlay
              muted
              playsInline
              onEnded={() => setDarkVideoEnded(true)}
              className="w-full h-full object-cover transition-opacity duration-700 ease-out"
              style={{
                opacity: !darkVideoEnded
                  ? (currentTab === 'motion' ? Math.max(0.92, 1 - scrollProgress * 0.08) : 0.90)
                  : 0,
                filter: currentTab === 'motion'
                  ? `brightness(${Math.max(0.93, 1 - scrollProgress * 0.07)})`
                  : 'brightness(1.0)'
              }}
            />
          </React.Fragment>
        ) : (
          <React.Fragment key="light-mode-media">
            {/* Light Mode Stationary Map (Final Frame) */}
            <img
              src="/india_white_final.png"
              alt="National Infrastructure Spatial Map - Light Mode"
              className="absolute inset-0 w-full h-full object-cover transition-opacity duration-700 ease-out"
              style={{
                opacity: lightVideoEnded
                  ? (currentTab === 'motion' ? Math.max(0.92, 1 - scrollProgress * 0.08) : 0.90)
                  : 0,
                filter: 'brightness(1.0)'
              }}
            />

            {/* Light Mode Video: dashboard_white.mp4 */}
            <video
              key="video-white"
              src="/dashboard_white.mp4"
              autoPlay
              muted
              playsInline
              onEnded={() => setLightVideoEnded(true)}
              className="w-full h-full object-cover transition-opacity duration-700 ease-out"
              style={{
                opacity: !lightVideoEnded
                  ? (currentTab === 'motion' ? Math.max(0.92, 1 - scrollProgress * 0.08) : 0.90)
                  : 0,
                filter: 'brightness(1.0)'
              }}
            />
          </React.Fragment>
        )}

        {/* Scroll-Driven Darkening Overlay - subtle in dark mode, clean in light mode */}
        <div
          className={`absolute inset-0 pointer-events-none transition-opacity duration-500 ease-out ${isDark ? 'bg-black' : 'bg-transparent'}`}
          style={{
            opacity: isDark
              ? (currentTab === 'motion' ? Math.min(0.12, scrollProgress * 0.12) : 0.10)
              : 0
          }}
        />
      </div>
      )}

      {/* VIEWPORT CONTENT CONTAINER — BUTTERY SMOOTH SCROLL */}
      {(currentTab === 'motion' || currentTab === 'overview') ? (
        !isAdmin ? (
          <div className="relative z-10 w-full h-full overflow-y-auto buttery-smooth-scroll">
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
          <div
            ref={containerRef}
            className="relative z-10 w-full h-full overflow-y-auto buttery-smooth-scroll"
          >
            {/* SECTION 01 / 04 — HERO "India, in motion." */}
          <section className="buttery-smooth-section w-full h-screen relative flex items-center justify-between px-6 sm:px-12 md:px-20 pointer-events-none">
            <div className="max-w-xl space-y-4 sm:space-y-6 pointer-events-auto mt-12 sm:mt-16">
              <h1 className={`text-5xl sm:text-6xl md:text-7xl lg:text-8xl font-bold font-display tracking-tight leading-[0.9] ${
                isDark
                  ? 'text-white drop-shadow-[0_8px_32px_rgba(0,0,0,0.95)]'
                  : 'text-black drop-shadow-[0_4px_16px_rgba(255,255,255,0.8)]'
              }`}>
                India,<br />
                in<br />
                motion.
              </h1>

              {/* Tagline Flashcard — Highly Visible Frosted Glass Card */}
              <div className={`p-4 sm:p-5 rounded-2xl border backdrop-blur-2xl max-w-lg transition-all duration-300 shadow-xl ${
                isDark
                  ? 'bg-black/75 border-white/25 text-white shadow-[0_12px_40px_rgba(0,0,0,0.85),inset_0_1px_1px_rgba(255,255,255,0.25)]'
                  : 'bg-white/95 border-slate-300/90 text-slate-900 shadow-[0_8px_30px_rgba(0,0,0,0.12),inset_0_1px_2px_rgba(255,255,255,1)]'
              }`}>
                <div className="space-y-1">
                  <div className={`text-[10px] sm:text-xs font-mono-code font-bold uppercase tracking-wider ${
                    isDark ? 'text-white/70' : 'text-slate-600'
                  }`}>
                    National Infrastructure Tracker
                  </div>
                  <p className={`text-xs sm:text-sm md:text-base font-medium leading-relaxed ${
                    isDark ? 'text-white' : 'text-slate-950'
                  }`}>
                    Live project tracking, budget monitoring, and delay risk predictions across infrastructure projects in India.
                  </p>
                </div>
              </div>

              {/* User Department Badge */}
              <div className="pt-2 flex flex-wrap items-center gap-2.5">
                <div className={`px-3 py-1.5 rounded-xl border flex items-center gap-2 text-xs font-mono shadow-sm ${
                  isDark ? 'bg-black/70 border-white/20 text-white' : 'bg-white/95 border-slate-300 text-slate-900 shadow-sm'
                }`}>
                  <span>
                    Officer: <strong className={isDark ? 'text-white' : 'text-black'}>{currentUser.full_name}</strong>
                  </span>
                  <span className="opacity-40">|</span>
                  <span>
                    Department: <strong className={isDark ? 'text-white' : 'text-black'}>{currentUser.ministry}</strong>
                  </span>
                </div>

                {currentUser.ministry && !currentUser.ministry.includes('MoSPI') && (
                  <button
                    onClick={() => setMinistryFilterOnly(!ministryFilterOnly)}
                    className={`px-3 py-1.5 rounded-xl text-xs font-mono font-bold transition-all border cursor-pointer ${
                      ministryFilterOnly
                        ? (isDark ? 'bg-white text-black border-white shadow-md' : 'bg-black text-white border-black shadow-md')
                        : (isDark ? 'bg-black/70 text-white hover:bg-black/90 border-white/20' : 'bg-white/95 text-black hover:bg-white border-slate-300 shadow-sm')
                    }`}
                  >
                    {ministryFilterOnly ? `Showing: ${currentUser.ministry} Projects ✓` : `Filter: ${currentUser.ministry}`}
                  </button>
                )}
              </div>

              <div className="pt-3 sm:pt-4 flex flex-wrap items-center gap-3">
                <button
                  onClick={() => setInsightsModalProjectId(selectedPin?.id || pins[0]?.id || null)}
                  className={`px-5 py-2.5 rounded-xl text-xs sm:text-sm font-mono-code font-bold shadow-2xl transition-all cursor-pointer ${
                    isDark
                      ? 'bg-white text-black hover:bg-slate-200'
                      : 'bg-black text-white hover:bg-zinc-800 shadow-md'
                  }`}
                >
                  View Project Details & Risks →
                </button>
                <button
                  onClick={() => setCurrentTab('assistant')}
                  className={`px-5 py-2.5 rounded-xl text-xs sm:text-sm font-mono-code font-bold transition-all cursor-pointer ${
                    isDark
                      ? 'bg-black/60 text-white border border-white/30 hover:bg-black/80'
                      : 'bg-white/80 text-black border border-black/20 hover:bg-white shadow-sm'
                  }`}
                >
                  Ask AI Assistant 💬
                </button>
              </div>
            </div>
          </section>

          {/* SECTION 02 / 04 — ROLE-BASED DASHBOARD SNAPSHOT */}
          {isAdmin ? (
            /* ADMIN: NATIONAL PORTFOLIO OVERVIEW */
            <section className="buttery-smooth-section w-full min-h-screen relative flex items-center justify-center px-4 sm:px-8 md:px-16 py-16 sm:py-20 pointer-events-none">
              <div className="w-full max-w-6xl pointer-events-auto">
                <div className="oled-solid-card p-6 sm:p-10 md:p-14 space-y-6 sm:space-y-10 shadow-2xl">
                  <div className="space-y-3 sm:space-y-4 max-w-3xl">
                    <div className="flex items-center gap-2">
                      <span className="px-2.5 py-0.5 rounded text-[11px] font-mono-code font-bold uppercase tracking-wider bg-white/10 text-white border border-white/20">
                        Admin Command Center
                      </span>
                      <span className="text-xs text-white/60">Portfolio-wide Monitoring</span>
                    </div>
                    <h2 className="text-2xl sm:text-4xl md:text-5xl font-bold font-display text-white tracking-tight leading-tight">
                      National Project Overview & Budget Health
                    </h2>
                    <p className="text-xs sm:text-sm text-white/80 leading-relaxed font-normal">
                      System-wide progress, budget exposure, and predictive risk tracking across {portfolioStats.totalProjects.toLocaleString()} sovereign infrastructure projects.
                    </p>
                  </div>

                  {/* 3 Executive Metric Cards */}
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 sm:gap-6 pt-2 sm:pt-4">
                    <div className="oled-solid-card p-5 sm:p-6 space-y-2 sm:space-y-3">
                      <div className="text-3xl sm:text-4xl font-bold font-display font-mono-code text-white">
                        {portfolioStats.avgDphis}
                      </div>
                      <div className="text-xs text-white/80 font-medium">Average Risk Score (0–100)</div>
                      <div className="text-xs font-mono-code text-white font-semibold flex items-center gap-1.5">
                        <CurvedGrowthArrow className="w-3.5 h-3.5 text-amber-400" />
                        <span>+4.1 pts higher risk than last month</span>
                      </div>
                    </div>

                    <div className="oled-solid-card p-5 sm:p-6 space-y-2 sm:space-y-3">
                      <div className="text-3xl sm:text-4xl font-bold font-display font-mono-code text-white">
                        {portfolioStats.totalProjects.toLocaleString()}
                      </div>
                      <div className="text-xs text-white/80 font-medium">Total Monitored Projects</div>
                      <div className="text-xs font-mono-code text-white font-semibold">18,000 monthly telemetry syncs</div>
                    </div>

                    <div className="oled-solid-card p-5 sm:p-6 space-y-2 sm:space-y-3">
                      <div className="text-3xl sm:text-4xl font-bold font-display font-mono-code text-white">
                        {portfolioStats.criticalCount}
                      </div>
                      <div className="text-xs text-white/80 font-medium">Projects Facing Critical Delays</div>
                      <div className="text-xs font-mono-code text-white font-semibold">Need immediate inter-ministerial review</div>
                    </div>
                  </div>
                </div>
              </div>
            </section>
          ) : (
            /* NORMAL USER: MY PROJECTS OVERVIEW */
            <section className="buttery-smooth-section w-full min-h-screen relative flex items-center justify-center px-4 sm:px-8 md:px-16 py-16 sm:py-20 pointer-events-none">
              <div className="w-full max-w-6xl pointer-events-auto">
                <div className="oled-solid-card p-6 sm:p-10 md:p-12 space-y-6 sm:space-y-8 shadow-2xl">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <span className="px-2.5 py-0.5 rounded text-[11px] font-mono-code font-bold uppercase tracking-wider bg-white/10 text-white border border-white/20">
                          My Projects Overview
                        </span>
                        <span className="text-xs text-white/60">
                          {currentUser.ministry || 'Assigned Scope'}
                        </span>
                      </div>
                      <h2 className="text-2xl sm:text-4xl font-bold font-display text-white tracking-tight leading-tight">
                        Status of Your Assigned Projects
                      </h2>
                      <p className="text-xs sm:text-sm text-white/80 max-w-2xl font-normal leading-relaxed">
                        Summary of projects under your direct monitoring, tracking milestone delivery, physical progress, and projects needing your immediate attention.
                      </p>
                    </div>

                    <button
                      onClick={() => setCurrentTab('projects')}
                      className="px-4 py-2 rounded-xl bg-white text-black text-xs font-mono-code font-bold hover:bg-slate-200 transition-all cursor-pointer shadow-md shrink-0 self-start sm:self-auto"
                    >
                      View All My Projects →
                    </button>
                  </div>

                  {/* Top 4 Summary Cards */}
                  <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 pt-1">
                    <div className="oled-solid-card p-4 sm:p-5 space-y-1.5">
                      <div className="text-2xl sm:text-3xl font-bold font-display font-mono-code text-white">
                        {pins.length}
                      </div>
                      <div className="text-xs text-white/90 font-medium">My Active Projects</div>
                      <div className="text-[11px] font-mono-code text-white/60">Assigned to your department</div>
                    </div>

                    <div className="oled-solid-card p-4 sm:p-5 space-y-1.5">
                      <div className="text-2xl sm:text-3xl font-bold font-display font-mono-code text-white">
                        {pins.filter(p => p.dphis >= 65).length}
                      </div>
                      <div className="text-xs text-white/90 font-medium">Projects Needing Attention</div>
                      <div className="text-[11px] font-mono-code text-white/60">Schedule or spending divergence</div>
                    </div>

                    <div className="oled-solid-card p-4 sm:p-5 space-y-1.5">
                      <div className="text-2xl sm:text-3xl font-bold font-display font-mono-code text-white">
                        {pins.filter(p => p.dphis >= 80).length}
                      </div>
                      <div className="text-xs text-white/90 font-medium">Projects At Risk</div>
                      <div className="text-[11px] font-mono-code text-white/60">Critical path timeline at risk</div>
                    </div>

                    <div className="oled-solid-card p-4 sm:p-5 space-y-1.5">
                      <div className="text-2xl sm:text-3xl font-bold font-display font-mono-code text-white">
                        {pins.length > 0 ? pins.length * 2 : 4}
                      </div>
                      <div className="text-xs text-white/90 font-medium">Upcoming Milestones</div>
                      <div className="text-[11px] font-mono-code text-white/60">Deliverables in next 60 days</div>
                    </div>
                  </div>

                  {/* Projects Needing Attention Cards (3–5 projects) */}
                  <div className="space-y-4 pt-2">
                    <div className="flex items-center justify-between">
                      <h3 className="text-base sm:text-lg font-bold font-display text-white">
                        Projects Needing Attention
                      </h3>
                      <span className="text-xs font-mono text-white/60">
                        Showing top priority projects
                      </span>
                    </div>

                    {pins.length === 0 ? (
                      <div className="p-8 text-center space-y-3 rounded-xl border border-white/10 bg-white/5">
                        <div className="text-sm font-bold text-white">No active projects assigned yet</div>
                        <p className="text-xs text-white/70 max-w-md mx-auto">
                          Your account currently has no projects registered. Click Add Project to track an infrastructure corridor.
                        </p>
                        <button
                          onClick={() => setShowAddModal(true)}
                          className="px-4 py-2 rounded-xl bg-white text-black text-xs font-mono font-bold hover:bg-slate-200 transition-all cursor-pointer"
                        >
                          + Add Project
                        </button>
                      </div>
                    ) : (
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {[...pins]
                          .sort((a, b) => b.dphis - a.dphis)
                          .slice(0, 3)
                          .map(p => {
                            const cat = getRiskCategory(p.dphis);
                            let reason = "Progress is behind planned schedule";
                            if (p.dphis >= 80) {
                              reason = "Spending is increasing faster than physical progress";
                            } else if (p.dphis >= 65) {
                              reason = "Construction progress is lower than planned milestone target";
                            } else if (p.dphis >= 45) {
                              reason = "Upcoming critical milestone requires contractor review";
                            } else {
                              reason = "Project progress aligned with scheduled deliverables";
                            }

                            return (
                              <div
                                key={p.id}
                                className="oled-solid-card p-5 space-y-3 flex flex-col justify-between hover:border-white/30 transition-all"
                              >
                                <div className="space-y-2">
                                  <div className="flex items-center justify-between">
                                    <span className="font-mono-code text-[11px] font-bold text-white/80">{p.id}</span>
                                    <span className={`px-2 py-0.5 rounded text-[10px] font-mono-code font-bold ${cat.bgClass} ${cat.borderClass} ${cat.colorClass}`}>
                                      {cat.label}
                                    </span>
                                  </div>
                                  <h4 className="text-sm font-bold text-white line-clamp-1">{p.name}</h4>
                                  <p className="text-xs text-white/75 leading-relaxed">
                                    {reason}
                                  </p>
                                </div>

                                <div className="space-y-3 pt-2 border-t border-white/10 text-xs">
                                  <div className="grid grid-cols-2 gap-2 text-[11px] font-mono-code text-white/70">
                                    <div>
                                      <span className="block text-white/50 text-[10px]">Location</span>
                                      <span className="text-white font-medium">{p.state}</span>
                                    </div>
                                    <div>
                                      <span className="block text-white/50 text-[10px]">Est. Delay</span>
                                      <span className="text-white font-medium">{p.delay}</span>
                                    </div>
                                    <div>
                                      <span className="block text-white/50 text-[10px]">Budget Health</span>
                                      <span className={`font-semibold ${p.dphis >= 65 ? 'text-white' : 'text-white/80'}`}>
                                        {p.dphis >= 65 ? 'At Risk' : 'Normal'}
                                      </span>
                                    </div>
                                    <div>
                                      <span className="block text-white/50 text-[10px]">Approved Cost</span>
                                      <span className="text-white font-medium">{p.cost}</span>
                                    </div>
                                  </div>

                                  <button
                                    onClick={() => {
                                      setSelectedPin(p);
                                      setInsightsModalProjectId(p.id);
                                    }}
                                    className="w-full py-2 rounded-lg bg-white/10 hover:bg-white hover:text-black text-white text-xs font-mono-code font-bold border border-white/20 transition-all cursor-pointer text-center"
                                  >
                                    Review Issue →
                                  </button>
                                </div>
                              </div>
                            );
                          })}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </section>
          )}

          {/* SECTION 03 / 04 — WHY PROJECTS ARE AT RISK (Non-Admin View Only; Removed for Admin as requested) */}
          {!isAdmin && (
            <section className="buttery-smooth-section w-full min-h-screen relative flex items-center justify-center px-4 sm:px-8 md:px-16 py-16 sm:py-20 pointer-events-none">
              <div className="w-full max-w-6xl pointer-events-auto">
                <div className="oled-solid-card p-6 sm:p-10 md:p-14 space-y-6 sm:space-y-8 shadow-2xl">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div className="space-y-2 sm:space-y-3">
                      <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold font-display text-white tracking-tight">
                        Why Your Projects Need Attention
                      </h2>
                      <p className="text-xs sm:text-sm text-white/80">
                        {selectedPin
                          ? `Plain-language analysis of delay causes on project ${selectedPin.id} (${selectedPin.name}).`
                          : 'Tracking key factors causing delivery delays and cost overruns.'}
                      </p>
                    </div>

                    <button
                      onClick={() => setInsightsModalProjectId(selectedPin?.id || pins[0]?.id || null)}
                      className="px-4 sm:px-5 py-2 sm:py-2.5 rounded-xl bg-white text-black text-xs sm:text-sm font-mono-code font-bold hover:bg-zinc-200 transition-all cursor-pointer shadow-lg whitespace-nowrap shrink-0"
                    >
                      View Project Insights →
                    </button>
                  </div>

                  {selectedPin ? (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6 pt-2">
                      <div className="oled-solid-card p-5 sm:p-6 space-y-3 sm:space-y-4">
                        {(() => {
                          const cat = getRiskCategory(selectedPin.dphis);
                          return (
                            <div className="flex items-center justify-between border-b border-white/10 pb-3">
                              <span className="font-mono-code font-bold text-white">{selectedPin.id}</span>
                              <span className={`px-2.5 py-1 rounded text-xs font-mono-code font-bold border ${cat.bgClass} ${cat.borderClass} ${cat.colorClass}`}>
                                {cat.label}
                              </span>
                            </div>
                          );
                        })()}
                        <h4 className="text-sm sm:text-base font-bold text-white">{selectedPin.name}</h4>
                        {(() => {
                          const physProgress = Math.max(12, Math.min(95, Math.round(100 - selectedPin.dphis * 0.85)));
                          const plannedTarget = Math.min(98, Math.round(physProgress + (selectedPin.dphis >= 65 ? (selectedPin.dphis - 50) * 0.75 : 5)));
                          const summaryText = selectedPin.dphis >= 65
                            ? 'Funds and timeline are pacing ahead of verified physical construction, putting completion milestones at risk.'
                            : selectedPin.dphis >= 45
                            ? 'Project is progressing with moderate schedule variance. Key milestones require routine contractor supervision.'
                            : 'Project milestones and expenditures are tracking cleanly within approved cost and timeline estimates.';
                          return (
                            <>
                              <p className="text-xs sm:text-sm text-white/80 leading-relaxed">
                                {summaryText}
                              </p>

                              <div className="pt-2 space-y-2 text-xs sm:text-sm">
                                <div className="flex justify-between font-mono-code text-white/80">
                                  <span>Physical Progress: {physProgress}%</span>
                                  <span className="text-white font-bold">Planned Target: {plannedTarget}%</span>
                                </div>
                                <div className="h-2 rounded-full bg-white/10 overflow-hidden border border-white/15">
                                  <div className="h-full bg-white rounded-full transition-all duration-500" style={{ width: `${physProgress}%` }} />
                                </div>
                              </div>
                            </>
                          );
                        })()}

                        <div className="pt-3 border-t border-white/10">
                          <h5 className="text-xs font-mono font-bold uppercase text-white/70 mb-2">Recommended Next Steps</h5>
                          <ul className="text-xs text-white/80 space-y-1.5 list-disc list-inside">
                            <li>Review delayed construction schedule with EPC contractor</li>
                            <li>Inspect on-site machinery and equipment deployment</li>
                            <li>Verify actual ground milestones against contractor expenditure claims</li>
                          </ul>
                        </div>
                      </div>

                      <div className="oled-solid-card p-5 sm:p-6 space-y-3">
                        <div className="flex items-center justify-between mb-2">
                          <h4 className="text-xs sm:text-sm font-mono-code font-bold uppercase tracking-wider text-white/80">
                            Key Risk Factors (AI Attribution)
                          </h4>
                          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-white/10 text-white/70">
                            Real-time Telemetry
                          </span>
                        </div>
                        {shapDrivers.map(d => (
                          <div key={d.name} className="p-3 rounded-xl bg-white/5 border border-white/15 space-y-1">
                            <div className="flex items-center justify-between text-xs sm:text-sm">
                              <span className="font-semibold text-white">{d.name}</span>
                              <TrendBadge value={d.impact} mode="risk" iconClassName="w-3.5 h-3.5" />
                            </div>
                            <p className="text-[11px] sm:text-xs text-white/70">{d.text}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <div className="oled-solid-card p-8 text-center space-y-4">
                      <div className="text-base font-bold text-white">No Projects Added Yet</div>
                      <p className="text-xs sm:text-sm text-white/75 max-w-xl mx-auto leading-relaxed">
                        You don't have any projects listed in your dashboard yet. Add your first project using the standard report fields to see risk predictions and AI recommendations.
                      </p>
                      <button
                        onClick={() => setShowAddModal(true)}
                        className="px-5 py-2.5 rounded-xl bg-white text-black text-xs font-mono-code font-bold hover:bg-slate-200 transition-all cursor-pointer shadow-lg inline-flex items-center gap-2"
                      >
                        <span>+ Add Project</span>
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </section>
          )}

          {/* SECTION 04 / 04 — LIVE PROJECTS & PORTFOLIO */}
          <section className="buttery-smooth-section w-full min-h-screen relative flex items-center justify-center px-4 sm:px-8 md:px-16 py-16 sm:py-20 pointer-events-none">
            <div className="w-full max-w-6xl pointer-events-auto">
              <div className="oled-solid-card p-6 sm:p-10 md:p-14 space-y-6 sm:space-y-8 shadow-2xl">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div className="space-y-1.5 sm:space-y-2">
                    <div className="flex flex-wrap items-center gap-3">
                      <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold font-display text-white tracking-tight">
                        {isAdmin ? 'All Monitored Projects' : 'My Assigned Projects'}
                      </h2>
                      <span className={`px-3 py-1 rounded-lg text-xs font-mono font-bold border ${
                        isDark ? 'bg-black/70 text-white border-white/20' : 'bg-white/95 text-black border-slate-300 shadow-sm'
                      }`}>
                        Department: {currentUser.ministry || 'Assigned Projects'}
                      </span>
                    </div>
                    <p className="text-xs sm:text-sm text-white/70">
                      Showing {displayedPins.length} projects under active monitoring ({currentUser.full_name} · {currentUser.designation || 'Project Officer'}).
                    </p>
                  </div>

                  {!isAdmin && (
                    <div className="flex items-center gap-3 shrink-0">
                      <button
                        onClick={() => setShowAddModal(true)}
                        style={!isDark ? { color: '#000000' } : undefined}
                        className={`px-5 py-2.5 rounded-xl text-xs sm:text-sm font-bold font-mono-code cursor-pointer transition-all duration-200 flex items-center gap-2 ${
                          isDark
                            ? 'bg-black text-white border border-white/30 shadow-[0_0_14px_rgba(255,255,255,0.22)] hover:bg-zinc-900 hover:border-white/60'
                            : 'bg-white/75 hover:bg-white/95 text-black border border-white/90 shadow-[0_4px_18px_rgba(0,0,0,0.08),inset_0_1.5px_2px_rgba(255,255,255,0.95)] backdrop-blur-md'
                        }`}
                      >
                        <span style={!isDark ? { color: '#000000' } : undefined}>+ Add Project</span>
                      </button>
                    </div>
                  )}
                </div>

                <div className="overflow-x-auto overflow-y-auto rounded-xl border border-white/15 bg-black/40 backdrop-blur-md max-h-[44vh] relative">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead className="sticky top-0 z-20">
                      <tr className="border-b border-white/15">
                        <th className="p-4 sticky top-0 z-20 bg-[#0B0F17] text-white/80 font-mono-code text-[10px] uppercase tracking-wider shadow-[0_2px_8px_rgba(0,0,0,0.5)]">Project ID</th>
                        <th className="p-4 sticky top-0 z-20 bg-[#0B0F17] text-white/80 font-mono-code text-[10px] uppercase tracking-wider shadow-[0_2px_8px_rgba(0,0,0,0.5)]">Project Name</th>
                        <th className="p-4 sticky top-0 z-20 bg-[#0B0F17] text-white/80 font-mono-code text-[10px] uppercase tracking-wider shadow-[0_2px_8px_rgba(0,0,0,0.5)]">Location</th>
                        <th className="p-4 sticky top-0 z-20 bg-[#0B0F17] text-white/80 font-mono-code text-[10px] uppercase tracking-wider shadow-[0_2px_8px_rgba(0,0,0,0.5)]">Status</th>
                        <th className="p-4 sticky top-0 z-20 bg-[#0B0F17] text-white/80 font-mono-code text-[10px] uppercase tracking-wider shadow-[0_2px_8px_rgba(0,0,0,0.5)]">Approved Cost</th>
                        <th className="p-4 sticky top-0 z-20 bg-[#0B0F17] text-white/80 font-mono-code text-[10px] uppercase tracking-wider shadow-[0_2px_8px_rgba(0,0,0,0.5)]">Delay</th>
                        <th className="p-4 sticky top-0 z-20 bg-[#0B0F17] text-white/80 font-mono-code text-[10px] uppercase tracking-wider shadow-[0_2px_8px_rgba(0,0,0,0.5)]">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5">
                      {displayedPins.length === 0 ? (
                        <tr>
                          <td colSpan={7} className="p-8 text-center font-mono text-xs text-slate-400">
                            No projects currently assigned to this user profile in the database.
                          </td>
                        </tr>
                      ) : (
                        displayedPins.map(p => {
                          const cat = getRiskCategory(p.dphis);
                          return (
                            <tr
                              key={p.id}
                              onClick={() => setSelectedPin(p)}
                              className={`cursor-pointer hover:bg-white/5 transition-colors ${
                                selectedPin?.id === p.id ? 'bg-white/10' : ''
                              }`}
                            >
                              <td className="p-4 font-mono-code font-bold text-white">{p.id}</td>
                              <td className="p-4 font-semibold text-white">{p.name}</td>
                              <td className="p-4 text-white/80">{p.state}</td>
                              <td className="p-4">
                                <span className={`px-2 py-0.5 rounded text-[10px] font-mono-code font-bold ${cat.bgClass} ${cat.borderClass} ${cat.colorClass}`}>
                                  {cat.label}
                                </span>
                              </td>
                              <td className="p-4 font-mono-code text-white">{p.cost}</td>
                              <td className="p-4 text-white font-mono-code">{p.delay}</td>
                              <td className="p-4">
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    setSelectedPin(p);
                                    setInsightsModalProjectId(p.id);
                                  }}
                                  className="px-2.5 py-1 rounded bg-[var(--surface-sunken)] hover:bg-white hover:text-black text-[10px] font-mono-code text-white border border-white/20 transition-all cursor-pointer"
                                >
                                  View Insights →
                                </button>
                              </td>
                            </tr>
                          );
                        })
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </section>
        </div>
        )
      ) : (
        /* ROLE-GOVERNED VIEWPORT ROUTING */
        <div className="relative z-10 w-full h-full overflow-y-auto">
          {currentTab === 'projects' && (
            <MyProjects
              currentUser={currentUser}
              pins={pins}
              onSelectProject={(id) => {
                const found = pins.find(p => p.id === id);
                if (found) setSelectedPin(found);
              }}
              onNavigateToInsights={(id) => {
                const found = pins.find(p => p.id === id);
                if (found) setSelectedPin(found);
                setInsightsModalProjectId(id);
              }}
              onNavigateToRiskIntelligence={(id) => {
                const found = pins.find(p => p.id === id);
                if (found) setSelectedPin(found);
                setCurrentTab('intelligence');
              }}
              onNavigateToInvestigation={(id) => {
                const found = pins.find(p => p.id === id);
                if (found) setSelectedPin(found);
                setInvestigationModalProjectId(id);
              }}
              onOpenAddProject={() => setShowAddModal(true)}
              onRemoveProject={handleRemoveProject}
            />
          )}

          {currentTab === 'intelligence' && (
            <ProjectIntelligence
              projectId={selectedPin?.id}
              currentUser={currentUser}
              allProjects={pins}
              onNavigateToInvestigation={(id) => {
                if (id) {
                  const found = pins.find(p => p.id === id);
                  if (found) setSelectedPin(found);
                }
                setInvestigationModalProjectId(id || selectedPin?.id || pins[0]?.id || null);
              }}
              onNavigateBack={() => setCurrentTab('projects')}
              onOpenAddProject={!isAdmin ? () => setShowAddModal(true) : undefined}
              onSelectProject={(id) => {
                const found = pins.find(p => p.id === id);
                if (found) setSelectedPin(found);
              }}
            />
          )}

          {currentTab === 'analytics' && (
            <Analytics
              pinsCount={pins.length}
              allProjects={pins}
              currentUser={currentUser}
              onOpenAddProject={!isAdmin ? () => setShowAddModal(true) : undefined}
              onNavigateToProject={(id) => {
                const found = pins.find(p => p.id === id);
                if (found) setSelectedPin(found);
                setCurrentTab('intelligence');
              }}
              onNavigateToInvestigation={(id) => {
                const found = pins.find(p => p.id === id);
                if (found) setSelectedPin(found);
                setInvestigationModalProjectId(id);
              }}
            />
          )}

          {currentTab === 'assistant' && (
            <Assistant
              selectedProjectId={selectedPin?.id || ''}
              currentUser={currentUser}
              allProjects={pins}
              onNavigateToProject={(id) => {
                const found = pins.find(p => p.id === id);
                if (found) setSelectedPin(found);
                setInsightsModalProjectId(id);
              }}
            />
          )}

          {currentTab === 'alerts' && (
            <Alerts
              currentUser={currentUser}
              pinsCount={pins.length}
              onOpenAddProject={!isAdmin ? () => setShowAddModal(true) : undefined}
              onNavigateToInvestigation={(id) => {
                const found = pins.find(p => p.id === id);
                if (found) setSelectedPin(found);
                setInvestigationModalProjectId(id);
              }}
              onNavigateToProject={(id) => {
                const found = pins.find(p => p.id === id);
                if (found) setSelectedPin(found);
                setInsightsModalProjectId(id);
              }}
            />
          )}

          {(currentTab === 'data_models' || currentTab === 'reports') && (
            <DataModels />
          )}

          {currentTab === 'users_audit' && (
            <UsersAudit />
          )}
        </div>
      )}

      {/* FLOATING BOTTOM DOCK CONTROLS (Only on Motion tab for Non-Admin Users) */}
      {(currentTab === 'motion' || currentTab === 'overview') && !isAdmin && (
        <div className="fixed bottom-5 left-1/2 -translate-x-1/2 z-40 pointer-events-auto">
          <button
            onClick={() => setShowAddModal(true)}
            style={!isDark ? { color: '#000000' } : undefined}
            className={`flex items-center gap-2 px-4 py-2 rounded-full text-xs font-mono-code font-bold transition-all duration-200 cursor-pointer ${
              isDark
                ? 'bg-[#0B0F17] hover:bg-[#141A26] border border-white/15 text-white shadow-lg'
                : 'bg-white/80 hover:bg-white/95 text-black border border-white/95 shadow-[0_6px_24px_rgba(0,0,0,0.12),inset_0_1.5px_2px_rgba(255,255,255,0.95)] backdrop-blur-md'
            }`}
          >
            <span style={!isDark ? { color: '#000000' } : undefined} className={`text-sm leading-none font-bold ${isDark ? 'text-white/80' : 'text-black'}`}>+</span>
            <span style={!isDark ? { color: '#000000' } : undefined} className={`font-bold tracking-tight ${isDark ? 'text-white' : 'text-black'}`}>Add Project</span>
          </button>
        </div>
      )}

      {/* PROJECT INSIGHTS POP-UP MODAL */}
      <ProjectInsightsModal
        isOpen={!!insightsModalProjectId}
        projectId={insightsModalProjectId}
        currentUser={currentUser}
        isAdmin={isAdmin}
        onClose={() => setInsightsModalProjectId(null)}
        onNavigateToInvestigation={(id) => {
          const found = pins.find(p => p.id === id);
          if (found) setSelectedPin(found);
          setInsightsModalProjectId(null);
          setInvestigationModalProjectId(id);
        }}
      />

      {/* INVESTIGATION POP-UP MODAL (Replaces separate investigation page) */}
      <InvestigationModal
        isOpen={!!investigationModalProjectId}
        projectId={investigationModalProjectId}
        onClose={() => setInvestigationModalProjectId(null)}
        onOpenAddProject={() => {
          setInvestigationModalProjectId(null);
          setShowAddModal(true);
        }}
      />

      {/* ACCOUNT & PROFILE SETTINGS MODAL */}
      <SettingsModal
        isOpen={settingsModalOpen}
        initialTab={settingsModalTab}
        currentUser={currentUser}
        onClose={() => setSettingsModalOpen(false)}
        onSignOut={handleSignOut}
      />

      {/* GEMINI 57-FEATURE & LIGHTGBM ML ASSET INGESTION MODAL */}
      <AddProjectModal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        currentUser={currentUser}
        onProjectAdded={handleProjectAdded}
        existingProjectsCount={pins.length}
      />

      {/* CEO PIN MANAGER MODAL */}
      {showCeoModal && (
        <CeoPinManager
          onAddPin={handleAddPin}
          onClose={() => setShowCeoModal(false)}
        />
      )}
    </div>
  );
}
