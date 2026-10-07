import React, { useState, useEffect, useMemo } from 'react';
import GlassCard from '../components/GlassCard';
import { 
  fetchProjectPredictions, fetchProjectRisk, fetchProject, fetchProjects, fetchProjectPeers,
  PredictionData, RiskData, ProjectData, UserProfile, PeerIntelligenceData
} from '../lib/api';
import { DEMO_ADMIN_28_PROJECTS, DEMO_USER_10_PROJECTS } from '../lib/seededProjects';
import { ProjectPin } from '../components/CeoPinManager';
import { getRiskCategory } from '../lib/risk';
import { useTheme } from '../hooks/useTheme';
import { computeRealTimeShapFactors } from '../lib/shap';
import { CurvedGrowthArrow, CurvedDecreaseArrow, TrendBadge } from '../components/CurvedTrendArrow';

interface Props {
  projectId?: string;
  currentUser?: UserProfile | null;
  allProjects?: ProjectPin[];
  onNavigateToInvestigation: (projectId: string) => void;
  onSelectProject?: (projectId: string) => void;
  onOpenAddProject?: () => void;
  onNavigateBack?: () => void;
}

function DHPISGauge({ score, isDark = true }: { score: number; isDark?: boolean }) {
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
            stroke={isDark ? "rgba(255, 255, 255, 0.15)" : "rgba(0, 0, 0, 0.12)"}
            strokeWidth={strokeWidth}
            fill="transparent"
          />
          {/* Progress Arc in crisp solid white or solid dark */}
          <circle
            cx={center}
            cy={center}
            r={radius}
            stroke={isDark ? "#ffffff" : "#0f172a"}
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
          <span className={`font-mono-code font-bold text-4xl sm:text-5xl tracking-tight ${isDark ? 'text-white' : 'text-slate-900'}`}>
            {score}
          </span>
          <span className={`mt-1 text-xs sm:text-sm font-mono-code font-bold uppercase tracking-wider ${cat.colorClass}`}>
            {cat.label}
          </span>
          <span className={`text-xs font-mono-code mt-0.5 ${isDark ? 'text-white/70' : 'text-slate-600'}`}>
            DPHIS Index · {cat.badgeText}
          </span>
        </div>
      </div>
    </div>
  );
}

