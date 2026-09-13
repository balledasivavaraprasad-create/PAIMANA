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
    { name: 'Schedule Deviation Rate', impact: '+43 pts', text: 'Superstructure Phase 1 milestone delayed by 28 months', severity: 'critical' },
    { name: 'Financial–Physical Progress Gap', impact: '+24 pts', text: '62% funds disbursed vs 34% physical progress achieved', severity: 'critical' },
    { name: 'Contractor Equipment Deployment', impact: '+14 pts', text: 'Machinery on site 38% below DPR requirements', severity: 'high' },
    { name: 'Right of Way (RoW) Clearance', impact: '-8 pts', text: 'Land acquisition 98% cleared by state authority', severity: 'low' },
  ];

  return (
    <div className={`relative w-screen h-screen overflow-hidden transition-colors duration-300 ${isDark ? 'bg-black text-white' : 'bg-[#F8FAFC] text-[#0F172A]'}`}>
      {/* Top Header Navigation */}
      <HeaderNav
        currentTab={currentTab}
        onTabChange={setCurrentTab}
        alertCount={alertCount}
      />

      {/* BACKGROUND VIDEO - VISIBLE ON ALL PAGES (STOPS ON INDIA IN MOTION) */}
      <div className="fixed inset-0 z-0 overflow-hidden pointer-events-none bg-black">
        <video
          autoPlay
          muted
          playsInline
          onEnded={(e) => { e.currentTarget.pause(); }}
          className="w-full h-full object-cover transition-all duration-300 ease-out"
          style={{
            opacity: currentTab === 'motion'
              ? Math.max(0.65, 0.95 - scrollProgress * 0.30)
              : 0.85,
            filter: currentTab === 'motion'
              ? `brightness(${Math.max(0.80, 1 - scrollProgress * 0.20)}) blur(${scrollProgress * 2}px)`
              : 'brightness(0.90) blur(0.5px)',
            transform: `scale(${1 + (currentTab === 'motion' ? scrollProgress * 0.03 : 0.02)})`
          }}
        >
          <source src="/video.mp4" type="video/mp4" />
        </video>
        {/* Scroll-Driven Darkening Overlay - subtle so background and foreground blend seamlessly */}
        <div
          className="absolute inset-0 pointer-events-none transition-opacity duration-300 ease-out bg-black"
          style={{
            opacity: currentTab === 'motion'
              ? Math.min(0.35, 0.10 + scrollProgress * 0.25)
              : 0.18
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
              <h1 className="text-5xl sm:text-6xl md:text-7xl lg:text-8xl font-bold font-display tracking-tight text-white leading-[0.9] drop-shadow-[0_8px_32px_rgba(0,0,0,0.95)]">
                India,<br />
                in<br />
                motion.
              </h1>

              <p className="text-xs sm:text-sm md:text-base text-white/90 font-medium leading-relaxed max-w-sm pt-2 drop-shadow-md">
                A living predictive intelligence model of the nation's infrastructure network across 28 states.
              </p>

              <div className="pt-3 sm:pt-4 flex flex-wrap items-center gap-3">
                <button
                  onClick={() => setCurrentTab('intelligence')}
                  className="px-5 py-2.5 rounded-xl bg-white text-black text-xs sm:text-sm font-mono-code font-bold shadow-2xl hover:bg-slate-200 transition-all cursor-pointer"
                >
                  Explore Risk Intelligence →
                </button>
                <button
                  onClick={() => setCurrentTab('assistant')}
                  className="px-5 py-2.5 rounded-xl bg-black/60 text-white border border-white/30 text-xs sm:text-sm font-mono-code font-bold hover:bg-black/80 transition-all cursor-pointer"
                >
                  Ask AI Assistant 💬
                </button>
              </div>
            </div>
          </section>

          {/* SECTION 02 / 04 — NATIONAL SNAPSHOT */}
          <section className="snap-start w-full min-h-screen relative flex items-center justify-center px-4 sm:px-8 md:px-16 py-16 sm:py-20 pointer-events-none">
            <div className="w-full max-w-6xl pointer-events-auto">
              <div className="oled-solid-card p-6 sm:p-10 md:p-14 space-y-6 sm:space-y-10 shadow-2xl">
                <div className="space-y-3 sm:space-y-4 max-w-2xl">
                  <h2 className="text-2xl sm:text-4xl md:text-5xl font-bold font-display text-white tracking-tight leading-tight">
                    The network is moving.<br />
                    Watch where it bends.
                  </h2>

                  <p className="text-xs sm:text-sm text-white/80 leading-relaxed font-normal">
                    Portfolio health is aggregated dynamically from {portfolioStats.totalProjects.toLocaleString()} monitored projects in the intelligence database.
                  </p>
                </div>

                {/* 3 Executive Metric Cards */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 sm:gap-6 pt-2 sm:pt-4">
                  <div className="oled-solid-card p-5 sm:p-6 space-y-2 sm:space-y-3">
                    <div className="text-3xl sm:text-4xl font-bold font-display font-mono-code text-white">
                      {portfolioStats.avgDphis}
                    </div>
                    <div className="text-xs text-white/80 font-medium">Average DPHIS Score</div>
                    <div className="text-xs font-mono-code text-white font-semibold">+4.1 pts trend acceleration</div>
                  </div>

                  <div className="oled-solid-card p-5 sm:p-6 space-y-2 sm:space-y-3">
                    <div className="text-3xl sm:text-4xl font-bold font-display font-mono-code text-white">
                      {portfolioStats.totalProjects.toLocaleString()}
                    </div>
                    <div className="text-xs text-white/80 font-medium">Monitored Infrastructure Projects</div>
                    <div className="text-xs font-mono-code text-white font-semibold">18,000 monthly snapshots</div>
                  </div>

                  <div className="oled-solid-card p-5 sm:p-6 space-y-2 sm:space-y-3">
                    <div className="text-3xl sm:text-4xl font-bold font-display font-mono-code text-white">
                      {portfolioStats.criticalCount}
                    </div>
                    <div className="text-xs text-white/80 font-medium">Critical Intervention Flags</div>
                    <div className="text-xs font-mono-code text-white font-semibold">Automated alert engine active</div>
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
                      Quantified risk drivers across national corridors.
                    </h2>
                    <p className="text-xs sm:text-sm text-white/80">
                      SHAP feature attribution explaining score escalation on critical projects like {selectedPin.id}.
                    </p>
                  </div>

                  <button
                    onClick={() => setCurrentTab('intelligence')}
                    className="px-4 sm:px-5 py-2 sm:py-2.5 rounded-xl bg-white text-black text-xs sm:text-sm font-mono-code font-bold hover:bg-zinc-200 transition-all cursor-pointer shadow-lg whitespace-nowrap shrink-0"
                  >
                    Deep Inspection →
                  </button>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6 pt-2">
                  <div className="oled-solid-card p-5 sm:p-6 space-y-3 sm:space-y-4">
                    <div className="flex items-center justify-between border-b border-white/10 pb-3">
                      <span className="font-mono-code font-bold text-white">{selectedPin.id}</span>
                      <span className="px-2.5 py-1 rounded bg-white/10 text-white text-xs font-mono-code font-bold border border-white/20">
                        Score: {selectedPin.dphis} · High / Elevated
                      </span>
                    </div>
                    <h4 className="text-sm sm:text-base font-bold text-white">{selectedPin.name}</h4>
                    <p className="text-xs sm:text-sm text-white/80 leading-relaxed">
                      Physical progress (34%) lags financial utilisation (62%) by 28 percentage points, creating severe milestone recovery risk.
                    </p>

                    <div className="pt-2 space-y-2 text-xs sm:text-sm">
                      <div className="flex justify-between font-mono-code text-white/80">
                        <span>Physical Execution: 34%</span>
                        <span className="text-white font-bold">Target: 78%</span>
                      </div>
                      <div className="h-2 rounded-full bg-white/10 overflow-hidden border border-white/15">
                        <div className="h-full bg-white rounded-full" style={{ width: '34%' }} />
                      </div>
                    </div>
                  </div>

                  <div className="oled-solid-card p-5 sm:p-6 space-y-3">
                    <h4 className="text-xs sm:text-sm font-mono-code font-bold uppercase tracking-wider text-white/80 mb-2">
                      Top Quantified SHAP Impact Drivers
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
                      Nationwide Project Telemetry
                    </h2>
                  </div>

                  <div className="flex items-center gap-3 shrink-0">
                    <button
                      onClick={() => setShowCeoModal(true)}
                      className="px-5 py-2.5 rounded-xl bg-black text-white text-xs sm:text-sm font-bold font-mono-code cursor-pointer border border-white/30 shadow-[0_0_14px_rgba(255,255,255,0.22)] hover:bg-zinc-900 hover:border-white/60 transition-all duration-200 flex items-center gap-2"
                    >
                      <span>+ Add Project</span>
                    </button>
                  </div>
                </div>

                <div className="overflow-x-auto rounded-xl border border-[var(--border-hairline)] bg-[var(--surface-sunken)] max-h-[48vh]">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="bg-[var(--bg-surface)] border-b border-[var(--border-hairline)] text-white/70 font-mono-code text-[10px] uppercase sticky top-0 z-10">
                        <th className="p-4">Pin ID</th>
                        <th className="p-4">Project Name</th>
                        <th className="p-4">State</th>
                        <th className="p-4">DPHIS</th>
                        <th className="p-4">Budget</th>
                        <th className="p-4">Delay</th>
                        <th className="p-4">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[var(--border-hairline)]">
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
                              Analyze →
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
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-40 flex items-center gap-3 pointer-events-auto">
          <div className="oled-solid-card px-4 py-2 flex items-center text-xs font-mono-code shadow-2xl">
            <button
              onClick={() => setShowCeoModal(true)}
              className="flex items-center gap-1.5 px-3 py-1 rounded-md bg-[var(--surface-sunken)] hover:bg-[var(--accent-soft)] text-[var(--text-primary)] font-medium cursor-pointer border border-[var(--border-hairline)]"
            >
              <span>+ Add Project</span>
            </button>
          </div>
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
