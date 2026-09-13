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

      {/* NON-LOOPING BACKGROUND VIDEO */}
      <div className="fixed inset-0 z-0 overflow-hidden pointer-events-none bg-black">
        <video
          autoPlay
          muted
          playsInline
          onEnded={(e) => { e.currentTarget.pause(); }}
          className="w-full h-full object-cover transition-all duration-300 ease-out"
          style={{
            opacity: currentTab === 'motion'
              ? Math.max(0.50, 0.95 - scrollProgress * 0.45)
              : 0.18,
            filter: currentTab === 'motion'
              ? `brightness(${Math.max(0.68, 1 - scrollProgress * 0.32)}) blur(${scrollProgress * 2}px)`
              : 'brightness(0.35) blur(10px)',
            transform: `scale(${1 + (currentTab === 'motion' ? scrollProgress * 0.03 : 0.05)})`
          }}
        >
          <source src="/video.mp4" type="video/mp4" />
        </video>
        {/* Scroll-Driven Darkening Overlay */}
        <div
          className="absolute inset-0 pointer-events-none transition-opacity duration-300 ease-out bg-black"
          style={{
            opacity: currentTab === 'motion'
              ? Math.min(0.48, 0.15 + scrollProgress * 0.33)
              : 0.85
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
          <section className="snap-start w-full h-screen relative flex items-center justify-between px-12 md:px-20 pointer-events-none">
            <div className="max-w-xl space-y-6 pointer-events-auto mt-16">
              <div className="text-[10px] font-mono-code font-bold tracking-[0.25em] uppercase text-slate-300 drop-shadow-md">
                NATIONAL INFRASTRUCTURE INTELLIGENCE · FASTAPI & MONGODB
              </div>

              <h1 className="text-6xl md:text-7xl lg:text-8xl font-bold font-display tracking-tight text-white leading-[0.9] drop-shadow-[0_8px_32px_rgba(0,0,0,0.95)]">
                India,<br />
                in<br />
                motion.
              </h1>

              <p className="text-sm md:text-base text-slate-200 font-medium leading-relaxed max-w-sm pt-2 drop-shadow-md">
                A living predictive intelligence model of the nation's infrastructure network across 28 states.
              </p>

              <div className="pt-4 flex items-center gap-3">
                <button
                  onClick={() => setCurrentTab('intelligence')}
                  className="px-5 py-2.5 rounded-xl bg-white text-black text-xs font-mono-code font-bold shadow-2xl hover:bg-slate-200 transition-all cursor-pointer"
                >
                  Explore Risk Intelligence →
                </button>
                <button
                  onClick={() => setCurrentTab('assistant')}
                  className="px-5 py-2.5 rounded-xl bg-black/60 text-white border border-white/30 text-xs font-mono-code font-bold hover:bg-black/80 transition-all cursor-pointer"
                >
                  Ask AI Assistant 💬
                </button>
              </div>
            </div>
          </section>

          {/* SECTION 02 / 04 — NATIONAL SNAPSHOT */}
          <section className="snap-start w-full min-h-screen relative flex items-center justify-center px-8 md:px-16 py-20 pointer-events-none">
            <div className="w-full max-w-6xl pointer-events-auto">
              <div className="oled-solid-card p-10 md:p-14 space-y-10 shadow-2xl">
                <div className="space-y-4 max-w-2xl">
                  <div className="text-xs font-mono-code font-bold tracking-widest uppercase text-[var(--accent)] flex items-center gap-2">
                    <span>02 / 04</span>
                    <span>•</span>
                    <span>NATIONAL SNAPSHOT</span>
                  </div>

                  <h2 className="text-4xl md:text-5xl font-bold font-display text-[var(--text-primary)] tracking-tight leading-tight">
                    The network is moving.<br />
                    Watch where it bends.
                  </h2>

                  <p className="text-sm text-[var(--text-secondary)] leading-relaxed font-normal">
                    Portfolio health is aggregated dynamically from {portfolioStats.totalProjects.toLocaleString()} monitored projects in the intelligence database.
                  </p>
                </div>

                {/* 3 Executive Metric Cards */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-4">
                  <div className="oled-solid-card p-6 space-y-3">
                    <div className="text-4xl font-bold font-display font-mono-code text-[var(--text-primary)]">
                      {portfolioStats.avgDphis}
                    </div>
                    <div className="text-xs text-[var(--text-secondary)] font-medium">Average DPHIS Score</div>
                    <div className="text-xs font-mono-code text-[var(--risk-critical)] font-semibold">+4.1 pts trend acceleration</div>
                  </div>

                  <div className="oled-solid-card p-6 space-y-3">
                    <div className="text-4xl font-bold font-display font-mono-code text-[var(--text-primary)]">
                      {portfolioStats.totalProjects.toLocaleString()}
                    </div>
                    <div className="text-xs text-[var(--text-secondary)] font-medium">Monitored Infrastructure Projects</div>
                    <div className="text-xs font-mono-code text-emerald-500 font-semibold">18,000 monthly snapshots</div>
                  </div>

                  <div className="oled-solid-card p-6 space-y-3">
                    <div className="text-4xl font-bold font-display font-mono-code text-[var(--text-primary)]">
                      {portfolioStats.criticalCount}
                    </div>
                    <div className="text-xs text-[var(--text-secondary)] font-medium">Critical Intervention Flags</div>
                    <div className="text-xs font-mono-code text-[var(--risk-low)] font-semibold">Automated alert engine active</div>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* SECTION 03 / 04 — RISK INTELLIGENCE & SHAP DRIVERS */}
          <section className="snap-start w-full min-h-screen relative flex items-center justify-center px-8 md:px-16 py-20 pointer-events-none">
            <div className="w-full max-w-6xl pointer-events-auto">
              <div className="oled-solid-card p-10 md:p-14 space-y-8 shadow-2xl">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div className="space-y-3">
                    <div className="text-xs font-mono-code font-bold tracking-widest uppercase text-[var(--accent)] flex items-center gap-2">
                      <span>03 / 04</span>
                      <span>•</span>
                      <span>PREDICTIVE DPHIS & EXPLAINABLE AI</span>
                    </div>

                    <h2 className="text-3xl md:text-4xl font-bold font-display text-[var(--text-primary)] tracking-tight">
                      Quantified risk drivers across national corridors.
                    </h2>
                    <p className="text-xs text-[var(--text-secondary)]">
                      SHAP feature attribution explaining score escalation on critical projects like {selectedPin.id}.
                    </p>
                  </div>

                  <button
                    onClick={() => setCurrentTab('intelligence')}
                    className="px-4 py-2 rounded-xl bg-[var(--accent)] text-white text-xs font-mono-code font-bold hover:bg-[var(--accent-hover)] transition-all cursor-pointer shadow-lg whitespace-nowrap"
                  >
                    Deep Inspection →
                  </button>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 pt-2">
                  <div className="oled-solid-card p-6 space-y-4">
                    <div className="flex items-center justify-between border-b border-[var(--border-hairline)] pb-3">
                      <span className="font-mono-code font-bold text-[var(--accent)]">{selectedPin.id}</span>
                      <span className="px-2.5 py-1 rounded bg-red-500/10 text-[var(--risk-critical)] text-xs font-mono-code font-bold border border-red-500/20">
                        DPHIS {selectedPin.dphis} ({selectedPin.risk.toUpperCase()})
                      </span>
                    </div>
                    <h4 className="text-sm font-bold text-[var(--text-primary)]">{selectedPin.name}</h4>
                    <p className="text-xs text-[var(--text-secondary)] leading-relaxed">
                      Physical progress (34%) lags financial utilisation (62%) by 28 percentage points, creating severe milestone recovery risk.
                    </p>

                    <div className="pt-2 space-y-2 text-xs">
                      <div className="flex justify-between font-mono-code text-[var(--text-secondary)]">
                        <span>Physical Execution: 34%</span>
                        <span className="text-[var(--accent)]">Target: 78%</span>
                      </div>
                      <div className="h-2 rounded-full bg-[var(--surface-sunken)] overflow-hidden border border-[var(--border-hairline)]">
                        <div className="h-full bg-[var(--accent)] rounded-full" style={{ width: '34%' }} />
                      </div>
                    </div>
                  </div>

                  <div className="oled-solid-card p-6 space-y-3">
                    <h4 className="text-xs font-mono-code font-bold uppercase tracking-wider text-[var(--text-muted)] mb-2">
                      Top Quantified SHAP Impact Drivers
                    </h4>
                    {shapDrivers.map(d => (
                      <div key={d.name} className="p-3 rounded-xl bg-[var(--surface-sunken)] border border-[var(--border-hairline)] space-y-1">
                        <div className="flex items-center justify-between text-xs">
                          <span className="font-semibold text-[var(--text-primary)]">{d.name}</span>
                          <span className={`font-mono-code font-bold ${d.severity === 'low' ? 'text-[var(--risk-low)]' : 'text-[var(--risk-critical)]'}`}>
                            {d.impact}
                          </span>
                        </div>
                        <p className="text-[10px] text-[var(--text-secondary)]">{d.text}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* SECTION 04 / 04 — LIVE PROJECTS & CEO ADMIN COMMAND */}
          <section className="snap-start w-full min-h-screen relative flex items-center justify-center px-8 md:px-16 py-20 pointer-events-none">
            <div className="w-full max-w-6xl pointer-events-auto">
              <div className="oled-solid-card p-10 md:p-14 space-y-8 shadow-2xl">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div className="space-y-2">
                    <div className="text-xs font-mono-code font-bold tracking-widest uppercase text-[var(--accent)] flex items-center gap-2">
                      <span>04 / 04</span>
                      <span>•</span>
                      <span>ADMIN & CEO COMMAND</span>
                    </div>

                    <h2 className="text-3xl md:text-4xl font-bold font-display text-[var(--text-primary)] tracking-tight">
                      Nationwide Project Telemetry
                    </h2>
                  </div>

                  <div className="flex items-center gap-3">
                    <button
                      onClick={() => setShowCeoModal(true)}
                      className="px-5 py-2.5 rounded-xl bg-black text-white text-xs font-bold font-mono-code cursor-pointer border border-white/30 shadow-[0_0_14px_rgba(255,255,255,0.22)] hover:bg-zinc-900 hover:border-white/60 hover:shadow-[0_0_18px_rgba(255,255,255,0.35)] transition-all duration-200 flex items-center gap-2"
                    >
                      <span>+ Add Project</span>
                    </button>
                  </div>
                </div>

                <div className="overflow-x-auto rounded-xl border border-[var(--border-hairline)] bg-[var(--surface-sunken)] max-h-[48vh]">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="bg-[var(--bg-surface)] border-b border-[var(--border-hairline)] text-[var(--text-muted)] font-mono-code text-[10px] uppercase sticky top-0 z-10">
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
                          className={`cursor-pointer hover:bg-[var(--accent-soft)] transition-colors ${
                            selectedPin?.id === p.id ? 'bg-[var(--accent-soft)]' : ''
                          }`}
                        >
                          <td className="p-4 font-mono-code font-bold text-[var(--accent)]">{p.id}</td>
                          <td className="p-4 font-semibold text-[var(--text-primary)]">{p.name}</td>
                          <td className="p-4 text-[var(--text-secondary)]">{p.state}</td>
                          <td className="p-4 font-mono-code font-bold text-[var(--risk-critical)]">{p.dphis}</td>
                          <td className="p-4 font-mono-code text-[var(--text-primary)]">{p.cost}</td>
                          <td className="p-4 text-amber-500 font-mono-code">{p.delay}</td>
                          <td className="p-4">
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                setSelectedPin(p);
                                setCurrentTab('intelligence');
                              }}
                              className="px-2.5 py-1 rounded bg-[var(--surface-sunken)] hover:bg-black hover:text-white text-[10px] font-mono-code text-[var(--accent)] border border-[var(--border-hairline)] transition-all cursor-pointer"
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
          <div className="oled-solid-card px-4 py-2 flex items-center gap-3 text-xs font-mono-code shadow-2xl">
            <button
              onClick={() => setShowCeoModal(true)}
              className="flex items-center gap-1.5 px-3 py-1 rounded-md bg-[var(--surface-sunken)] hover:bg-[var(--accent-soft)] text-[var(--text-primary)] font-medium cursor-pointer border border-[var(--border-hairline)]"
            >
              <span>+ Add Project</span>
            </button>

            <span className="text-[var(--text-muted)]">|</span>

            <span className="text-[var(--text-secondary)]">
              MODEL <strong className="text-[var(--text-primary)]">{activeSection}</strong> / 04
            </span>
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