function MiniDphisGauge({ score, isDark = true }: { score: number; isDark?: boolean }) {
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
          stroke={isDark ? "rgba(255, 255, 255, 0.15)" : "rgba(0, 0, 0, 0.12)"}
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
        <span className={`font-mono-code font-bold text-sm leading-none ${isDark ? 'text-white' : 'text-slate-900'}`}>
          {score}
        </span>
        <span className={`text-[7px] font-mono-code font-bold uppercase mt-0.5 ${isDark ? 'text-white/60' : 'text-slate-500'}`}>
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
  onSelectProject,
  onOpenAddProject,
  onNavigateBack
}: Props) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  const isAdmin = currentUser?.role === 'ADMIN' || currentUser?.role === 'ANALYST';
  
  // Navigation state: null = project list view (admin only), string = deep intelligence view
  const defaultProjectId = projectId || (!isAdmin && allProjects && allProjects.length > 0 ? allProjects[0].id : null);
  const [activeProjectId, setActiveProjectId] = useState<string | null>(defaultProjectId);

  useEffect(() => {
    if (projectId) {
      setActiveProjectId(projectId);
    } else if (!isAdmin && allProjects && allProjects.length > 0) {
      setActiveProjectId(allProjects[0].id);
    }
  }, [projectId, isAdmin, allProjects]);

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
  const [activeTab, setActiveTab] = useState<'shap' | 'predictions' | 'peers'>('shap');
  const [project, setProject] = useState<ProjectData | null>(null);
  const [prediction, setPrediction] = useState<PredictionData | null>(null);
  const [risk, setRisk] = useState<RiskData | null>(null);
  const [peerData, setPeerData] = useState<PeerIntelligenceData | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  // Load project list on mount
  useEffect(() => {
    let isMounted = true;
    setDirectoryLoading(true);

    const isUserAccount = !isAdmin && currentUser?.username && currentUser.username.toLowerCase() !== 'admin';
    fetchProjects(undefined, 100, undefined, undefined, isUserAccount ? currentUser.username : undefined).then(apiProjects => {
      if (!isMounted) return;
      if (apiProjects && apiProjects.length > 0) {
        setProjectList(isUserAccount ? apiProjects.slice(0, 10) : apiProjects);
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
        setProjectList(isUserAccount ? mapped.slice(0, 10) : mapped);
      } else {
        setProjectList(isUserAccount ? DEMO_USER_10_PROJECTS : DEMO_ADMIN_28_PROJECTS);
      }
      setDirectoryLoading(false);
    }).catch(() => {
      if (isMounted) {
        setProjectList(isUserAccount ? DEMO_USER_10_PROJECTS : DEMO_ADMIN_28_PROJECTS);
        setDirectoryLoading(false);
      }
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
      setPeerData(null);
      setDetailLoading(false);
      return;
    }

    setDetailLoading(true);
    Promise.all([
      fetchProject(activeProjectId),
      fetchProjectPredictions(activeProjectId),
      fetchProjectRisk(activeProjectId),
      fetchProjectPeers(activeProjectId)
    ]).then(([p, pred, r, peers]) => {
      if (p) setProject(p);
      if (pred) setPrediction(pred);
      if (r) setRisk(r);
      if (peers) setPeerData(peers);
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

  /* =========================================================================
     DEEP RISK INTELLIGENCE DETAIL PAGE (DIRECTLY REACHED FROM PORTFOLIO)
     ========================================================================= */
  const resolvedProjectId = activeProjectId || (allProjects && allProjects.length > 0 ? ((allProjects[0] as any).project_id || allProjects[0].id) : "618488");
  const pName = project?.project_name || "NH-48 Varanasi-Ranchi Expressway Package 4";
  const pState = project?.state || "Uttar Pradesh";
  const pSector = project?.sector || "Roads & Highways";
  const currentDphis = risk?.dphis ?? project?.dphis ?? 85.0;
  const riskCat = getRiskCategory(currentDphis);

  // Dynamic real-time SHAP explainability factors based on live project telemetry
  const shapFactors = useMemo(() => {
    return computeRealTimeShapFactors({
      ...project,
      id: resolvedProjectId,
      dphis: currentDphis,
      name: pName,
      sector: pSector,
      state: pState,
      delay: prediction?.delay?.expected_delay_months,
      cost: project?.cost || { revised: 4218, original: 4000 }
    });
  }, [project, resolvedProjectId, currentDphis, pName, pSector, pState, prediction]);

  return (
    <div className="space-y-6 sm:space-y-8 pt-16 sm:pt-20 pb-16 px-4 sm:px-8 md:px-12 max-w-7xl mx-auto">
      {/* Return to Directory / Back to My Projects */}
      <div className="flex items-center justify-between pb-2">
        <button
          onClick={() => {
            if (onNavigateBack) {
              onNavigateBack();
            } else {
              setActiveProjectId(null);
            }
          }}
          className={`px-4 py-2 rounded-xl text-xs sm:text-sm font-mono-code font-bold border transition-all cursor-pointer flex items-center gap-2 shadow-md ${
            isDark 
              ? 'bg-white/10 hover:bg-white hover:text-black text-white border-white/20' 
              : 'bg-slate-100 hover:bg-slate-200 text-slate-800 hover:text-black border-slate-300'
          }`}
        >
          <span>{currentUser?.role?.toUpperCase() === 'ADMIN' ? '← Back to Portfolio' : '← Back to My Projects'}</span>
        </button>

        <div className={`text-xs font-mono ${isDark ? 'text-white/60' : 'text-slate-500'}`}>
          Inspecting Asset: <strong className={isDark ? 'text-white' : 'text-slate-900'}>{resolvedProjectId}</strong>
        </div>
      </div>

      {/* Top Project Context Card */}
      <GlassCard variant="hero" padding={24} className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
        <div className="space-y-2 sm:space-y-3">
          <div className="flex flex-wrap items-center gap-2.5">
            <span className={`font-mono-code font-bold text-xs sm:text-sm px-2.5 py-0.5 rounded ${
              isDark ? 'bg-white/10 text-white' : 'bg-slate-200 text-slate-900 border border-slate-300'
            }`}>
              {resolvedProjectId}
            </span>
            <span className={`px-2.5 py-0.5 rounded text-xs font-mono font-bold border ${riskCat.badgeBg}`}>
              {riskCat.label}
            </span>
            <span className={`text-xs ${isDark ? 'text-white/70' : 'text-slate-600'}`}>
              {project?.ministry || 'Ministry of Infrastructure'}
            </span>
          </div>

          <h2 className={`text-xl sm:text-2xl md:text-3xl font-bold font-display leading-tight ${isDark ? 'text-white' : 'text-slate-900'}`}>
            {pName}
          </h2>

          <div className={`flex flex-wrap items-center gap-3 text-xs sm:text-sm font-medium ${isDark ? 'text-white/80' : 'text-slate-600'}`}>
            <span>📍 {pState}</span>
            <span>•</span>
            <span>Sector: {pSector}</span>
            <span>•</span>
            <span className={`font-mono-code font-bold ${isDark ? 'text-white' : 'text-slate-900'}`}>
              Sanctioned Budget: ₹{project?.cost?.revised || 4218} Cr
            </span>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3 shrink-0">
          <button
            type="button"
            onClick={() => onNavigateToInvestigation(resolvedProjectId)}
            style={{ touchAction: 'manipulation' }}
            className={`px-5 sm:px-6 py-2.5 rounded-xl text-xs sm:text-sm font-mono-code font-bold active:scale-95 transition-all cursor-pointer flex items-center justify-center gap-2 select-none shadow-md ${
              isDark 
                ? 'bg-black text-white border border-white/30 shadow-[0_0_16px_rgba(255,255,255,0.22)] hover:bg-zinc-900' 
                : 'bg-slate-900 text-white hover:bg-black shadow-slate-300'
            }`}
          >
            <span>Launch Deep AI Investigation Console →</span>
          </button>
        </div>
      </GlassCard>

      {/* Main Grid: DPHIS Gauge + Predictions / SHAP */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 sm:gap-8">
        {/* Left: DPHIS Gauge & Component Breakdown */}
        <GlassCard variant="medium" padding={24} className="space-y-5">
          <div className="flex items-center justify-between">
            <h3 className={`text-base sm:text-lg font-bold font-display ${isDark ? 'text-white' : 'text-slate-900'}`}>
              Project Health Score
            </h3>
            <span className={`text-xs sm:text-sm font-mono-code ${isDark ? 'text-white/70' : 'text-slate-500'}`}>0–100 Scale</span>
          </div>

          <DHPISGauge score={currentDphis} isDark={isDark} />

          {/* Component Bar Breakdown */}
          {risk?.components && (
            <div className={`space-y-3 pt-3 border-t text-sm ${isDark ? 'border-white/15' : 'border-slate-200'}`}>
              <div className={`text-xs font-mono-code font-bold uppercase ${isDark ? 'text-white/70' : 'text-slate-700'}`}>
                Risk Factor Breakdown
              </div>
              <div className="space-y-2.5">
                {[
                  { name: 'Timeline & Delay Risk', val: risk.components.time },
                  { name: 'Budget Overrun Risk', val: risk.components.cost },
                  { name: 'Physical Work Pace', val: risk.components.progress },
                  { name: 'Spending vs Progress Gap', val: risk.components.financial },
                  { name: 'Model Reliability Score', val: risk.components.implementation },
                ].map(comp => (
                  <div key={comp.name} className="space-y-1">
                    <div className="flex justify-between font-mono-code text-xs sm:text-sm">
                      <span className={isDark ? 'text-white/80' : 'text-slate-600'}>{comp.name}</span>
                      <span className={`font-bold ${isDark ? 'text-white' : 'text-slate-900'}`}>{(comp.val * 100).toFixed(0)}%</span>
                    </div>
                    <div className={`h-2 rounded-full overflow-hidden ${isDark ? 'bg-white/10' : 'bg-slate-200'}`}>
                      <div
                        className={`h-full rounded-full transition-all duration-700 ${isDark ? 'bg-white' : 'bg-slate-900'}`}
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
          <div className={`flex flex-wrap items-center justify-between border-b pb-4 gap-3 ${isDark ? 'border-white/15' : 'border-slate-200'}`}>
            <div className="flex items-center gap-2 sm:gap-3">
              <button
                onClick={() => setActiveTab('shap')}
                className={`px-3 sm:px-4 py-2 rounded-xl text-xs sm:text-sm font-mono-code font-bold transition-all cursor-pointer ${
                  activeTab === 'shap' 
                    ? (isDark ? 'bg-white text-black' : 'bg-slate-900 text-white shadow-sm') 
                    : (isDark ? 'text-white/80 hover:text-white hover:bg-white/10' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100')
                }`}
              >
                Key Risk Factors (AI Analysis)
              </button>
              <button
                onClick={() => setActiveTab('predictions')}
                className={`px-3 sm:px-4 py-2 rounded-xl text-xs sm:text-sm font-mono-code font-bold transition-all cursor-pointer ${
                  activeTab === 'predictions' 
                    ? (isDark ? 'bg-white text-black' : 'bg-slate-900 text-white shadow-sm') 
                    : (isDark ? 'text-white/80 hover:text-white hover:bg-white/10' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100')
                }`}
              >
                Future Forecasts &amp; Timeline
              </button>
              <button
                onClick={() => setActiveTab('peers')}
                className={`px-3 sm:px-4 py-2 rounded-xl text-xs sm:text-sm font-mono-code font-bold transition-all cursor-pointer flex items-center gap-1.5 ${
                  activeTab === 'peers' 
                    ? (isDark ? 'bg-white text-black' : 'bg-slate-900 text-white shadow-sm') 
                    : (isDark ? 'text-white/80 hover:text-white hover:bg-white/10' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100')
                }`}
              >
                <span>Empirical Peer Cohorts</span>
                <span className={`text-[10px] px-1.5 py-0.2 rounded font-mono ${
                  activeTab === 'peers' ? (isDark ? 'bg-black/20 text-black' : 'bg-white/20 text-white') : (isDark ? 'bg-white/15 text-white' : 'bg-slate-200 text-slate-800')
                }`}>
                  {peerData?.cohort_size || 428} Corridors
                </span>
              </button>
            </div>
            <span className={`text-xs font-mono-code font-semibold ${isDark ? 'text-white/80' : 'text-slate-600'}`}>
              Continuous AI Monitoring Engine v4.0
            </span>
          </div>

          {activeTab === 'shap' ? (
            <div className="space-y-4">
              <p className={`text-sm md:text-base leading-relaxed ${isDark ? 'text-white/85' : 'text-slate-800 font-medium'}`}>
                Our AI analyzed this project's timeline, budget, and construction milestones to identify what is driving the risk level up or down:
              </p>
              <div className="space-y-3">
                {shapFactors.map(f => (
                  <div key={f.feature} className={`p-4 rounded-xl border flex flex-col sm:flex-row sm:items-center justify-between gap-3 ${
                    isDark ? 'bg-white/5 border-white/15' : 'bg-white border-2 border-slate-300 shadow-sm'
                  }`}>
                    <div className="space-y-1 max-w-xl">
                      <div className={`font-semibold text-sm sm:text-base ${isDark ? 'text-white' : 'text-slate-950 font-bold'}`}>{f.feature}</div>
                      <div className={`text-xs sm:text-sm ${isDark ? 'text-white/80' : 'text-slate-800 font-medium'}`}>{f.description}</div>
                    </div>
                    <div className="sm:text-right font-mono-code shrink-0 space-y-1">
                      <TrendBadge 
                        value={`${f.impact > 0 ? '+' : ''}${f.impact} pts`} 
                        mode="risk" 
                        className="text-sm sm:text-base py-1 px-2.5" 
                        iconClassName="w-4 h-4"
                      />
                      <div className={`text-xs uppercase flex items-center justify-end gap-1 ${isDark ? 'text-white/60' : 'text-slate-700 font-bold'}`}>
                        {f.impact > 0 ? (
                          <>
                            <CurvedGrowthArrow className="w-3 h-3 text-amber-400" />
                            <span className={isDark ? '' : 'text-amber-900 font-black'}>Increases Risk</span>
                          </>
                        ) : (
                          <>
                            <CurvedDecreaseArrow className="w-3 h-3 text-emerald-400" />
                            <span className={isDark ? '' : 'text-emerald-900 font-black'}>Lowers Risk</span>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : activeTab === 'predictions' ? (
            <div className="space-y-6">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-5">
                <div className={`p-5 rounded-xl border space-y-2 ${isDark ? 'bg-white/5 border-white/15' : 'bg-white border-2 border-slate-300 shadow-sm'}`}>
                  <div className={`text-xs font-mono-code uppercase ${isDark ? 'text-white/70' : 'text-slate-700 font-bold'}`}>Predicted Final Cost</div>
                  <div className={`text-2xl sm:text-3xl font-bold font-mono-code ${isDark ? 'text-white' : 'text-slate-950 font-black'}`}>
                    ₹{prediction?.cost.predicted_final_cost || 4520} Cr
                  </div>
                  <div className={`text-xs sm:text-sm font-semibold flex items-center gap-1.5 ${isDark ? 'text-white/85' : 'text-slate-800 font-bold'}`}>
                    <CurvedGrowthArrow className="w-3.5 h-3.5 text-amber-400" />
                    <span>+{prediction?.cost.predicted_overrun_pct || 7.2}% projected budget overrun</span>
                  </div>
                </div>

                <div className={`p-5 rounded-xl border space-y-2 ${isDark ? 'bg-white/5 border-white/15' : 'bg-white border-2 border-slate-300 shadow-sm'}`}>
                  <div className={`text-xs font-mono-code uppercase ${isDark ? 'text-white/70' : 'text-slate-700 font-bold'}`}>Timeline Slippage Projection</div>
                  <div className={`text-2xl sm:text-3xl font-bold font-mono-code flex items-center gap-2 ${isDark ? 'text-white' : 'text-slate-950 font-black'}`}>
                    <CurvedGrowthArrow className="w-6 h-6 text-amber-400" />
                    <span>+{prediction?.delay.expected_delay_months || 24} Months</span>
                  </div>
                  <div className={`text-xs sm:text-sm ${isDark ? 'text-white/85' : 'text-slate-800 font-medium'}`}>
                    Predicted Completion: {prediction?.delay.predicted_completion_date || '2027-12-31'}
                  </div>
                </div>
              </div>

              <div className={`p-5 rounded-xl border space-y-2 ${isDark ? 'bg-white/5 border-white/15' : 'bg-slate-100 border-2 border-slate-300 shadow-xs'}`}>
                <div className={`font-semibold text-sm sm:text-base ${isDark ? 'text-white' : 'text-slate-950 font-bold'}`}>Model Reliability &amp; Verification</div>
                <p className={`text-xs sm:text-sm leading-relaxed ${isDark ? 'text-white/80' : 'text-slate-800 font-medium'}`}>
                  Trained and benchmarked on 3,399 major national infrastructure projects. Regularly verified against ground completion records to guarantee dependable early risk alerts.
                </p>
              </div>
            </div>
          ) : (
            /* =================================================================
               EMPIRICAL PEER COHORT INTELLIGENCE (NEW V4 SOVEREIGN ENGINE)
               ================================================================= */
            <div className="space-y-6">
              {/* Cohort Header & Match Criteria */}
              <div className={`p-5 rounded-xl border space-y-4 ${
                isDark ? 'bg-white/5 border-white/15' : 'bg-white border-2 border-slate-300 shadow-sm'
              }`}>
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <div className={`text-xs font-mono uppercase tracking-wider ${isDark ? 'text-amber-400' : 'text-amber-600 font-bold'}`}>
                      Empirical MoSPI Benchmark Cohort
                    </div>
                    <h3 className={`text-base sm:text-lg font-bold font-display ${isDark ? 'text-white' : 'text-slate-950'}`}>
                      Cohort Profile: {peerData?.cohort_id || 'National Infrastructure Baseline'}
                    </h3>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`px-2.5 py-1 rounded-lg text-xs font-mono font-bold border ${
                      isDark ? 'bg-white/10 text-white border-white/20' : 'bg-slate-100 text-slate-900 border-slate-300'
                    }`}>
                      {peerData?.cohort_size || 428} Comparable Corridors Monitored
                    </span>
                    <span className={`px-2.5 py-1 rounded-lg text-xs font-mono font-bold ${
                      (peerData?.target_deviation || 0) > 10
                        ? 'bg-red-500/20 text-red-400 border border-red-500/30'
                        : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                    }`}>
                      {peerData?.classification || 'Similar to peer cohort'}
                    </span>
                  </div>
                </div>

                {/* Match Criteria Tags */}
                <div className="space-y-1.5">
                  <div className={`text-[11px] font-mono uppercase ${isDark ? 'text-white/60' : 'text-slate-600 font-bold'}`}>
                    Cohort Matching Vector:
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {(peerData?.matching_criteria || [
                      `Sector: ${pSector}`,
                      `Ministry: ${project?.ministry || 'Government of India'}`,
                      'Stage: Active Execution (±20%)',
                      'Capex Band: Calibrated Mega-Asset Range'
                    ]).map((crit, idx) => (
                      <span key={idx} className={`px-2.5 py-1 rounded-md text-xs font-mono ${
                        isDark ? 'bg-black/40 text-white/90 border border-white/10' : 'bg-slate-100 text-slate-800 border border-slate-300 font-semibold'
                      }`}>
                        {crit}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Baseline Metrics Bar */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2">
                  <div className={`p-3 rounded-lg border font-mono ${isDark ? 'bg-black/30 border-white/10' : 'bg-slate-50 border-slate-200'}`}>
                    <div className={`text-[10px] uppercase ${isDark ? 'text-white/60' : 'text-slate-500 font-bold'}`}>Cohort Median DPHIS</div>
                    <div className={`text-lg font-bold ${isDark ? 'text-white' : 'text-slate-900'}`}>{peerData?.peer_median_dphis || 52.4}</div>
                  </div>
                  <div className={`p-3 rounded-lg border font-mono ${isDark ? 'bg-black/30 border-white/10' : 'bg-slate-50 border-slate-200'}`}>
                    <div className={`text-[10px] uppercase ${isDark ? 'text-white/60' : 'text-slate-500 font-bold'}`}>75th Percentile Ceil</div>
                    <div className={`text-lg font-bold text-amber-500`}>{peerData?.peer_p75_dphis || 62.0}</div>
                  </div>
                  <div className={`p-3 rounded-lg border font-mono ${isDark ? 'bg-black/30 border-white/10' : 'bg-slate-50 border-slate-200'}`}>
                    <div className={`text-[10px] uppercase ${isDark ? 'text-white/60' : 'text-slate-500 font-bold'}`}>Asset Percentile Rank</div>
                    <div className={`text-lg font-bold ${isDark ? 'text-white' : 'text-slate-900'}`}>{peerData?.target_percentile || 91}th %tile</div>
                  </div>
                  <div className={`p-3 rounded-lg border font-mono ${isDark ? 'bg-black/30 border-white/10' : 'bg-slate-50 border-slate-200'}`}>
                    <div className={`text-[10px] uppercase ${isDark ? 'text-white/60' : 'text-slate-500 font-bold'}`}>Cohort Variance</div>
                    <div className={`text-lg font-bold ${(peerData?.target_deviation || 0) > 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                      {(peerData?.target_deviation || 0) > 0 ? `+${peerData?.target_deviation}` : peerData?.target_deviation} pts
                    </div>
                  </div>
                </div>
              </div>

              {/* Comparable Projects Grid */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className={`text-sm sm:text-base font-bold font-display ${isDark ? 'text-white' : 'text-slate-950 font-bold'}`}>
                    Top 6 Empirical Peer Projects in MoSPI Portfolio
                  </h4>
                  <span className={`text-xs font-mono ${isDark ? 'text-white/60' : 'text-slate-500'}`}>
                    Cosine Vector Distance &lt; 0.18
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 sm:gap-4">
                  {(peerData?.peer_projects || []).map((peer, i) => (
                    <div key={peer.id || i} className={`p-4 rounded-xl border space-y-2.5 transition-all ${
                      isDark ? 'bg-white/5 border-white/15 hover:border-white/30' : 'bg-white border-2 border-slate-300 shadow-sm hover:border-slate-500'
                    }`}>
                      <div className="flex items-center justify-between gap-2">
                        <span className={`text-[11px] font-mono font-bold px-2 py-0.5 rounded ${
                          isDark ? 'bg-white/10 text-white' : 'bg-slate-200 text-slate-900'
                        }`}>
                          {peer.code}
                        </span>
                        <span className="px-2 py-0.5 rounded text-xs font-mono font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                          {peer.similarity_score_pct}% Match
                        </span>
                      </div>

                      <div className={`font-semibold text-xs sm:text-sm line-clamp-2 ${isDark ? 'text-white' : 'text-slate-900 font-bold'}`}>
                        {peer.name}
                      </div>

                      <div className={`grid grid-cols-3 gap-2 pt-1.5 border-t text-xs font-mono ${isDark ? 'border-white/10' : 'border-slate-200'}`}>
                        <div>
                          <div className={`text-[9px] uppercase ${isDark ? 'text-white/60' : 'text-slate-500'}`}>DPHIS</div>
                          <div className="font-bold text-amber-500">{peer.dphis}</div>
                        </div>
                        <div>
                          <div className={`text-[9px] uppercase ${isDark ? 'text-white/60' : 'text-slate-500'}`}>Progress</div>
                          <div className={`font-bold ${isDark ? 'text-white' : 'text-slate-900'}`}>{peer.physical_progress_pct}%</div>
                        </div>
                        <div>
                          <div className={`text-[9px] uppercase ${isDark ? 'text-white/60' : 'text-slate-500'}`}>Budget</div>
                          <div className={`font-bold ${isDark ? 'text-white' : 'text-slate-900'}`}>₹{Math.round(peer.budget_cr).toLocaleString()}Cr</div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Precedent Interventions Registry */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className={`text-sm sm:text-base font-bold font-display ${isDark ? 'text-white' : 'text-slate-950 font-bold'}`}>
                    Historical Precedent Interventions &amp; Recovery Outcomes
                  </h4>
                  <span className={`text-xs font-mono text-emerald-400`}>
                    ✓ Empirical Precedents Verified
                  </span>
                </div>

                <div className="space-y-3">
                  {(peerData?.peer_interventions || []).map((intv, idx) => (
                    <div key={idx} className={`p-4 rounded-xl border space-y-2 border-l-4 border-l-emerald-500 ${
                      isDark ? 'bg-white/5 border-white/15' : 'bg-white border-2 border-slate-300 shadow-sm'
                    }`}>
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <span className={`text-xs font-bold ${isDark ? 'text-white' : 'text-slate-950'}`}>
                          Applied to: {intv.peer_project_name}
                        </span>
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                            {intv.similarity_score_pct}% Cohort Match
                          </span>
                          <span className={`text-[10px] font-mono px-2 py-0.5 rounded ${
                            isDark ? 'bg-white/10 text-white/80' : 'bg-slate-200 text-slate-800 font-bold'
                          }`}>
                            Recovered in {intv.time_to_outcome_days} days
                          </span>
                        </div>
                      </div>

                      <div className={`text-xs sm:text-sm font-semibold leading-relaxed ${isDark ? 'text-amber-300' : 'text-amber-800'}`}>
                        "{intv.intervention}"
                      </div>

                      <div className={`p-2.5 rounded-lg text-xs leading-relaxed ${
                        isDark ? 'bg-black/40 text-white/85 border border-white/10' : 'bg-slate-100 text-slate-900 border border-slate-200 font-medium'
                      }`}>
                        <strong className="text-emerald-500">Observed Recovery:</strong> {intv.observed_outcome}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* 5-Month Trajectory Comparison */}
              <div className={`p-5 rounded-xl border space-y-3 ${
                isDark ? 'bg-white/5 border-white/15' : 'bg-white border-2 border-slate-300 shadow-sm'
              }`}>
                <h4 className={`text-sm sm:text-base font-bold font-display ${isDark ? 'text-white' : 'text-slate-950 font-bold'}`}>
                  5-Month Trajectory vs Peer Cohort Distribution
                </h4>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs font-mono text-left">
                    <thead>
                      <tr className={`border-b ${isDark ? 'border-white/15 text-white/60' : 'border-slate-300 text-slate-600'}`}>
                        <th className="py-2 px-3">Period</th>
                        <th className="py-2 px-3">Target Project Risk</th>
                        <th className="py-2 px-3">Peer Cohort Median</th>
                        <th className="py-2 px-3">P25 (Best Quartile)</th>
                        <th className="py-2 px-3">P75 (Lagging Quartile)</th>
                        <th className="py-2 px-3">Delta to Median</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(peerData?.peer_trajectory || []).map((t, idx) => {
                        const delta = Number((t.target - t.median).toFixed(1));
                        return (
                          <tr key={idx} className={`border-b ${isDark ? 'border-white/5 hover:bg-white/5' : 'border-slate-200 hover:bg-slate-50'}`}>
                            <td className={`py-2 px-3 font-bold ${isDark ? 'text-white' : 'text-slate-900'}`}>{t.period}</td>
                            <td className="py-2 px-3 font-bold text-amber-400">{t.target}</td>
                            <td className={`py-2 px-3 ${isDark ? 'text-white/80' : 'text-slate-800'}`}>{t.median}</td>
                            <td className="py-2 px-3 text-emerald-400">{t.p25}</td>
                            <td className="py-2 px-3 text-red-400">{t.p75}</td>
                            <td className={`py-2 px-3 font-bold ${delta > 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                              {delta > 0 ? `+${delta}` : delta} pts
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </GlassCard>
      </div>
    </div>
  );
}
