import React, { useState, useEffect, useMemo } from 'react';
import GlassCard from '../components/GlassCard';
import { 
  fetchProjectPredictions, fetchProjectRisk, fetchProject, fetchProjects, triggerInvestigation,
  PredictionData, RiskData, ProjectData, InvestigationReport, UserProfile 
} from '../lib/api';
import { ProjectPin } from '../components/CeoPinManager';
import { getRiskCategory } from '../lib/risk';

interface Props {
  projectId?: string;
  currentUser?: UserProfile | null;
  allProjects?: ProjectPin[];
  onNavigateToInvestigation: (projectId: string) => void;
  onSelectProject?: (projectId: string) => void;
  onOpenAddProject?: () => void;
}

function DHPISGauge({ score }: { score: number }) {
  const size = 220;
  const strokeWidth = 14;
  const center = size / 2;
  const radius = center - strokeWidth - 4;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (Math.min(100, Math.max(0, score)) / 100) * circumference;
  const cat = getRiskCategory(score);

  return (
    <div className="flex flex-col items-center justify-center py-2 sm:py-4">
      <div className="relative w-48 h-48 sm:w-56 sm:h-56 flex items-center justify-center">
        <svg className="w-full h-full -rotate-90" viewBox={`0 0 ${size} ${size}`}>
          {/* Track Circle */}
          <circle
            cx={center}
            cy={center}
            r={radius}
            stroke="rgba(255, 255, 255, 0.15)"
            strokeWidth={strokeWidth}
            fill="transparent"
          />
          {/* Progress Arc in crisp solid white */}
          <circle
            cx={center}
            cy={center}
            r={radius}
            stroke="#ffffff"
            strokeWidth={strokeWidth}
            fill="transparent"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            className="transition-all duration-1000 ease-out"
          />
        </svg>

        {/* Centered Content */}
        <div className="absolute inset-0 flex flex-col items-center justify-center text-center p-2">
          <span className="font-mono-code font-bold text-4xl sm:text-5xl text-white tracking-tight">
            {score}
          </span>
          <span className={`mt-1 text-xs sm:text-sm font-mono-code font-bold uppercase tracking-wider ${cat.colorClass}`}>
            {cat.label}
          </span>
          <span className="text-xs font-mono-code text-white/70 mt-0.5">
            DPHIS Index · {cat.badgeText}
          </span>
        </div>
      </div>
    </div>
  );
}

function MiniDphisGauge({ score }: { score: number }) {
  const size = 64;
  const strokeWidth = 6;
  const center = size / 2;
  const radius = center - strokeWidth - 2;
  const circumference = 2 * Math.PI * radius;
  const clamped = Math.min(100, Math.max(0, score));
  const strokeDashoffset = circumference - (clamped / 100) * circumference;
  const cat = getRiskCategory(score);

  return (
    <div className="relative flex items-center justify-center shrink-0" style={{ width: size, height: size }}>
      <svg className="w-full h-full -rotate-90" viewBox={`0 0 ${size} ${size}`}>
        <circle
          cx={center}
          cy={center}
          r={radius}
          stroke="rgba(255, 255, 255, 0.15)"
          strokeWidth={strokeWidth}
          fill="transparent"
        />
        <circle
          cx={center}
          cy={center}
          r={radius}
          stroke={cat.level === 'critical' ? '#ef4444' : cat.level === 'high' ? '#f97316' : cat.level === 'moderate' ? '#eab308' : '#10b981'}
          strokeWidth={strokeWidth}
          fill="transparent"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          className="transition-all duration-700 ease-out"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
        <span className="font-mono-code font-bold text-sm text-white leading-none">
          {score}
        </span>
        <span className="text-[7px] font-mono-code font-bold text-white/60 uppercase mt-0.5">
          DPHIS
        </span>
      </div>
    </div>
  );
}

