import React, { useState, useEffect, useRef } from 'react';
import HeaderNav, { ActiveTab } from './components/HeaderNav';
import CeoPinManager, { ProjectPin } from './components/CeoPinManager';
import ProjectIntelligence from './pages/ProjectIntelligence';
import Investigation from './pages/Investigation';
import Analytics from './pages/Analytics';
import Assistant from './pages/Assistant';
import Alerts from './pages/Alerts';
import { useTheme } from './hooks/useTheme';
import { fetchProjects, fetchAlerts, fetchAnalyticsOverview } from './lib/api';

const initialPins: ProjectPin[] = [
  { id: 'P1024', name: 'NH-48 Varanasi-Ranchi Expressway', state: 'Uttar Pradesh', latPct: 38, lngPct: 54, dphis: 91, risk: 'critical', cost: '₹4,218 Cr', delay: '28 mo' },
  { id: 'P0847', name: 'Metro Rail Phase III', state: 'Tamil Nadu', latPct: 82, lngPct: 46, dphis: 84, risk: 'critical', cost: '₹12,450 Cr', delay: '14 mo' },
  { id: 'P1156', name: 'Solar Energy Grid, Jaisalmer', state: 'Rajasthan', latPct: 34, lngPct: 24, dphis: 78, risk: 'high', cost: '₹6,820 Cr', delay: '11 mo' },
  { id: 'P0392', name: 'Port Modernisation Project', state: 'Andhra Pradesh', latPct: 68, lngPct: 58, dphis: 76, risk: 'high', cost: '₹3,190 Cr', delay: '9 mo' },
  { id: 'P0771', name: 'Broad Gauge Rail Conversion', state: 'Bihar', latPct: 40, lngPct: 64, dphis: 74, risk: 'high', cost: '₹2,870 Cr', delay: '18 mo' },
  { id: 'P0512', name: 'Mumbai Trans Harbour Link', state: 'Maharashtra', latPct: 58, lngPct: 30, dphis: 45, risk: 'low', cost: '₹17,840 Cr', delay: '4 mo' },
  { id: 'P0982', name: 'Dedicated Freight Corridor', state: 'Gujarat', latPct: 48, lngPct: 18, dphis: 32, risk: 'low', cost: '₹8,120 Cr', delay: '2 mo' },
  { id: 'P0411', name: 'Assam Gas Cracker Project', state: 'Assam', latPct: 34, lngPct: 84, dphis: 55, risk: 'moderate', cost: '₹5,410 Cr', delay: '6 mo' },
];

export default function App() {
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  const [currentTab, setCurrentTab] = useState<ActiveTab>('motion');
  const [pins, setPins] = useState<ProjectPin[]>(initialPins);
  const [selectedPin, setSelectedPin] = useState<ProjectPin>(initialPins[0]);
  const [activeSection, setActiveSection] = useState<'01' | '02' | '03' | '04'>('01');
  const [showCeoModal, setShowCeoModal] = useState(false);
  const [alertCount, setAlertCount] = useState<number>(0);
  const [portfolioStats, setPortfolioStats] = useState({
    avgDphis: 78.4,
    totalProjects: 1500,
    criticalCount: 60
  });

  // Scroll Progress Tracking for Video Dimming
  const [scrollProgress, setScrollProgress] = useState(0);
  const [darkVideoEnded, setDarkVideoEnded] = useState(false);
  const [lightVideoEnded, setLightVideoEnded] = useState(false);
  const videoEnded = isDark ? darkVideoEnded : lightVideoEnded;
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // 1. Fetch live projects from FastAPI
    fetchProjects().then(dbProjects => {
      if (dbProjects && dbProjects.length > 0) {
        const mappedPins: ProjectPin[] = dbProjects.slice(0, 15).map(p => ({
          id: p.project_id,
          name: p.project_name,
          state: p.state,
          latPct: Math.round(((p.location.latitude - 8) / (36 - 8)) * 100),
          lngPct: Math.round(((p.location.longitude - 68) / (97 - 68)) * 100),
          dphis: Math.round(p.dphis || 50),
          risk: p.risk_level || 'moderate',
          cost: `₹${p.cost.revised} Cr`,
          delay: `${Math.round(p.dphis > 70 ? 24 : 6)} mo`
        }));
        setPins(mappedPins);
        setSelectedPin(mappedPins[0]);
      }
    }).catch(console.warn);

    // 2. Fetch live alerts count
    fetchAlerts().then(items => {
      setAlertCount(items.filter(a => a.status === 'PENDING').length);
    }).catch(console.warn);

    // 3. Fetch portfolio stats
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

  useEffect(() => {
    const handleScroll = () => {
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
    };

    const ref = containerRef.current;
    if (ref) ref.addEventListener('scroll', handleScroll, { passive: true });
    return () => ref?.removeEventListener('scroll', handleScroll);
  }, [currentTab]);

  const handleAddPin = async (newPin: ProjectPin) => {
    setPins(prev => [newPin, ...prev]);
    setSelectedPin(newPin);

    // Persist to FastAPI MongoDB backend
    try {
      const costNum = parseFloat(newPin.cost.replace(/[^0-9.]/g, '')) || 3500;
      await fetch('http://localhost:8000/api/v1/projects', {
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

  const shapDrivers = [
    { name: 'Critical Path Schedule Deviation', impact: '+43.2 pts', text: 'Superstructure Phase 1 milestone buffer exhausted; critical path slip: Δt = +28 mos', severity: 'critical' },
    { name: 'CapEx Disbursement–Execution Disparity', impact: '+24.1 pts', text: 'Disbursement velocity (62%) diverges from certified physical completion (34%) by 28 pts', severity: 'critical' },
    { name: 'Contractual Mechanization Deficit', impact: '+14.5 pts', text: 'On-site machinery mobilization 38% below Detailed Project Report (DPR) baseline', severity: 'high' },
    { name: 'Right-of-Way (RoW) Liquidation Efficacy', impact: '-8.0 pts', text: 'Cadastral land acquisition 98.4% finalized with statutory encumbrance clearance', severity: 'low' },
  ];

  return (
    <div className={`relative w-screen h-screen overflow-hidden transition-colors duration-300 ${isDark ? 'bg-black text-white' : 'bg-[#F8FAFC] text-[#0F172A]'}`}>
      {/* Top Header Navigation */}
      <HeaderNav
        currentTab={currentTab}
        onTabChange={setCurrentTab}
        alertCount={alertCount}
      />

      {/* BACKGROUND VIDEO & STATIC MAP AT END - VISIBLE ON ALL PAGES */}
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
          className={`absolute inset-0 pointer-events-none transition-opacity duration-300 ease-out ${isDark ? 'bg-black' : 'bg-transparent'}`}
          style={{
            opacity: isDark
              ? (currentTab === 'motion' ? Math.min(0.12, scrollProgress * 0.12) : 0.10)
              : 0
          }}
        />
      </div>

      {/* VIEWPORT CONTENT CONTAINER */}
      {currentTab === 'motion' ? (
        <div
          ref={containerRef}
          className="relative z-10 w-full h-full overflow-y-auto scroll-smooth snap-y snap-mandatory"
        >
          {/* SECTION 01 / 04 — HERO "India, in motion." */}
          <section className="snap-start w-full h-screen relative flex items-center justify-between px-6 sm:px-12 md:px-20 pointer-events-none">
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

              <p className={`text-xs sm:text-sm md:text-base font-semibold leading-relaxed max-w-md pt-2 ${
                isDark ? 'text-white/90 drop-shadow-md' : 'text-black'
              }`}>
                Continuous econometric surveillance and stochastic risk decomposition across 28 sub-national infrastructure corridors.
              </p>

              <div className="pt-3 sm:pt-4 flex flex-wrap items-center gap-3">
                <button
                  onClick={() => setCurrentTab('intelligence')}
                  className={`px-5 py-2.5 rounded-xl text-xs sm:text-sm font-mono-code font-bold shadow-2xl transition-all cursor-pointer ${
                    isDark
                      ? 'bg-white text-black hover:bg-slate-200'
                      : 'bg-black text-white hover:bg-zinc-800 shadow-md'
                  }`}
                >
                  Inspect Portfolio Risk Matrix →
                </button>
                <button
                  onClick={() => setCurrentTab('assistant')}
                  className={`px-5 py-2.5 rounded-xl text-xs sm:text-sm font-mono-code font-bold transition-all cursor-pointer ${
                    isDark
                      ? 'bg-black/60 text-white border border-white/30 hover:bg-black/80'
                      : 'bg-white/80 text-black border border-black/20 hover:bg-white shadow-sm'
                  }`}
                >
                  Consult Analytical Copilot 💬
                </button>
              </div>
            </div>
          </section>

          {/* SECTION 02 / 04 — NATIONAL SNAPSHOT */}
          <section className="snap-start w-full min-h-screen relative flex items-center justify-center px-4 sm:px-8 md:px-16 py-16 sm:py-20 pointer-events-none">
            <div className="w-full max-w-6xl pointer-events-auto">
              <div className="oled-solid-card p-6 sm:p-10 md:p-14 space-y-6 sm:space-y-10 shadow-2xl">
                <div className="space-y-3 sm:space-y-4 max-w-3xl">
                  <h2 className="text-2xl sm:text-4xl md:text-5xl font-bold font-display text-white tracking-tight leading-tight">
                    Macroeconomic Capital Velocity & Inter-Corridor Stress Surveillance
                  </h2>

                  <p className="text-xs sm:text-sm text-white/80 leading-relaxed font-normal">
                    Longitudinal portfolio health synthesized dynamically across {portfolioStats.totalProjects.toLocaleString()} sovereign infrastructure assets spanning 18,000 empirical snapshot vectors.
                  </p>
                </div>

                {/* 3 Executive Metric Cards */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 sm:gap-6 pt-2 sm:pt-4">
                  <div className="oled-solid-card p-5 sm:p-6 space-y-2 sm:space-y-3">
                    <div className="text-3xl sm:text-4xl font-bold font-display font-mono-code text-white">
                      {portfolioStats.avgDphis}
                    </div>
                    <div className="text-xs text-white/80 font-medium">Portfolio Mean Health Index (DPHIS)</div>
                    <div className="text-xs font-mono-code text-white font-semibold">+4.1 pts longitudinal risk acceleration</div>
                  </div>

                  <div className="oled-solid-card p-5 sm:p-6 space-y-2 sm:space-y-3">
                    <div className="text-3xl sm:text-4xl font-bold font-display font-mono-code text-white">
                      {portfolioStats.totalProjects.toLocaleString()}
                    </div>
                    <div className="text-xs text-white/80 font-medium">Active Strategic Capital Assets</div>
                    <div className="text-xs font-mono-code text-white font-semibold">18,000 multi-temporal telemetry audits</div>
                  </div>

                  <div className="oled-solid-card p-5 sm:p-6 space-y-2 sm:space-y-3">
                    <div className="text-3xl sm:text-4xl font-bold font-display font-mono-code text-white">
                      {portfolioStats.criticalCount}
                    </div>
                    <div className="text-xs text-white/80 font-medium">High-Vulnerability Intervention Thresholds</div>
                    <div className="text-xs font-mono-code text-white font-semibold">Algorithmic anomaly detection active</div>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* SECTION 03 / 04 — RISK INTELLIGENCE & SHAP DRIVERS */}
          <section className="snap-start w-full min-h-screen relative flex items-center justify-center px-4 sm:px-8 md:px-16 py-16 sm:py-20 pointer-events-none">
            <div className="w-full max-w-6xl pointer-events-auto">
              <div className="oled-solid-card p-6 sm:p-10 md:p-14 space-y-6 sm:space-y-8 shadow-2xl">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div className="space-y-2 sm:space-y-3">
                    <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold font-display text-white tracking-tight">
                      Empirical Risk Decomposition & Additive Shapley Attribution
                    </h2>
                    <p className="text-xs sm:text-sm text-white/80">
                      Isolating marginal covariate contributions driving probabilistic failure escalation on corridor {selectedPin.id}.
                    </p>
                  </div>

                  <button
                    onClick={() => setCurrentTab('intelligence')}
                    className="px-4 sm:px-5 py-2 sm:py-2.5 rounded-xl bg-white text-black text-xs sm:text-sm font-mono-code font-bold hover:bg-zinc-200 transition-all cursor-pointer shadow-lg whitespace-nowrap shrink-0"
                  >
                    Forensic Audit Dossier →
                  </button>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6 pt-2">
                  <div className="oled-solid-card p-5 sm:p-6 space-y-3 sm:space-y-4">
                    <div className="flex items-center justify-between border-b border-white/10 pb-3">
                      <span className="font-mono-code font-bold text-white">{selectedPin.id}</span>
                      <span className="px-2.5 py-1 rounded bg-white/10 text-white text-xs font-mono-code font-bold border border-white/20">
                        DPHIS: {selectedPin.dphis} · Critical Risk Cohort
                      </span>
                    </div>
                    <h4 className="text-sm sm:text-base font-bold text-white">{selectedPin.name}</h4>
                    <p className="text-xs sm:text-sm text-white/80 leading-relaxed">
                      Certified physical completion (34%) exhibits severe hysteresis relative to cumulative financial disbursement (62%), inducing acute milestone recovery friction.
                    </p>

                    <div className="pt-2 space-y-2 text-xs sm:text-sm">
                      <div className="flex justify-between font-mono-code text-white/80">
                        <span>Physical Capitalization: 34%</span>
                        <span className="text-white font-bold">Sanctioned Target Baseline: 78%</span>
                      </div>
                      <div className="h-2 rounded-full bg-white/10 overflow-hidden border border-white/15">
                        <div className="h-full bg-white rounded-full" style={{ width: '34%' }} />
                      </div>
                    </div>
                  </div>

                  <div className="oled-solid-card p-5 sm:p-6 space-y-3">
                    <h4 className="text-xs sm:text-sm font-mono-code font-bold uppercase tracking-wider text-white/80 mb-2">
                      Top Additive Shapley Attribution Vectors (SHAP)
                    </h4>
                    {shapDrivers.map(d => (
                      <div key={d.name} className="p-3 rounded-xl bg-white/5 border border-white/15 space-y-1">
                        <div className="flex items-center justify-between text-xs sm:text-sm">
                          <span className="font-semibold text-white">{d.name}</span>
                          <span className="font-mono-code font-bold text-white">
                            {d.impact}
                          </span>
                        </div>
                        <p className="text-[11px] sm:text-xs text-white/70">{d.text}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* SECTION 04 / 04 — LIVE PROJECTS & CEO ADMIN COMMAND */}
          <section className="snap-start w-full min-h-screen relative flex items-center justify-center px-4 sm:px-8 md:px-16 py-16 sm:py-20 pointer-events-none">
            <div className="w-full max-w-6xl pointer-events-auto">
              <div className="oled-solid-card p-6 sm:p-10 md:p-14 space-y-6 sm:space-y-8 shadow-2xl">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div className="space-y-1.5 sm:space-y-2">
                    <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold font-display text-white tracking-tight">
                      National Infrastructure Portfolio Ledger & Capital Telemetry
                    </h2>
                  </div>

                  <div className="flex items-center gap-3 shrink-0">
                    <button
                      onClick={() => setShowCeoModal(true)}
                      className="px-5 py-2.5 rounded-xl bg-black text-white text-xs sm:text-sm font-bold font-mono-code cursor-pointer border border-white/30 shadow-[0_0_14px_rgba(255,255,255,0.22)] hover:bg-zinc-900 hover:border-white/60 transition-all duration-200 flex items-center gap-2"
                    >
                      <span>+ Ingest Capital Asset</span>
                    </button>
                  </div>
                </div>

                <div className="overflow-x-auto overflow-y-auto rounded-xl border border-white/15 bg-black/40 backdrop-blur-md max-h-[44vh] relative">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead className="sticky top-0 z-20">
                      <tr className="border-b border-white/15">
                        <th className="p-4 sticky top-0 z-20 bg-[#0B0F17] text-white/80 font-mono-code text-[10px] uppercase tracking-wider shadow-[0_2px_8px_rgba(0,0,0,0.5)]">Asset Token</th>
                        <th className="p-4 sticky top-0 z-20 bg-[#0B0F17] text-white/80 font-mono-code text-[10px] uppercase tracking-wider shadow-[0_2px_8px_rgba(0,0,0,0.5)]">Infrastructure Nomenclature</th>
                        <th className="p-4 sticky top-0 z-20 bg-[#0B0F17] text-white/80 font-mono-code text-[10px] uppercase tracking-wider shadow-[0_2px_8px_rgba(0,0,0,0.5)]">Jurisdictional State</th>
                        <th className="p-4 sticky top-0 z-20 bg-[#0B0F17] text-white/80 font-mono-code text-[10px] uppercase tracking-wider shadow-[0_2px_8px_rgba(0,0,0,0.5)]">DPHIS Index</th>
                        <th className="p-4 sticky top-0 z-20 bg-[#0B0F17] text-white/80 font-mono-code text-[10px] uppercase tracking-wider shadow-[0_2px_8px_rgba(0,0,0,0.5)]">Sanctioned Outlay</th>
                        <th className="p-4 sticky top-0 z-20 bg-[#0B0F17] text-white/80 font-mono-code text-[10px] uppercase tracking-wider shadow-[0_2px_8px_rgba(0,0,0,0.5)]">Critical Delay</th>
                        <th className="p-4 sticky top-0 z-20 bg-[#0B0F17] text-white/80 font-mono-code text-[10px] uppercase tracking-wider shadow-[0_2px_8px_rgba(0,0,0,0.5)]">Analytical Protocol</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5">
                      {pins.map(p => (
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
                          <td className="p-4 font-mono-code font-bold text-white">{p.dphis}</td>
                          <td className="p-4 font-mono-code text-white">{p.cost}</td>
                          <td className="p-4 text-white font-mono-code">{p.delay}</td>
                          <td className="p-4">
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                setSelectedPin(p);
                                setCurrentTab('intelligence');
                              }}
                              className="px-2.5 py-1 rounded bg-[var(--surface-sunken)] hover:bg-white hover:text-black text-[10px] font-mono-code text-white border border-white/20 transition-all cursor-pointer"
                            >
                              Inspect →
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </section>
        </div>
      ) : (
        /* DEEP INTELLIGENCE MODULES VIEWPORT */
        <div className="relative z-10 w-full h-full overflow-y-auto">
          {currentTab === 'intelligence' && (
            <ProjectIntelligence
              projectId={selectedPin.id}
              onNavigateToInvestigation={() => setCurrentTab('investigation')}
              onSelectProject={(id) => {
                const found = pins.find(p => p.id === id);
                if (found) setSelectedPin(found);
              }}
            />
          )}

          {currentTab === 'investigation' && (
            <Investigation projectId={selectedPin.id} />
          )}

          {currentTab === 'analytics' && (
            <Analytics onNavigateToProject={(id) => {
              const found = pins.find(p => p.id === id);
              if (found) setSelectedPin(found);
              setCurrentTab('intelligence');
            }} />
          )}

          {currentTab === 'assistant' && (
            <Assistant
              selectedProjectId={selectedPin.id}
              onNavigateToProject={(id) => {
                const found = pins.find(p => p.id === id);
                if (found) setSelectedPin(found);
                setCurrentTab('intelligence');
              }}
            />
          )}

          {currentTab === 'alerts' && (
            <Alerts
              onNavigateToInvestigation={(id) => {
                const found = pins.find(p => p.id === id);
                if (found) setSelectedPin(found);
                setCurrentTab('investigation');
              }}
            />
          )}
        </div>
      )}

      {/* FLOATING BOTTOM DOCK CONTROLS (Only on Motion tab) */}
      {currentTab === 'motion' && (
        <div className="fixed bottom-5 left-1/2 -translate-x-1/2 z-40 pointer-events-auto">
          <button
            onClick={() => setShowCeoModal(true)}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-[#0B0F17] hover:bg-[#141A26] border border-white/10 text-white text-xs font-mono-code font-medium shadow-md transition-colors duration-150 cursor-pointer"
          >
            <span className="text-white/80 text-sm leading-none font-normal">+</span>
            <span className="text-white">Ingest Capital Asset</span>
          </button>
        </div>
      )}

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