export default function ProjectIntelligence({ 
  projectId, 
  currentUser,
  allProjects,
  onNavigateToInvestigation, 
  onSelectProject
}: Props) {
  const isAdmin = currentUser?.role === 'ADMIN' || currentUser?.role === 'ANALYST';
  
  // Navigation state: null = project list view, string = deep intelligence view
  const [activeProjectId, setActiveProjectId] = useState<string | null>(null);

  // Directory Projects State
  const [projectList, setProjectList] = useState<any[]>([]);
  const [directoryLoading, setDirectoryLoading] = useState(true);

  // Filters State
  const [searchQuery, setSearchQuery] = useState('');
  const [riskFilter, setRiskFilter] = useState<'ALL' | 'CRITICAL' | 'HIGH' | 'MODERATE' | 'LOW'>('ALL');
  const [sectorFilter, setSectorFilter] = useState<string>('ALL');
  const [stateFilter, setStateFilter] = useState<string>('ALL');
  const [sortBy, setSortBy] = useState<'dphis_desc' | 'dphis_asc' | 'cost_desc' | 'delay_desc' | 'name_asc'>('dphis_desc');

  // Deep View State
  const [activeTab, setActiveTab] = useState<'shap' | 'predictions'>('shap');
  const [project, setProject] = useState<ProjectData | null>(null);
  const [prediction, setPrediction] = useState<PredictionData | null>(null);
  const [risk, setRisk] = useState<RiskData | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  // Normal user embedded investigation state
  const [showTechnicalShap, setShowTechnicalShap] = useState(false);
  const [isInvestigating, setIsInvestigating] = useState(false);
  const [investigationReport, setInvestigationReport] = useState<InvestigationReport | null>(null);
  const [investigationStep, setInvestigationStep] = useState<number>(0);

  // Load project list on mount
  useEffect(() => {
    let isMounted = true;
    setDirectoryLoading(true);

    fetchProjects(undefined, 100, undefined, undefined, isAdmin ? undefined : currentUser?.username).then(apiProjects => {
      if (!isMounted) return;
      if (apiProjects && apiProjects.length > 0) {
        setProjectList(apiProjects);
      } else if (allProjects && allProjects.length > 0) {
        // Fallback to pins passed via props
        const mapped = allProjects.map(p => ({
          project_id: p.id,
          project_name: p.name,
          ministry: currentUser?.ministry || 'Ministry of Infrastructure',
          sector: p.name.toLowerCase().includes('rail') || p.name.toLowerCase().includes('gauge') ? 'Railways' : p.name.toLowerCase().includes('solar') ? 'Power & Energy' : p.name.toLowerCase().includes('port') ? 'Ports & Shipping' : 'Roads & Highways',
          state: p.state,
          cost: { revised: parseInt(p.cost.replace(/[^\d]/g, '') || '3500') },
          schedule: { revised_end: '2027-12-31' },
          dphis: p.dphis,
          risk_level: p.risk,
          delay_str: p.delay
        }));
        setProjectList(mapped);
      }
      setDirectoryLoading(false);
    }).catch(() => {
      if (isMounted) setDirectoryLoading(false);
    });

    return () => {
      isMounted = false;
    };
  }, [allProjects, isAdmin, currentUser]);

  // Load detail data when an active project is selected
  useEffect(() => {
    if (!activeProjectId) {
      setProject(null);
      setPrediction(null);
      setRisk(null);
      setDetailLoading(false);
      return;
    }

    setDetailLoading(true);
    Promise.all([
      fetchProject(activeProjectId),
      fetchProjectPredictions(activeProjectId),
      fetchProjectRisk(activeProjectId)
    ]).then(([p, pred, r]) => {
      if (p) setProject(p);
      if (pred) setPrediction(pred);
      if (r) setRisk(r);
      setDetailLoading(false);
    }).catch(() => setDetailLoading(false));
  }, [activeProjectId]);

  // Inferred filter options
  const inferredSectors = useMemo(() => {
    const set = new Set<string>();
    projectList.forEach(p => {
      if (p.sector) set.add(p.sector);
    });
    return Array.from(set).sort();
  }, [projectList]);

  const inferredStates = useMemo(() => {
    const set = new Set<string>();
    projectList.forEach(p => {
      if (p.state) set.add(p.state);
    });
    return Array.from(set).sort();
  }, [projectList]);

  // Filtered & sorted projects
  const filteredProjects = useMemo(() => {
    return projectList.filter(p => {
      const pDphis = p.dphis ?? 50;
      const cat = getRiskCategory(pDphis);

      // Risk level filter
      const matchesRisk = 
        riskFilter === 'ALL' ||
        (riskFilter === 'CRITICAL' && cat.level === 'critical') ||
        (riskFilter === 'HIGH' && cat.level === 'high') ||
        (riskFilter === 'MODERATE' && cat.level === 'moderate') ||
        (riskFilter === 'LOW' && cat.level === 'low');

      // Sector filter
      const matchesSector = 
        sectorFilter === 'ALL' ||
        (p.sector && p.sector.toLowerCase() === sectorFilter.toLowerCase());

      // State filter
      const matchesState = 
        stateFilter === 'ALL' ||
        (p.state && p.state.toLowerCase() === stateFilter.toLowerCase());

      // Search query
      const q = searchQuery.toLowerCase().trim();
      const matchesSearch = 
        !q ||
        (p.project_id && p.project_id.toLowerCase().includes(q)) ||
        (p.project_name && p.project_name.toLowerCase().includes(q)) ||
        (p.ministry && p.ministry.toLowerCase().includes(q)) ||
        (p.sector && p.sector.toLowerCase().includes(q)) ||
        (p.state && p.state.toLowerCase().includes(q));

      return matchesRisk && matchesSector && matchesState && matchesSearch;
    }).sort((a, b) => {
      const aDphis = a.dphis ?? 50;
      const bDphis = b.dphis ?? 50;
      const aCost = a.cost?.revised || 0;
      const bCost = b.cost?.revised || 0;

      if (sortBy === 'dphis_desc') return bDphis - aDphis;
      if (sortBy === 'dphis_asc') return aDphis - bDphis;
      if (sortBy === 'cost_desc') return bCost - aCost;
      if (sortBy === 'delay_desc') return bDphis - aDphis;
      if (sortBy === 'name_asc') return (a.project_name || '').localeCompare(b.project_name || '');
      return 0;
    });
  }, [projectList, riskFilter, sectorFilter, stateFilter, searchQuery, sortBy]);

  const handleRunNormalInvestigation = async () => {
    if (!activeProjectId || isInvestigating) return;
    setIsInvestigating(true);
    setInvestigationStep(1);

    const stepTimer = setInterval(() => {
      setInvestigationStep(prev => (prev < 4 ? prev + 1 : prev));
    }, 450);

    try {
      const res = await triggerInvestigation(activeProjectId);
      clearInterval(stepTimer);
      setInvestigationReport(res);
    } catch (err) {
      clearInterval(stepTimer);
      console.warn('Investigation trigger error:', err);
    } finally {
      setIsInvestigating(false);
      setInvestigationStep(5);
    }
  };

  /* =========================================================================
     VIEW 1: REDESIGNED RISK INTELLIGENCE DIRECTORY (SEARCH + INFERRED FILTERS)
     ========================================================================= */
  if (!activeProjectId) {
    return (
      <div className="space-y-6 sm:space-y-8 pt-16 sm:pt-20 pb-16 px-4 sm:px-8 md:px-12 max-w-7xl mx-auto">
        {/* Header Hero */}
        <GlassCard variant="hero" padding={24} className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1.5">
            <div className="flex flex-wrap items-center gap-2">
              <h2 className="text-xl sm:text-2xl md:text-3xl font-bold font-display text-white">
                Risk Intelligence &amp; Predictive Analytics
              </h2>
              <span className="px-2.5 py-0.5 rounded text-xs font-mono font-bold bg-white/10 text-white/90 border border-white/20">
                {filteredProjects.length} Projects Analyzed
              </span>
            </div>
            <p className="text-xs sm:text-sm md:text-base text-white/80 leading-relaxed">
              Early warning risk models, DPHIS telemetry, and SHAP explainability across monitored infrastructure corridors
            </p>
          </div>
        </GlassCard>

        {/* Search Bar + Inferred Filter Controls */}
        <div className="space-y-3">
          <div className="flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-3">
            {/* Search Bar */}
            <div className="relative flex-1">
              <input
                type="text"
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                placeholder="Search by project name, ID, sector, state, or ministry..."
                className="w-full bg-[#0B0F17]/80 border border-white/20 rounded-xl px-4 py-2.5 text-xs sm:text-sm text-white placeholder:text-white/40 focus:outline-none focus:border-white/50"
              />
            </div>

            {/* Inferred Filters to the right of Search */}
            <div className="flex flex-wrap items-center gap-2 shrink-0">
              {/* Sector Filter */}
              <select
                value={sectorFilter}
                onChange={e => setSectorFilter(e.target.value)}
                className="bg-[#0B0F17]/80 border border-white/20 rounded-xl px-3 py-2 text-xs font-mono text-white focus:outline-none focus:border-white/50 cursor-pointer"
              >
                <option value="ALL">All Sectors ({inferredSectors.length})</option>
                {inferredSectors.map(s => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>

              {/* State Filter */}
              <select
                value={stateFilter}
                onChange={e => setStateFilter(e.target.value)}
                className="bg-[#0B0F17]/80 border border-white/20 rounded-xl px-3 py-2 text-xs font-mono text-white focus:outline-none focus:border-white/50 cursor-pointer"
              >
                <option value="ALL">All States ({inferredStates.length})</option>
                {inferredStates.map(st => (
                  <option key={st} value={st}>{st}</option>
                ))}
              </select>

              {/* Sort By Filter */}
              <select
                value={sortBy}
                onChange={e => setSortBy(e.target.value as any)}
                className="bg-[#0B0F17]/80 border border-white/20 rounded-xl px-3 py-2 text-xs font-mono text-white focus:outline-none focus:border-white/50 cursor-pointer"
              >
                <option value="dphis_desc">Sort: DPHIS High → Low</option>
                <option value="dphis_asc">Sort: DPHIS Low → High</option>
                <option value="cost_desc">Sort: Outlay Highest</option>
                <option value="name_asc">Sort: Name (A–Z)</option>
              </select>
            </div>
          </div>

          {/* Quick Risk Level Buttons */}
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-none">
            {(['ALL', 'CRITICAL', 'HIGH', 'MODERATE', 'LOW'] as const).map(st => {
              const labelMap = {
                ALL: 'All Risk Tiers',
                CRITICAL: 'Critical (DPHIS ≥ 80)',
                HIGH: 'High Risk (65–79)',
                MODERATE: 'Moderate (45–64)',
                LOW: 'Low Risk (< 45)'
              };
              const active = riskFilter === st;
              return (
                <button
                  key={st}
                  onClick={() => setRiskFilter(st)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-mono font-medium transition-all cursor-pointer whitespace-nowrap border ${
                    active
                      ? 'bg-white text-black font-bold border-white shadow-sm'
                      : 'bg-white/5 hover:bg-white/10 text-white/80 border-white/15'
                  }`}
                >
                  {labelMap[st]}
                </button>
              );
            })}
          </div>
        </div>

        {/* Project Cards Grid */}
        {directoryLoading ? (
          <GlassCard variant="medium" padding={32} className="text-center space-y-3">
            <div className="w-6 h-6 border-2 border-white border-t-transparent rounded-full animate-spin mx-auto" />
            <div className="text-xs font-mono text-white/70">Loading risk telemetry from database...</div>
          </GlassCard>
        ) : filteredProjects.length === 0 ? (
          <GlassCard variant="medium" padding={32} className="text-center space-y-4">
            <div className="text-base font-bold text-white">No Projects Match Selected Filters</div>
            <p className="text-xs sm:text-sm text-white/70 max-w-md mx-auto">
              No projects satisfy your active search query or filter parameters. Try clearing the filters.
            </p>
            <button
              onClick={() => {
                setSearchQuery('');
                setRiskFilter('ALL');
                setSectorFilter('ALL');
                setStateFilter('ALL');
              }}
              className="px-4 py-2 rounded-xl bg-white/10 hover:bg-white/20 text-white text-xs font-mono font-bold border border-white/20 transition-all cursor-pointer"
            >
              Clear All Filters
            </button>
          </GlassCard>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
            {filteredProjects.map(p => {
              const pScore = p.dphis ?? 50;
              const cat = getRiskCategory(pScore);
              const pId = p.project_id || p.id;
              const pOutlay = p.cost?.revised || 4218;

              return (
                <div
                  key={pId}
                  onClick={() => {
                    setActiveProjectId(pId);
                    onSelectProject?.(pId);
                  }}
                  className="oled-solid-card p-5 sm:p-6 space-y-4 hover:border-white/50 transition-all cursor-pointer flex flex-col justify-between group"
                >
                  <div className="space-y-3.5">
                    {/* Top Row: ID, State, and Risk Tier */}
                    <div className="flex items-center justify-between gap-2 border-b border-white/10 pb-3">
                      <div className="flex items-center gap-2">
                        <span className="font-mono-code font-bold text-xs text-white px-2 py-0.5 rounded bg-white/10">
                          {pId}
                        </span>
                        <span className="text-xs text-white/70 font-medium">
                          📍 {p.state}
                        </span>
                      </div>
                      <span className={`px-2.5 py-0.5 rounded text-[11px] font-mono font-bold border ${cat.badgeBg}`}>
                        {cat.label}
                      </span>
                    </div>

                    {/* Project Title & Sector */}
                    <div>
                      <h3 className="font-bold text-sm sm:text-base text-white leading-snug group-hover:text-white transition-colors line-clamp-2">
                        {p.project_name}
                      </h3>
                      <div className="text-xs text-white/60 mt-1 font-mono">
                        {p.sector || 'Infrastructure'} · {p.ministry || 'Central Sector'}
                      </div>
                    </div>

                    {/* Compact Circular Gauge + Scrollbar */}
                    <div className="p-3 rounded-xl bg-white/5 border border-white/10 flex items-center gap-3">
                      <MiniDphisGauge score={pScore} />

                      <div className="flex-1 space-y-1.5 min-w-0">
                        <div className="flex items-center justify-between text-xs">
                          <span className="font-mono-code font-bold text-white/80 text-[11px] uppercase tracking-wider">
                            DPHIS Index
                          </span>
                          <span className="font-mono-code font-bold text-white">
                            {pScore} <span className="text-white/40 font-normal">/ 100</span>
                          </span>
                        </div>

                        {/* DPHIS Bar / Scrollbar */}
                        <div className="h-2 w-full rounded-full bg-white/10 p-0.5 overflow-hidden">
                          <div
                            className="h-full rounded-full transition-all duration-500"
                            style={{
                              width: `${Math.min(100, Math.max(5, pScore))}%`,
                              background: pScore >= 80 
                                ? 'linear-gradient(90deg, #f97316, #ef4444)' 
                                : pScore >= 65 
                                ? 'linear-gradient(90deg, #eab308, #f97316)' 
                                : pScore >= 45 
                                ? '#eab308' 
                                : '#10b981'
                            }}
                          />
                        </div>

                        <div className="text-[10px] font-mono text-white/60 flex items-center justify-between">
                          <span>0</span>
                          <span className="font-semibold text-white/90">Sanctioned: ₹{pOutlay} Cr</span>
                          <span>100</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Click to Inspect Prompt */}
                  <div className="pt-3 border-t border-white/10 flex items-center justify-between">
                    <span className="text-xs font-mono text-white/70 group-hover:text-white transition-colors">
                      Inspect Risk Intelligence
                    </span>
                    <span className="text-xs font-bold text-white group-hover:translate-x-1 transition-transform">
                      →
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    );
  }

  /* =========================================================================
     VIEW 2: DEEP RISK INTELLIGENCE DETAIL PAGE (WITH BACK BUTTON)
     ========================================================================= */
  const pName = project?.project_name || "NH-48 Varanasi-Ranchi Expressway Package 4";
  const pState = project?.state || "Uttar Pradesh";
  const pSector = project?.sector || "Roads & Highways";
  const currentDphis = risk?.dphis ?? project?.dphis ?? 85.0;
  const riskCat = getRiskCategory(currentDphis);

  return (
    <div className="space-y-6 sm:space-y-8 pt-16 sm:pt-20 pb-16 px-4 sm:px-8 md:px-12 max-w-7xl mx-auto">
      {/* Return to Redefined Risk Intelligence Directory Bar */}
      <div className="flex items-center justify-between pb-2">
        <button
          onClick={() => setActiveProjectId(null)}
          className="px-4 py-2 rounded-xl bg-white/10 hover:bg-white hover:text-black text-white text-xs sm:text-sm font-mono-code font-bold border border-white/20 transition-all cursor-pointer flex items-center gap-2 shadow-md"
        >
          <span>← Back to Risk Intelligence List</span>
        </button>

        <div className="text-xs font-mono text-white/60">
          Inspecting Asset: <strong className="text-white">{activeProjectId}</strong>
        </div>
      </div>

      {/* Top Project Context Card */}
      <GlassCard variant="hero" padding={24} className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
        <div className="space-y-2 sm:space-y-3">
          <div className="flex flex-wrap items-center gap-2.5">
            <span className="font-mono-code font-bold text-xs sm:text-sm text-white px-2.5 py-0.5 rounded bg-white/10">
              {activeProjectId}
            </span>
            <span className={`px-2.5 py-0.5 rounded text-xs font-mono font-bold border ${riskCat.badgeBg}`}>
              {riskCat.label}
            </span>
            <span className="text-xs text-white/70">
              {project?.ministry || 'Ministry of Infrastructure'}
            </span>
          </div>

          <h2 className="text-xl sm:text-2xl md:text-3xl font-bold font-display text-white leading-tight">
            {pName}
          </h2>

          <div className="flex flex-wrap items-center gap-3 text-xs sm:text-sm text-white/80 font-medium">
            <span>📍 {pState}</span>
            <span>•</span>
            <span>Sector: {pSector}</span>
            <span>•</span>
            <span className="font-mono-code font-bold text-white">
              Sanctioned Budget: ₹{project?.cost?.revised || 4218} Cr
            </span>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3 shrink-0">
          {!isAdmin ? (
            <button
              onClick={handleRunNormalInvestigation}
              disabled={isInvestigating}
              className="px-5 py-2.5 rounded-xl bg-white text-black hover:bg-slate-200 text-xs sm:text-sm font-mono-code font-bold transition-all cursor-pointer shadow-lg flex items-center gap-2"
            >
              {isInvestigating ? (
                <>
                  <span className="w-3.5 h-3.5 rounded-full border-2 border-black border-t-transparent animate-spin" />
                  <span>Investigating Issues...</span>
                </>
              ) : (
                <>
                  <span>⚡</span>
                  <span>Investigate Issues</span>
                </>
              )}
            </button>
          ) : (
            <button
              onClick={() => onNavigateToInvestigation(activeProjectId || '')}
              className="px-5 sm:px-6 py-2.5 rounded-xl bg-black text-white text-xs sm:text-sm font-mono-code font-bold border border-white/30 shadow-[0_0_16px_rgba(255,255,255,0.22)] hover:bg-zinc-900 transition-all cursor-pointer flex items-center justify-center gap-2"
            >
              <span>Launch Deep AI Investigation Console →</span>
            </button>
          )}
        </div>
      </GlassCard>

      {/* Main Grid: DPHIS Gauge + Predictions / SHAP */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 sm:gap-8">
        {/* Left: DPHIS Gauge & Component Breakdown */}
        <GlassCard variant="medium" padding={24} className="space-y-5">
          <div className="flex items-center justify-between">
            <h3 className="text-base sm:text-lg font-bold font-display text-white">
              Dynamic Project Health (DPHIS)
            </h3>
            <span className="text-xs sm:text-sm font-mono-code text-white/70">0–100 Scale</span>
          </div>

          <DHPISGauge score={currentDphis} />

          {/* Component Bar Breakdown */}
          {risk?.components && (
            <div className="space-y-3 pt-3 border-t border-white/15 text-sm">
              <div className="text-xs font-mono-code font-bold uppercase text-white/70">
                Risk Component Decomposition
              </div>
              <div className="space-y-2.5">
                {[
                  { name: 'Schedule Delays (30% weight)', val: risk.components.time },
                  { name: 'Budget Overrun Risk (30% weight)', val: risk.components.cost },
                  { name: 'Physical Progress Lags (25% weight)', val: risk.components.progress },
                  { name: 'Financial Velocity Disparity (10% weight)', val: risk.components.financial },
                  { name: 'Model Implementation Confidence (5% weight)', val: risk.components.implementation },
                ].map(comp => (
                  <div key={comp.name} className="space-y-1">
                    <div className="flex justify-between font-mono-code text-xs sm:text-sm">
                      <span className="text-white/80">{comp.name}</span>
                      <span className="font-bold text-white">{(comp.val * 100).toFixed(0)}%</span>
                    </div>
                    <div className="h-2 rounded-full bg-white/10 overflow-hidden">
                      <div
                        className="h-full bg-white rounded-full transition-all duration-700"
                        style={{ width: `${Math.min(100, comp.val * 100)}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </GlassCard>

        {/* Right 2 Cols: Predictions & SHAP Explainability */}
        <GlassCard variant="medium" padding={24} className="lg:col-span-2 space-y-6">
          <div className="flex flex-wrap items-center justify-between border-b border-white/15 pb-4 gap-3">
            <div className="flex items-center gap-2 sm:gap-3">
              <button
                onClick={() => setActiveTab('shap')}
                className={`px-3 sm:px-4 py-2 rounded-xl text-xs sm:text-sm font-mono-code font-bold transition-all cursor-pointer ${
                  activeTab === 'shap' ? 'bg-white text-black' : 'text-white/80 hover:text-white hover:bg-white/10'
                }`}
              >
                SHAP Explainability Vectors
              </button>
              <button
                onClick={() => setActiveTab('predictions')}
                className={`px-3 sm:px-4 py-2 rounded-xl text-xs sm:text-sm font-mono-code font-bold transition-all cursor-pointer ${
                  activeTab === 'predictions' ? 'bg-white text-black' : 'text-white/80 hover:text-white hover:bg-white/10'
                }`}
              >
                Forecast Models &amp; Horizons
              </button>
            </div>
            <span className="text-xs font-mono-code text-white/80 font-semibold">
              LightGBM / XGBoost Regressor v2.1
            </span>
          </div>

          {activeTab === 'shap' ? (
            <div className="space-y-4">
              <p className="text-sm md:text-base text-white/85 leading-relaxed">
                Feature attribution values generated via TreeSHAP explainability algorithms, identifying primary risk-driving variables:
              </p>
              <div className="space-y-3">
                {(prediction?.top_shap_factors || [
                  { feature: 'Construction Schedule Delays', impact: 43.2, direction: 'increase', description: 'Main construction milestones are running 28 months behind the planned timeline.' },
                  { feature: 'Spending Ahead of Progress', impact: 24.1, direction: 'increase', description: '62% of funds have been spent, while only 34% of actual physical construction is completed.' },
                  { feature: 'Machinery & Equipment Shortage', impact: 14.5, direction: 'increase', description: 'Heavy equipment on site is 38% lower than agreed in the project plan.' },
                  { feature: 'Land Acquisition Completed', impact: -8.0, direction: 'decrease', description: '98.4% of land has been acquired and cleared, which prevents work stoppages.' },
                ]).map(f => (
                  <div key={f.feature} className="p-4 rounded-xl bg-white/5 border border-white/15 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div className="space-y-1 max-w-xl">
                      <div className="font-semibold text-sm sm:text-base text-white">{f.feature}</div>
                      <div className="text-xs sm:text-sm text-white/80">{f.description}</div>
                    </div>
                    <div className="sm:text-right font-mono-code shrink-0">
                      <div className="text-base sm:text-xl font-bold text-white">
                        {f.impact > 0 ? `+${f.impact}` : f.impact} pts
                      </div>
                      <div className="text-xs text-white/60 uppercase">{f.impact > 0 ? '+ Increases Risk' : '− Reduces Risk'}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="space-y-6">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-5">
                <div className="p-5 rounded-xl bg-white/5 border border-white/15 space-y-2">
                  <div className="text-xs font-mono-code uppercase text-white/70">Predicted Final Cost</div>
                  <div className="text-2xl sm:text-3xl font-bold font-mono-code text-white">
                    ₹{prediction?.cost.predicted_final_cost || 4520} Cr
                  </div>
                  <div className="text-xs sm:text-sm text-white/85 font-semibold">
                    +{prediction?.cost.predicted_overrun_pct || 7.2}% projected budget overrun
                  </div>
                </div>

                <div className="p-5 rounded-xl bg-white/5 border border-white/15 space-y-2">
                  <div className="text-xs font-mono-code uppercase text-white/70">Timeline Slippage Projection</div>
                  <div className="text-2xl sm:text-3xl font-bold font-mono-code text-white">
                    +{prediction?.delay.expected_delay_months || 24} Months
                  </div>
                  <div className="text-xs sm:text-sm text-white/85">
                    Predicted Completion: {prediction?.delay.predicted_completion_date || '2027-12-31'}
                  </div>
                </div>
              </div>

              <div className="p-5 rounded-xl bg-white/5 border border-white/15 space-y-2">
                <div className="font-semibold text-sm sm:text-base text-white">Model Governance &amp; Benchmarking</div>
                <p className="text-xs sm:text-sm text-white/80 leading-relaxed">
                  Trained on 3,399 central sector project historical tracking cycles. Calibrated with quantile loss regressors and validated with 5-fold spatial cross-validation.
                </p>
              </div>
            </div>
          )}
        </GlassCard>
      </div>
    </div>
  );
}
